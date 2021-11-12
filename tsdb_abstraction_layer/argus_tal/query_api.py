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
from . import timeseries_datadict as tsdd
from . import timeseries_id as ts_id
import pandas as pd

'''
Example usage:
    # We need at least 1 timeseries id. The QueryAPI object can accept a list
    # of such objects.
    ts_id = Timeseries_ID("metric_foo", {'tag1' : 'value1})

    # Multiple options to create the QueryAPI object, based on:
    #  1) You want data (as written)
    #  2) You want rate
    #  3) You want data but at millisecond granularity
    #  4) You want rate but at millisecond granularity

    # Using hostname
    q_api_obj = QueryApi("www.foo.bar", 4242, start_ts_obj, end_ts_obj,
                         [ts_id1], Aggregator.NONE)
    # OR, using IP address
    q_api_obj = QueryApi("10.121.32.1", 4242, start_ts_obj, end_ts_obj,
                         [ts_id1, ts_id2], Aggregator.NONE)

    # Querying for rate instead of data
    q_api_obj = QueryApi("10.121.32.1", 4242, start_ts_obj, end_ts_obj,
                         [ts_id1, ts_id2], Aggregator.NONE,
                         flag_compute_rate=True)

    # Querying for data at millisecond granularity.
    q_api_obj = QueryApi("10.121.32.1", 4242, start_ts_obj, end_ts_obj,
                         [ts_id1, ts_id2], Aggregator.NONE,
                         flag_millisecond=True)

'''
class QueryApi(object):
  def __init__(self, http_host, http_port, start_time, end_time, tsid_list,
               aggregator_type, flag_compute_rate=False,
               flag_ms_response=False, tsdb_platform=basic_types.Tsdb.OPENTSDB):
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
    self.__flag_millsecond_response = flag_ms_response
    self.__start_time = start_time
    self.__end_time = end_time
    self.__url = qurlgen.url(self.__tsdb_platform,
            self.__http_host, self.__http_port,
            self.__start_time, self.__end_time, self.__aggregator,
            self.__tsid_list, flag_compute_rate=self.__flag_compute_rate,
            flag_ms_response=self.__flag_millsecond_response)

    # List of TimeseriesDataDict objects for each timeseries returned.
    self.__tsdd_obj_list = []

    # To store the HTTP response code (for ease of debuggability).
    self.__http_response_code = 0

    # Expected tags in the response received (per timeseries)
    self.__tags_expected_in_response = ["aggregateTags", "dps", \
                                        "metric", "tags"]
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
      self.__http_response_code = response.status_code
      return -1

    try:
      self.__tsdd_obj_list, error = self.__parse_query_response(response.json())
    except ValueError:
      # log error
      return -2  # JSON response could not be decoded

    return error

  def get_result_set(self):
    return self.__tsdd_obj_list

  '''
     This method makes the result processing very convenient.

     It returns the result as a map/dictionary. The map is indexed by the FQID
     of the timeseries_id and the value is the query result data dict object.
  '''
  def get_result_map(self):
    # tsid.fqid -> tsdd (i.e. query result object)
    return { \
        tsdd.get_timeseries_id().fqid: tsdd for tsdd in self.__tsdd_obj_list}

  '''
      This method returns results as pandas Dataframes instead of TSDD objects.

      The result is a returned as a map, where the timeseries FQID is an index
      into the map and the value is the dataframe object.

      Each dataframe contains 2 columns: "timestamp", "result".
  '''
  def get_result_as_dataframes(self):
    # tsid.fqid -> tsdd converted into a dataframe
    result_map = { }
    for tsdd in self.__tsdd_obj_list:
      # Convert TSDD object into a dataframe using DataFrame.from_dict(). That
      # requires creating a temporary dictionary of the type shown by tmp_dict
      # below i.e. keys as column names and values as lists.
      tmp_dict = {'timestamp': [], 'result': []}
      for kk,vv in tsdd:
          tmp_dict['timestamp'].append(kk)
          tmp_dict['result'].append(vv)
      df = pd.DataFrame.from_dict(tmp_dict)  # convert to dataframe
      result_map[tsdd.get_timeseries_id().fqid] = df   # Save df in result_map
    return result_map

  @property
  def http_status_code(self):
    return self.__http_response_code

  #############################################################################
  # Helper methods start here.
  #############################################################################
  def __validate_input_args(self, http_host, http_port, \
        tsid_list, aggregator_type, start_time, end_time):
    # Validate each parameter.
    # RESUME HERE !!!
    pass

  def hello(self):
    return "Hello from %s" % self.__class__.__name__

  def __all_tags_found(self, expected_tags, response_data):
    for tag in expected_tags:
      if None == response_data.get(tag, None):
        return False
    return True

  def __parse_query_response(self, resp_data):
    assert(self.__aggregator == basic_types.Aggregator.NONE)

    # If the aggregator is "none" then we can be guaranteed that each element
    # in resp_data is a timeseries object. Simplifies parsing !
    tsdd_list = []
    for unique_ts in resp_data:
      if not self.__all_tags_found(self.__tags_expected_in_response, unique_ts):
        return tsdd_list, -2  # FIXME: This should become an exception

      assert(len(unique_ts['aggregateTags']) == 0)
      timeseries_data_dict = tsdd.TimeseriesDataDict( \
          ts_id.TimeseriesID(unique_ts['metric'], unique_ts['tags']), \
          unique_ts['dps'])
      tsdd_list.append(timeseries_data_dict)

    # Its not improbable that we got a legit JSON response back BUT containing
    # no timeseries data. That would still be an error !
    if len(tsdd_list) == 0:
      return tsdd_list, -3  # error
    return tsdd_list, 0  # sucess
