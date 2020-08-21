'''
  extruder_machine_states_calculator.py

  Requirements:
    https://docs.google.com/document/d/1FiHxbkZ98A6GeOkCLY65IxueMRLmzkU9W-ABq4fnZm4/edit#

  Use case: ADP_DASH_SW5

  Core algorithm:
     FIXME_Vishwas please fill in at a high level:
       (1) which timeseries are used to compute machine usage.
       (2) how is each timeseries used (functionally)
'''

from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
from argus_tal.timeseries_datadict import LookupQualifier as LQ

from all_machines_common_base import ComputationMode, MachineAnalyticsBase, PowerState

class ExtruderMachineStateCalculator(MachineAnalyticsBase):
  def __init__(self, data_source_IP_address,
                     data_source_TCP_port,
                     computation_mode,
                     power_state_ts_id,
                     melt_temperature_ts_id,
                     line_speed_ts_id,
                     screw_speed_ts):
    super(ExtruderMachineStateCalculator, self).__init__("Extruder_machine")
    self.__data_source_IP_address = data_source_IP_address
    self.__data_source_TCP_port = data_source_TCP_port
    self.__computation_mode = computation_mode
    self.__power_state_ts_id = power_state_ts_id
    self.__melt_temperature_ts_id = melt_temperature_ts_id
    self.__line_speed_ts_id = line_speed_ts_id
    self.__screw_speed_ts_id = screw_speed_ts

  def compute_result(self, start_time, end_time):
    stateList = self.__createPowerStateList(start_time, end_time)
    time_in_off_state, time_in_on_state = self.__calculateTotalTimeOnOff(stateList)
    time_in_ready_state = self.__calculateTotalReadyTime(stateList)
    time_in_purge_state = self.__calculateTotalPurgeTime(stateList)

    # Fill result map
    result_map = {}
    result_map['time_window'] = (start_time, end_time)
    result_map['off_state'] = time_in_off_state
    result_map['on_state'] = time_in_on_state
    result_map['ready_state'] = time_in_ready_state
    result_map['purge_state'] = time_in_purge_state
    return result_map


  def __get_timeseries_data(self, timeseries_id,
                                  start_timestamp,
                                  end_timestamp,
                                  flag_compute_rate=False):

      foo = query_api.QueryApi(
          self.__data_source_IP_address, self.__data_source_TCP_port,
          start_timestamp, end_timestamp,
          [timeseries_id],
          bt.Aggregator.NONE,
          flag_compute_rate,
          )

      rv = foo.populate_ts_data()
      assert rv == 0

      result_list = foo.get_result_set()
      assert len(result_list) == 1

      # for result in result_list:
      #     for kk, vv in result:
      #         print("\t%s->%d" % (kk, vv))
      return result_list[0]

  def __createPowerStateList(self, start_timestamp, end_timestamp):
      result = self.__get_timeseries_data(
          self.__power_state_ts_id, start_timestamp, end_timestamp)

      # Housekeeping variables.
      # FIXME_Vishwas: Please add comments here to explain what is happening
      # in the loop below. Specifically what do we expect to find inside
      # stateList.
      Startkey = 0
      EndKey = 0
      StartValue = 0
      stateList = []

      #Below block traverses the result and forms tuple of start and end timestamps with powerstate
      i=0
      for k, v in result:
          if i == 0:
              Startkey = k
              StartValue = v
          elif i == len(result) - 1:
              EndKey = k
              stateList.append(tuple((Startkey, EndKey, StartValue)))
          elif v == result.get_datapoint(k, LQ.NEAREST_SMALLER)[1]:
              # print(k,v,result.get_datapoint(k, LQ.NEAREST_SMALLER)[0],result.get_datapoint(k, LQ.NEAREST_SMALLER)[1])
              i += 1
              continue
          else:
              EndKey = result.get_datapoint(k, LQ.NEAREST_SMALLER)[0]
              stateList.append(tuple((Startkey, EndKey, StartValue)))
              Startkey = k
              StartValue = v
          i += 1

      return stateList

  #Uses powestate tuples and calculates overall timeon and timeoff 
  # FIXME: Can be potentially moved to base class since this is going to be 
  # needed for any machine.
  def __calculateTotalTimeOnOff(self, stateList):
      total_time_on = 0
      total_time_off = 0
      for entry in stateList:
          if entry[2] == 0.0:
              total_time_off += (entry[1]) - (entry[0])
          elif entry[2] == 1.0:
              total_time_on += (entry[1]) - (entry[0])
      return (total_time_off, total_time_on)


  def __calculateTotalReadyTime(self, stateList):
      total_ready_time = 0
      for entry in stateList:
          if entry[2] == 1.0: #Checks the power state list and if in ON state proceeds
              start_timestamp = ts.Timestamp(entry[0])
              end_timestamp = ts.Timestamp(entry[1])
              rate = self.__get_timeseries_data(self.__melt_temperature_ts_id,start_timestamp,end_timestamp,flag_compute_rate=True)

              StartTime = 0
              for k,v in rate:
                  if v < -1 or v > 1: #Rate is considered stable if within -1 and +1 so result set is checked
                      if StartTime != 0:
                          total_ready_time += rate.get_datapoint(k, LQ.NEAREST_SMALLER)[0] - StartTime #Rate out of range stop and add time to total ready time
                          StartTime = 0
                  elif 1 > v > -1: #Rate in range proceed to next datapoint
                      if StartTime == 0:
                          StartTime = k
                      elif k == rate.get_max_key() and StartTime != 0: #rate in range throught dataset so add time on the last entry
                          total_ready_time += rate.get_datapoint(k, LQ.NEAREST_SMALLER)[0] - StartTime
      return total_ready_time


  def __calculateTotalPurgeTime(self, stateList): #linespeed zero, screw speed non-zero
      total_purge_time = 0
      for entry in stateList:
          if entry[2] == 1.0: #Checks if machine state is on
              start_timestamp = ts.Timestamp(entry[0])
              end_timestamp = ts.Timestamp(entry[1])
              data = self.__get_timeseries_data(
                  self.__line_speed_ts_id, start_timestamp, end_timestamp)

              Startkey = 0
              EndKey = 0
              tempStateList = []
              purgeStart = 0
              i=0
              for k, v in data:
                  if i == len(data) and Startkey != 0: #if whole dataset has zero line speed, create tuple at last value
                      EndKey = k
                      tempStateList.append(tuple((Startkey, EndKey)))
                      Startkey = 0
                  elif v < 1000 and Startkey == 0: #LineSpeed is considered zero if lesser than 1000(job parameter) so need to find that
                      Startkey = k
                  elif v < 1000 and Startkey != 0: #If speed zero, continue
                      i += 1
                      continue
                  elif v > 1000 and Startkey != 0: #If speed non zero, stop and make a tuple with start and end
                      EndKey = data.get_datapoint(k, LQ.NEAREST_SMALLER)[0]
                      tempStateList.append(tuple((Startkey, EndKey)))
                      Startkey = 0
                  i += 1

              for entry in tempStateList: #check screwspeed at all intervals for every tuple created above
                  start_timestamp = ts.Timestamp(entry[0])
                  end_timestamp = ts.Timestamp(entry[1])
                  screwdata = self.__get_timeseries_data(
                      self.__screw_speed_ts_id, start_timestamp, end_timestamp)
                  for k,v in screwdata:
                      if 20 <= v <= 200: #If screw speed is non zero and in range (Values needs to discussed!!)
                          continue
                      else: 
                          tempStateList.remove(entry) #If screwspeed not in range remove the tuple entry
                          break

              #after pruning the tuple need to check if melt temprature has reached stable set values
              for entry in tempStateList:
                  start_timestamp = ts.Timestamp(entry[0])
                  end_timestamp = ts.Timestamp(entry[1])
                  meltdata = self.__get_timeseries_data(
                      self.__melt_temperature_ts_id,
                      start_timestamp, end_timestamp)

                  for k,v in meltdata:
                      if v > 160 or v < 147: #Stable target temperature, provided by caller (JOB Parameters)
                          if purgeStart != 0:
                              total_purge_time += meltdata.get_datapoint(k, LQ.NEAREST_SMALLER)[0] - purgeStart
                              purgeStart = 0
                      elif 147.0 <= v <= 160.0:
                          if purgeStart == 0:
                              purgeStart = k
                          elif k == meltdata.get_max_key() and purgeStart != 0:
                              total_purge_time += meltdata.get_datapoint(k, LQ.NEAREST_SMALLER)[0] - purgeStart
      return total_purge_time
