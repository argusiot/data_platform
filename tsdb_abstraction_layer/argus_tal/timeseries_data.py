'''
  timeseries_data.py

  This file defines the TimeseriesData class and supporting enum/classes
  needed to use a TimeseriesData object.
'''

from enum import Enum
from collections import OrderedDict

'''
  Qualifies the timestamp parameter (key) being supplied. The API knows
  how to use the timestamp value based on the LookupParamQualifier supplied.

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
class LookupParamQualifier(Enum):
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
    get_identifier()
      Returns the metadata that idenfities the timeseries i.e the following
      pair - (metric_id, tag_value_pair_dict)

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
      LookupParamQualifier for details.

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
'''
class TimeseriesData(object):
  '''
    metric_name: Name of metric id as a string.

    filters: Additional tag values pairs to fully qualify the timeseries.

    timestamp_to_value_dict: A dictionary of timestamps to data values.
  '''
  def __init__(self, metric_name, tag_value_pairs, timestamp_to_value_dict):
    self.__metric_id = metric_name
    self.__query_filters = tag_value_pairs
    self.__ordered_ts_data = OrderedDict()
    for ts, dp in timestamp_to_value_dict.items():
      self.__ordered_ts_data[int(ts)] = dp


  def hello(self):
    return "Hello from %s" % self.__class__.__name__
