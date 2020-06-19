'''
  Leaf level module containing an Enum for constant definitions.
'''
from enum import Enum

class Tsdb(Enum):
  OPENTSDB = 1
  PROMETHEUS = 2
  METRICTANK = 3

# Query response aggregator
class Aggregator(Enum):
  NONE = 1
  ''' These will be supported in follow-up commits.
  SUM = 2
  COUNT = 3
  MIN = 4
  MAX = 5
  '''
