'''
   all_machines_common_base.py

   Use case(s): COMMON_INFRA

   This is a common base class for all machine analysis. It is expected that
   all machine analytics classes will derive from this.
'''

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
  def __init__(self, machine_type):
    self.__machine_type = machine_type

  def machine_type(self):
    return self.__machine_type
