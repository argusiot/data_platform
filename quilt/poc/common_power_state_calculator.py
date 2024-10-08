'''
  common_power_state_calculator.py

  Requirements:
    https://docs.google.com/document/d/1FiHxbkZ98A6GeOkCLY65IxueMRLmzkU9W-ABq4fnZm4/edit#

  Use case: COMMON_INFRA

  Core algorithm:
     In order to compute machine power states, the power_state timeseries is used.
     When the value of an entry in power_state_ts is 1, machine is considered ON,
     it is considered OFF when the value is 0.
     The goal is create a list of tuples of form (t1, t2, state_k) where t1 and t2 represent
     the start and end timestamps of the period in which the machine was in state(ON or OFF)
     represented by state_k. 
     This is achieved by looking for transitions of value in the power_state_ts.
     When a transition occurs from ON to OFF or vice versa, the timestamp is recorded as t1.
     Further power_state_ts is sequentially checked for the next transition and that timestamp 
     is recorded as t2. state_k is recorded as the one the machine spent from t1 to t2.
     The tuple is appended to a list and the process is repeated until the end of the power_state_ts. 
'''

from argus_tal.timeseries_datadict import LookupQualifier as LQ

from all_machines_common_base import ComputationMode, MachineAnalyticsBase, PowerState

class PowerStateCalculator(MachineAnalyticsBase):
  def __init__(self, data_source_IP_address,
                     data_source_TCP_port,
                     computation_mode,
                     power_state_ts_id):
    super(PowerStateCalculator, self).__init__(
        "Power_state_analyser",
        data_source_IP_address,
        data_source_TCP_port)
    self.__computation_mode = computation_mode
    self.__power_state_ts_id = power_state_ts_id

    # __power_state_tranistions_list is used to store the result from
    # compute_result(). This transition list is super helpful for users of this
    # object to calculate other states.
    self.__power_state_tranistions_list = None

  def compute_result(self, start_time, end_time):
    '''This generates 2 pieces of useful information for the caller.

       It computes the time spent in On and Off states. That is returned in the
       result map.

    '''
    self.__power_state_tranistions_list = self.__create_state_transition_list(
        start_time, end_time)
    time_in_off_state, time_in_on_state = self.__calculate_on_off_time(
        self.__power_state_tranistions_list)

    # Fill result map
    result_map = {}
    result_map['time_window'] = (start_time, end_time)
    result_map['off_state'] = time_in_off_state
    result_map['on_state'] = time_in_on_state
    return result_map

  @ property
  def state_transition_list(self):
    ''' Returns a list of time windows idenitfying edges on which state
       transitions occurred.

       More precisely, it returns a list of tuples of the form:
            [(t_1, t_2, state_k), (t_3, t_4, state_k')....]

       state_k & state_k' can only take on either 0.0 (power off) or 1.0
       (power on) values.

       (t_i, t_j) represents a time window where the sames state_k exists
       for that entire window. The window of time that follows has a
       the opposite state state_k' !
     '''
    return self.__power_state_tranistions_list

  def __create_state_transition_list(self, start_timestamp, end_timestamp):
      result = self.get_timeseries_data(
          self.__power_state_ts_id, start_timestamp, end_timestamp)

      # Housekeeping variables.
      # FIXME_Vishwas: Please add comments here to explain what is happening
      # in the loop below. Specifically what do we expect to find inside
      # state_transition_list.
      start_key = 0
      end_key = 0
      start_value = 0
      state_transition_list = []

      #Below block traverses the result and forms tuple of start and end timestamps with powerstate
      #FIXME_Vishwas: Discuss this with Vishwas !
      for idx, (kk, vv) in enumerate(result):
          if idx == 0:  # Initial condition
              start_key = kk
              start_value = vv
          elif idx == len(result) - 1:  # Last element in the result
              end_key = kk
              state_transition_list.append(tuple((start_key, end_key, start_value)))
          elif vv == result.get_datapoint(kk, LQ.NEAREST_SMALLER)[1]:
              continue
          else:
              end_key = kk
              state_transition_list.append(tuple((start_key, end_key, start_value)))
              start_key = kk
              start_value = vv

      return state_transition_list

  #Uses powestate tuples and calculates overall timeon and timeoff
  def __calculate_on_off_time(self, state_transition_list):
      total_time_on = 0
      total_time_off = 0
      for entry in state_transition_list:
          start_time, end_time, state_value = entry # unpack
          if state_value == 0.0:
              total_time_off += (end_time - start_time)
          else:
              assert(state_value == 1.0)  # No other value is possible.
              total_time_on += (end_time - start_time)
      return (total_time_off, total_time_on)
