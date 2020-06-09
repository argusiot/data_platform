'''
  API for Argus Data Platform queries.

  This API is to be used by applications that are developed for using the ADP.

  Current status: Proposed API
  (Possible statuses: Reviewed | Experimental Use | Accepted)
'''

from enum import Enum

class TsdbPlatform(Enum):
  OPENTSDB = 1
  PROMETHEUS = 2
  METRICTANK = 3

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
  def hello(self):
    return "Hello from %s" % self.__class__.__name__

'''
1. Input:
   1a) a FQ timeseries (metric_id + tags).
       No '*' permitted in request.
   1b) qualifiers e.g. rate
   1c) Query sets aggregation by 'none'.
2. Convert each timeseries from the response to into a collection of
   TimeseriesData objects.

Example:
  1) populate_timeseries_data usage (with single response object):
     --------------------------------------------------------------
    Query to retrieve data values expecting a single response object:
    query = QueryApi()
    metric_id = "machine.sensor.melt_temperature"
    filtering_tags = {'machine_name' : '65mm_extruder', 'port_number' : 1}
    try:
      query.populate_ts_data(metric_id,
                             filtering_tags,
                             DATA_VALUE,  # We want actual data in the response.
                             Timestamp(1590776274005),  # start time.
                             Timestamp(1591121874005))  # end time.

      # Get a list of TimeseriesData objects back
      ts_data = query.result_list()

      # In this example we expect the result set to contain exactly 1 object.
      assert(len(ts_data) == 1)

      ts_result_obj = ts_data[0]

      # Expect that the metric & filtering tags in the response to match input.
      assert((metric_id, filtering_tags) == ts_result_obj.get_identifier())

      # Cool ...now we're ready to use ts_result_obj. See documentation above
      # TimeseriesData class to see usage idioms.

    except <fill_in_later>:
      print("Query failed !")

  1) populate_timeseries_set usage (multiple timeseries in response):
     --------------------------------------------------------------
    # Create a list of metric IDs.
    metric_id_list = []
    metric_id_list.extend("machine.sensor.machine_powerOn_State")
    metric_id_list.extend("machine.sensor.melt_temperature")
    metric_id_list.extend("machine.sensor.line_speed")
    metric_id_list.extend("machine.sensor.screw_speed")

    # Filtering tags are same for all metrics.
    filetering_tags_list = []
    for idx in range(len(metric_id_list)):
      filetering_tags_list.extend({'machine_name' : '65mm_extruder'})
    try:
      query.populate_ts_set(metric_id_list,
                            filtering_tags_list,
                            DATA_VALUE,  # We want actual data in the response.
                            Timestamp(1590776274005),  # start time.
                            Timestamp(1591121874005))  # end time.

      ts_data = query.result_list()

      # We expect to get 4 timeseries back.
      assert(len(ts_data) == 4)

      # Lets verify that the metrics and tags we received meet our expectation.
      # FIXME .... RESUME HERE
      # Do I want to guarantee that results will be in same order as query ?
      # OR
      # Do I want the ability to pull the desired timeseries out of the result
      # object.... in which case making the result object a dictionart makes
      # sense.

    except <fill_in_later>:
      print("Query failed !")

'''
class QueryQualifier(Enum):
  DATA_VALUE = 1
  RATE = 2

'''
  Encapsulates the timestamp formats supported.
  Plan is to support only seconds or milliseconds.
  At present only 'Seconds' is supported.
'''
class Timestamp(object):
  def __init__(timestamp, unit='Seconds'):
    assert(unit == 'Seconds')
    self.__timestamp = int(timestamp)

  @property
  def value(self):
    return self.__timestamp

class QueryApi(object):
  def __init__(self, tsdb_platform=TsdbPlatform.OPENTSDB):
    self.__tsdb_platform = tsdb_platform

  def hello(self):
    return "Hello from %s" % self.__class__.__name__

  '''
    This is a synchronous blocking call and will block till the supplied query
    is validated, the HTTP request made and the response arrives.

    metric_name:
      Fully qualified name of the metric e.g. machine.sensor.melt_temperature.

    tag_value_pair:
      A dictionary of tags and values to identify a specific timeseries. No wild
      carding for value is permitted.
  '''
  def populate_ts_data(metric_name, tag_value_pairs, query_qualifier,
                       start_time, end_time):
    pass

  def populate_ts_set(metric_id_list, tag_value_pair_list, query_qualifier,
                      start_time, end_time):
    pass
