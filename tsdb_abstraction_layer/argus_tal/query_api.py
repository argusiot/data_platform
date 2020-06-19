'''
  API for Argus Data Platform queries.

  This API is to be used by applications that are developed for using the ADP.

  Current status: Proposed API
  (Possible statuses: Reviewed | Experimental Use | Accepted)
'''

from enum import Enum
import requests
import json
from . import query_urlgen as qurlgen
from . import basic_types

'''
1. Input:
   1a) a FQ timeseries (metric_id + tags).
       No '*' permitted in request.
   1b) aggregators e.g. rate
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
class QueryApi(object):
  def __init__(self, http_host, http_port, start_time, end_time, tsid_list, \
               aggregator_type, flag_compute_rate=False, \
               tsdb_platform=basic_types.Tsdb.OPENTSDB):
    self.__tsdb_platform = tsdb_platform

    # This will validate and raise an exception if any of the parameters are
    # out of whack.
    self.__validate_input_args(http_host, http_port, tsid_list, \
        aggregator_type, start_time, end_time)

    # All parameters are validated. We're ready to roll !
    self.__http_host = http_host
    self.__http_port = http_port
    self.__tsid_list = [ts for ts in tsid_list] # clone the list so we
                                                # are not referencing to a
                                                # caller supplied list.
    self.__aggregator = aggregator_type
    self.__flag_compute_rate = flag_compute_rate
    self.__start_time = start_time
    self.__end_time = end_time
    self.__url = qurlgen.url(self.__tsdb_platform, \
            self.__http_host, self.__http_port, \
            self.__start_time, self.__end_time, self.__aggregator, \
            self.__tsid_list, flag_compute_rate=self.__flag_compute_rate)

    # List of TimeseriesDataDict objects for each timeseries returned.
    self.__tsdd_obj_list = []

    # To store the HTTP response code (for ease of debuggability).
    self.__http_response_code = 0

  def __validate_input_args(self, http_host, http_port, \
        tsid_list, aggregator_type, start_time, end_time):
    # Validate each parameter.
    # RESUME HERE !!!
    pass

  def hello(self):
    return "Hello from %s" % self.__class__.__name__

  def __parse_query_response(resp_data):

    assert(self.__aggregator == basic_types.Aggregator.NONE)

    # If the aggregator is "none" then we can be guaranteed that each element
    # in resp_data is a timeseries object. Simplifies parsing !
    tsdd_list = []
    for unique_ts in resp_data:
      assert(len(unique_ts['aggregateTags']) == 0)
      timeseries_data_dict = TimeseriesDataDict( \
          TimeseriesID(unique_ts['metric'], unique_ts['tags']), \
          unique_ts['dps'])
      tsdd_list.append(timeseries_data_dict)

    # Its not improbable that we got a legit JSON response back BUT containing
    # no timeseries data. That would still be an error !
    if len(tsdd_list) == 0:
      return tsdd_list, -3  # error
    return tsdd_list, 0  # sucess
                                      
  '''
    This will trigger the HTTP call to the TSDB, parse the result. If the HTTP
    fails, this call will return an error.

    If the HTTP call succeeds, then the query result object can be accessed via
    the get_result() method.
  '''
  def populate_ts_data(self):
    error = 0
    response = requests.get(self.__url)
    self.__http_response_code = response.status_code
    
    # FIXME: Add handling of all HTPP error types.
    if response.status_code < 200 or response.status_code > 299:
      # log error.
      return -1

    try:
      self.__tsdd_obj_list, error = self.__parse_query_response(resp.json())  
    except ValueError:
      # log error
      return -2  # JSON response could not be decoded
      
    return error

  def get_result_set(self):
    return self.__tsdd_obj_list
