'''
  timeseries_datadict.py

  This file defines the TimeseriesDataDict class and supporting enum/classes
  needed to use a TimeseriesDataDict object.
'''

from enum import Enum
import array

'''
  Qualifies the timestamp parameter (key) being supplied. The API knows
  how to use the timestamp value based on the LookupQualifier supplied.

   e.g. data set: timestamp->value
                  12345->10
                  12350->20
                  12365->30

        ts_obj.get_datapoint(12350, EXACT_MATCH) returns 20
        ts_obj.get_datapoint(12351, EXACT_MATCH) returns None

        ts_obj.get_datapoint(12348, NEAREST_SMALLER_STRICT) returns 10
Exact-> ts_obj.get_datapoint(12345, NEAREST_SMALLER_STRICT) returns None
OOB->   ts_obj.get_datapoint(12340, NEAREST_SMALLER_STRICT) returns None

        ts_obj.get_datapoint(12352, NEAREST_LARGER_STRICT) returns 30
Exact-> ts_obj.get_datapoint(12365, NEAREST_LARGER_STRICT) returns None
OOB->   ts_obj.get_datapoint(12367, NEAREST_LARGER_STRICT) returns None

        ts_obj.get_datapoint(12348, NEAREST_SMALLER_WEAK) returns 10
Exact-> ts_obj.get_datapoint(12345, NEAREST_SMALLER_WEAK) returns 10
OOB->   ts_obj.get_datapoint(12340, NEAREST_SMALLER_WEAK) returns 10

        ts_obj.get_datapoint(12352, NEAREST_LARGER_WEAK) returns 30
Exact-> ts_obj.get_datapoint(12365, NEAREST_LARGER_WEAK) returns 30
OOB->   ts_obj.get_datapoint(12367, NEAREST_LARGER_WEAK) returns 30
'''
class LookupQualifier(Enum):
  # Treat the timestamp as an exact match key.
  EXACT_MATCH = 1

  # First check if an exact match exists, if found, return it.
  # If no exact match is found, then return the nearest element smaller (larger)
  # than the supplied timestamp.
  NEAREST_SMALLER = 2
  NEAREST_LARGER = 3

  # First check if an exact match exists, if found, return it.
  # If no exact match is found, then return the nearest element smaller (larger)
  # than the supplied timestamp.
  # If supplied timestamp is smaller (larger) than the smallest (largest) time
  # stamp in the data set i.e. nothing smaller (larger) is found (and we know
  # there's no exact match), then return the actual smallest (largest) element
  # from the dataset.
  NEAREST_SMALLER_WEAK = 4
  NEAREST_LARGER_WEAK = 5

