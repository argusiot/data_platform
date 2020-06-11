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

'''
class QueryQualifier(Enum):
  DATA_VALUE = 1
  RATE = 2

class QueryApi(object):
  def __init__(self, http_host, http_port,  metric_name, tag_value_pairs, \
               query_qualifier, start_time, end_time, \
               tsdb_platform=TsdbPlatform.OPENTSDB):
    self.__tsdb_platform = tsdb_platform

    # This will validate and raise an exception if any of the parameters are
    # out of whack.
    self.__validate_input_args(http_host, http_port, \
        metric_name, tag_value_pairs, query_qualifier, start_time, end_time)

    # All parameters are validated. We're ready to roll !
    self.__http_host = http_host
    self.__http_port = http_port
    self.__metric_id = metric_name
    self.__query_filters = tag_value_pairs
    self.__qualifier = query_qualifier
    self.__start_time = start_time
    self.__end_time = end_time
    self.__query_result = None

  def __validate_input_args(self, http_host, http_port, \
        metric_name, tag_value_pairs, query_qualifier, start_time, end_time):
    # Validate each parameter.
    # RESUME HERE !!!
    pass

  def hello(self):
    return "Hello from %s" % self.__class__.__name__

  '''
    This will trigger the HTTP call to the TSDB, parse the result. If the HTTP
    fails, this call will return an error.

    If the HTTP call succeeds, then the query result object can be accessed via
    the get_result() method.
  '''
  def populate_ts_data(self):
    # 1. Construct the URL
    # 2. Make the HTTP call to the backend and get the data.
    # 3. For success:
    #     Parse the response.
    #     Populate the result into TimeseriesData object.
    #     Store the result in self.__query_result.
    # 4. Do all the HTTP error handling.
    pass

  def get_result(self):
    return self.__query_result
