'''
  Catalog of exceptions that can be thrown by the TSDB Abstraction Layer.
'''

class TsdbAbstractionLayerError(Exception):
  '''Base class for any TSDB Abstraction Layer exceptions'''
  def __init__(self, err_type, err_desc):
    self.__err_type = err_type
    self.__err_desc = err_desc

  def report(self):
    return "[%s] %s" % (self.__err_type, self.__err_desc)

'''
  A negative value was supplied as the timestamp value.
'''
class NegativeTimestamp(TsdbAbstractionLayerError):
  def __init__(self, err_str):
    super(TsdbAbstractionLayerError, self).__init__(type(self).__name__, \
                                                    err_str)

'''
  Failed to convert timestamp from supplied format to integer e.g.
  timestamp could be supplied as "June 4, 2020 12:12:12", which is unsupported.
'''
class InvalidTimestampFormat(TsdbAbstractionLayerError):
  def __init__(self, err_str):
    super(TsdbAbstractionLayerError, self).__init__(type(self).__name__, \
                                                    err_str)

class WildcardedTimeseriesId(TsdbAbstractionLayerError):
  def __init__(self, err_str):
    super(TsdbAbstractionLayerError, self).__init__(type(self).__name__, \
                                                    err_str)
