# -*- coding: utf-8 -*-
'''
  timeseries_id.py

  A python module that defines the TimeseriesID class. This is the basic
  currency used to refer to fully qualified timeseries objects.

  Mutability: This class is immutable.

  This will generally be used only when all filters can be fully expanded and
  cannot contain any wild cards etc.

  FIXME: Need to figure out more sanity checks for TimeseriesID
'''

from . import exceptions as excp
import hashlib

class TimeseriesID(object):
  def __init__(self, metric_id, tag_value_pairs):
    # Validate value to make sure it doesn't contain wildcard.
    for tag, value in tag_value_pairs.items():
      if value.find("*") != -1:
        # We found '*' in the values. Not expected !
        raise excp.WildcardedTimeseriesId("metric: %s, tag: %s, value: %s" % \
                                          (metric_id, tag, value))

    self.__metric_id = metric_id
    self.__tag_value_pairs = tag_value_pairs

  def __eq__(self, other):
    if isinstance(other, TimeseriesID):
        return self.fqid == other.fqid
    return False

  def __str__(self):
    return "%s%s" % (self.metric_id, self.filters)

  def __hash__(self):
    return hash((self.__metric_id,
                 hash(frozenset(self.__tag_value_pairs.items()))))

  @property
  def metric_id(self):
    return self.__metric_id

  @property
  def filters(self):
    return self.__tag_value_pairs

  @property
  def fqid(self):
    '''Returns a SHA256 hash of the string-ified version of this object.'''
    return hash(self)
