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