'''
  Stores timeseries data returned from a query.

  Data is stored ordered by time.

  Accessor APIs:
    get_timeseries_id():
      Returns the timeseries id object idenfities the timeseries i.e the object
      that encapsulates the following pair: (metric_id, tag_value_pair_dict)

    get_keys()
      Returns a reference to a list of all keys ordered by timestamp. Well
      suited to use if you want to iterate over the entire time series.

    get_key_slice(timestamp1, lookup_qualifier1, timestamp2, lookup_qualifier2)
      Returns a slice of the key space ordered by timestamp. The slice is
      bounded by timestamp1 & timestamp2. The qualifiers determine exactly how
      to carve up the slice.

    get_datapoint(timestamp, lookup_qualifier)
      Returns pair (timestamp, data_point) corresponding to the supplied
      timestamp depending upon lookup_qualifier. See documentation above
      LookupQualifier for details.

    get_first_datapoint()
    get_last_datapoint()
      Returns pair (timestamp, data_point) corresponding to the first (last)
      data point in the timeseries.

    is_empty()
      Returns True if timeseries is empty, False otherwise.

  Usage idioms:
  ============
    1. Full timeseries iteration:
       --------------------------
       To iterate in ascesnding order using keys from the object:
       keys = ts_obj.get_keys()
       for timestamp in keys:
         (ts, value) = ts_obj.get_datapoint(timestamp, EXACT_MATCH)
         # process value
         # ...

    2. Getting datapoint at an arbitrary timestamp:
       --------------------------------------------
       Given a 'timestamp' if you're not sure whether the datapoint exists in
       the timeseries object, use this:

       (a) To get the datapoint at a time value just larger than 'timestamp':
       (new_ts, value) = ts_obj.get_datapoint(timestamp, NEAREST_LARGER)
       if value != None:
         # Use value
       else:
         # We got None for value means that the timestamp we supplied is larger
         # than the largest. Decide what we want to do !

       (b) To get the datapoint at a time value just smaller than 'timestamp':
       (new_ts, value) = ts_obj.get_datapoint(timestamp, NEAREST_SMALLER)
       if value != None:
         # Use value
       else:
         # We got None for value means that the timestamp we supplied is smaller
         # than the first value, so lets . By changing to WEAK
         (new_ts, value) = ts_obj.get_last_datapoint()

     3. Slice retrieval and processing :
        --------------------------------
        Given a pair of timestamps get a slice of timestamps. We dont want to
        this *ever* fail thus keeping error handling simple.

        if ts_obj.is_empty():
          # return error.

        time_slice = ts_obj.get_key_slice(timestamp1, NEAREST_SMALLER_WEAK,
                                          timestamp2, NEAREST_LARGER_WEAK)
        for timestamp in time_slice:
         (ts, value) = ts_obj.get_datapoint(timestamp, EXACT_MATCH)

      4. Slice iterator:
         ---------------
        Given a pair of timestamps get a pair of indices corresponding to
        the pair of timestamps. These indices will then be used wita
        itertools.islice(ts_data...) to iterate over the range. This eliminates
        copying the keys into a list.

        if ts_obj.is_empty():
          # return error.

        (idx1, idx2) = ts_obj.get_iter_slice(timestamp1, NEAREST_SMALLER_WEAK,
                                             timestamp2, NEAREST_LARGER_WEAK)
        for ii in itertools.islice(ts_obj, idx1, idx2):
          value = next(ii)

        This is highly space efficient. Only downside here is that islice still
        walks through keys from 0 to idx1, thus slightly reducing efficiency.
        Thus it becomes a function of O(idx2) instead of O(idx2 - idx1).
'''
class TimeseriesDataDict(object):
  '''
    metric_name: Name of metric id as a string.

    filters: Additional tag values pairs to fully qualify the timeseries.

    datapoints_dict: A dictionary of timestamps to data values.
  '''
  def __init__(self, ts_id_obj, datapoints_dict):
    self.__ts_id_obj = ts_id_obj   # TimeseriesID
    self.__ts_dps_dict = {}        # Dictionary of data points time->value

    # The key/value from datapoints_dict get stored in self.__ts_dps_dict.
    # In addition we also store the timestamps (i.e the dictionary keys)
    # into __ts_keys_arr in sorted order. This duplication of keys is ok,
    # a TimeseriesDataDict object is immutable.
    # Benefit of this scheme is:
    #   - when key is known to exist O(1) lookup from dict
    #   - when key is not known O(logN) lookup from sorted array and then
    #     O(1) lookup from dict.
    # We use LookupQualifier to hint us for lookups.
    for ts, dp in datapoints_dict.items():
      self.__ts_dps_dict[int(ts)] = dp
    self.__ts_keys_arr = array.array('Q', sorted(self.__ts_dps_dict.keys()))

    self.__iter_idx = 0  # To support the iterator protocol.


  def get_timeseries_id(self):
    '''Returns the timeseries id object idenfities the timeseries i.e the
       object that encapsulates the pair: (metric_id, tag_value_pair_dict)'''
    return self.__ts_id_obj

  def get_keys(self):
    '''O(N) operation + memory used to build list ...use with care !'''
    return self.__ts_keys_arr.tolist()

  def __search_timestamp_index(self, timestamp, lookup_qualifier):
    # Initialize housekeeping vars for doing binary search self.__ts_keys_arr.
    low = 0
    high = len(self.__ts_keys_arr) - 1
    mid = 0

    # Now we do a binary search.
    while low <= high:
      mid = int((high + low)/2)
      if timestamp > self.__ts_keys_arr[mid]:    # If timestamp is larger than
        low = mid + 1                            # middle value, ignore left
      elif timestamp < self.__ts_keys_arr[mid]:  # half. Othewise ignore right
        high = mid - 1                           # half.
      else:
        return mid  # return index where timestamp has an exact match.

    if lookup_qualifier == LookupQualifier.EXACT_MATCH:
      # If caller has requested EXACT_MATCH and the key wasn't found during
      # binary search, there's nothing more we can do. Hence...
      return None

    '''
    Post binary search we have 3 cases based on value of low & high w.r.t
    array bounds.

    case 1:
    Supplied timestamp is smaller than the smallest value in __ts_keys_arr.
    It causes index high to fall off the bottom of the array lower bound.
                          0     1  ...                                max
                        -------------------------------------------------
     (timestamp)       | TSi | TSj | ....                          | TSm |
                        -------------------------------------------------
                  high   low
                (= -1)   mid
    case 2:
    Supplied timestamp is higher than the highest value in __ts_keys_arr.
    It causes index low to fall off the array upper bound cliff.
           0     1  ...                                max
          -------------------------------------------------
         | TSi | TSj | ....                          | TSm |    (timestamp)
          -------------------------------------------------
                                                      high   low
                                                      mid   (= len)
    case 3:
    __ts_keys_arr[0] <= supplied timestamp <= __ts_keys_arr[len - 1]
    This keeps low and high within array bounds and low >= high.
    '''
    if high < 0:  # Case 1
      assert(timestamp < self.__ts_keys_arr[0])
      if lookup_qualifier == LookupQualifier.NEAREST_LARGER_WEAK or \
         lookup_qualifier == LookupQualifier.NEAREST_LARGER or \
         lookup_qualifier == LookupQualifier.NEAREST_SMALLER_WEAK:
        return low   # since low > high
      elif lookup_qualifier == LookupQualifier.NEAREST_SMALLER:
        return None

    if low == len(self.__ts_keys_arr):  # Case 2
      assert(timestamp > self.__ts_keys_arr[low - 1])
      if lookup_qualifier == LookupQualifier.NEAREST_SMALLER_WEAK or \
         lookup_qualifier == LookupQualifier.NEAREST_SMALLER or \
         lookup_qualifier == LookupQualifier.NEAREST_LARGER_WEAK:
        return high   # since high < low
      elif lookup_qualifier == LookupQualifier.NEAREST_LARGER :
        return None

    # Case 3: both high and low are within bounds
    if lookup_qualifier == LookupQualifier.NEAREST_LARGER_WEAK or \
       lookup_qualifier == LookupQualifier.NEAREST_LARGER:
      return low
    if lookup_qualifier == LookupQualifier.NEAREST_SMALLER_WEAK or \
       lookup_qualifier == LookupQualifier.NEAREST_SMALLER:
      return high

    assert(False)  # We should never reach here.

  def get_key_slice(self, timestamp1, lookup_qualifier1,
                          timestamp2, lookup_qualifier2):
    '''Returns a slice of the key space ordered by timestamp. The slice is
       bounded by timestamp1 & timestamp2. The qualifiers determine exactly
       how to carve up the slice.'''
    key1 = self.__search_timestamp_index(timestamp1, lookup_qualifier1)
    key2 = self.__search_timestamp_index(timestamp2, lookup_qualifier2)
    return self.__ts_dps_dict.keys()[key1:key2]

  def get_iter_slice(self, timestamp1, lookup_qualifier1,
                           timestamp2, lookup_qualifier2):
    '''This is to assist efficient iteration over the object user standard
       Python iterators. See usage example #4 at the top of the class.'''
    key1 = self.__search_timestamp_index(timestamp1, lookup_qualifier1)
    key2 = self.__search_timestamp_index(timestamp2, lookup_qualifier2)
    return (key1, key2)

  def __iter__(self):
    self.__iter_idx = 0;
    return self

  def __next__(self):
    prev_idx = self.__iter_idx  # save previous index.
    self.__iter_idx = self.__iter_idx + 1
    if self.__iter_idx > len(self.__ts_keys_arr):
      raise StopIteration
    key = self.__ts_keys_arr[prev_idx]
    value = self.__ts_dps_dict[key]
    return key, value

  def get_datapoint(self, timestamp, lookup_qualifier):
    ''' Returns pair (timestamp, data_point) corresponding to the supplied
        timestamp depending upon lookup_qualifier. See documentation above
        LookupQualifier for details.'''
    # If qualifer is requesting EXACT_MATCH, we go directly to the dictionary.
    # If the timestamp is found there, we're done !
    value = None
    if lookup_qualifier == LookupQualifier.EXACT_MATCH:
      value = self.__ts_dps_dict.get(int(timestamp), None)
      return timestamp, value

    ts_idx = self.__search_timestamp_index(timestamp, lookup_qualifier)
    if ts_idx != None:
      timestamp = self.__ts_keys_arr[ts_idx]
      value = self.__ts_dps_dict[timestamp]
    return timestamp, value

  def get_min_key(self):
    return self.__ts_keys_arr[0]

  def get_max_key(self):
    return self.__ts_keys_arr[len(self.__ts_keys_arr) - 1]

  def is_empty(self):
    return len(self.__ts_dps_dict) == 0

  def hello(self):
    return "Hello from %s" % self.__class__.__name__
