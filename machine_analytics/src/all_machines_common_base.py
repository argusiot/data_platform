'''
   all_machines_common_base.py

   Use case(s): COMMON_INFRA

   This is a common base class for all machine analysis. It is expected that
   all machine analytics classes will derive from this.
'''

from argus_tal import query_api
from argus_tal import basic_types as bt

from enum import Enum, auto

class ComputationMode(Enum):
  # In this mode, the object will continuously fetch the data in the background
  # (at a pre-specified period) and compute the machine states. This mode is to
  # be used if you dont want the user of the analytics object to block on the
  # time needed to fetch the data from the data source and do the computation.
  # This this mode allows for asynchronous download, compute and consume of the
  # data. Naturally when the result is obtained it is going to be 1 time period
  # old.
  CONTINUOUS = auto(),

  # In this mode, the caller supplies a specific time window and expects results
  # for that time window. Caller blocks until data is downloaded from data
  # source (over the network) and computation is done.
  ON_DEMAND = auto(),

class PowerState(Enum):
  OFF = 0.0
  ON = 1.0

class MachineAnalyticsBase(object):
  '''A common base class for all machine analytics stuff.

     Contanins some common functionality that all classes need.
  '''
  def __init__(self, machine_type,
                     data_source_IP_address,
                     data_source_TCP_port):
    self.__machine_type = machine_type
    self.__data_source_IP_address = data_source_IP_address
    self.__data_source_TCP_port = data_source_TCP_port

  def machine_type(self):
    return self.__machine_type

  def get_timeseries_data(self, timeseries_id,
                                start_timestamp,
                                end_timestamp,
                                flag_compute_rate=False):

      query_obj = query_api.QueryApi(
          self.__data_source_IP_address, self.__data_source_TCP_port,
          start_timestamp, end_timestamp,
          [timeseries_id],
          bt.Aggregator.NONE,
          flag_compute_rate,
          )

      rv = query_obj.populate_ts_data()
      assert rv == 0

      result_list = query_obj.get_result_set()
      assert len(result_list) == 1

      # for result in result_list:
      #     for kk, vv in result:
      #         print("\t%s->%d" % (kk, vv))
      return result_list[0]
