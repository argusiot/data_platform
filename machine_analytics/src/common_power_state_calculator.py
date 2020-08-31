'''
  common_power_state_calculator.py

  Requirements:
    https://docs.google.com/document/d/1FiHxbkZ98A6GeOkCLY65IxueMRLmzkU9W-ABq4fnZm4/edit#

  Use case: COMMON_INFRA

  Core algorithm:
     FIXME_Vishwas please fill in at a high level:
       How is the power timeseries used to compute the transition state tuple
       list ?
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
