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

from argus_tal import timestamp as ts
from argus_tal.timeseries_datadict import LookupQualifier as LQ

from all_machines_common_base import ComputationMode, MachineAnalyticsBase, PowerState
from common_power_state_calculator import PowerStateCalculator

class ExtruderMachineStateCalculator(MachineAnalyticsBase):
  def __init__(self, data_source_IP_address,
                     data_source_TCP_port,
                     computation_mode,
                     power_state_ts_id,
                     melt_temperature_ts_id,
                     line_speed_ts_id,
                     screw_speed_ts):
    super(ExtruderMachineStateCalculator, self).__init__(
        "Extruder_machine", data_source_IP_address, data_source_TCP_port)

    self.__computation_mode = computation_mode
    self.__melt_temperature_ts_id = melt_temperature_ts_id
    self.__line_speed_ts_id = line_speed_ts_id
    self.__screw_speed_ts_id = screw_speed_ts
    self.__power_state_ts_id = power_state_ts_id

    # For power state calculation we take help from the PowerStateCalculator.
    self.__power_state_obj = PowerStateCalculator(
        data_source_IP_address,
        data_source_TCP_port,
        ComputationMode.ON_DEMAND,
        power_state_ts_id)

    # For delegate power state calculation to the PowerStateCalculator obj.
  def compute_result(self, start_time, end_time):
    # Compute power state list and on/off state
    power_state_result = self.__power_state_obj.compute_result(
        start_time, end_time)

    # Now use the power state transitions to calculate time in READY state
    # and ...
    time_in_ready_state = self.__calculate_ready_time(
        self.__power_state_obj.state_transition_list)
    # ... time in PURGE state.
    time_in_purge_state = self.__calculate_purge_time(
        self.__power_state_obj.state_transition_list)

    # Fill result map
    result_map = {}
    result_map['time_window'] = (start_time, end_time)
    result_map['off_state'] = power_state_result['off_state']
    result_map['on_state'] = power_state_result['on_state']
    result_map['ready_state'] = time_in_ready_state
    result_map['purge_state'] = time_in_purge_state
    return result_map

  def __calculate_ready_time(self, stateList):
      total_ready_time = 0
      for entry in stateList:
          if entry[2] == 1.0: #Checks the power state list and if in ON state proceeds
              start_timestamp = ts.Timestamp(entry[0])
              end_timestamp = ts.Timestamp(entry[1])
              rate = self.get_timeseries_data(self.__melt_temperature_ts_id,start_timestamp,end_timestamp,flag_compute_rate=True)

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


  def __calculate_purge_time(self, stateList): #linespeed zero, screw speed non-zero
      total_purge_time = 0
      for entry in stateList:
          if entry[2] == 1.0: #Checks if machine state is on
              start_timestamp = ts.Timestamp(entry[0])
              end_timestamp = ts.Timestamp(entry[1])
              data = self.get_timeseries_data(
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
                  screwdata = self.get_timeseries_data(
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
                  meltdata = self.get_timeseries_data(
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
