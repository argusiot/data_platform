'''
  Leaf level module containing an Enum for constant definitions.
'''

class Tsdb(Enum):
  OPENTSDB = 1
  PROMETHEUS = 2
  METRICTANK = 3
