# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from . import helpers as hh

import unittest

#import requests
from unittest import mock


# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == hh.get_url_for_dummy_query_params():
        return MockResponse(hh.get_good_json_response(), 200)
    elif args[0] == hh.get_url_for_truncated_json_response():
        return MockResponse(hh.get_truncated_json_response(), 200)
    elif args[0] == hh.get_url_for_dummy_query_params_with_rate():
        return MockResponse(hh.get_good_json_response_for_rate(), 200)

    return MockResponse(None, 404)


class QueryApi_Tests(unittest.TestCase):
    """Advanced test cases."""

    def test_hello(self):
      host, port, metric, query_filters, aggregator, start, end = \
        hh.get_dummy_query_params()

      api = query_api.QueryApi(host, port, start, end, \
                               [ts_id.TimeseriesID(metric, query_filters)], \
                               aggregator)
      self.assertEqual(api.hello(), "Hello from QueryApi")

    def __verify_tsdd_result_obj(self, tsdd_to_verify,\
                                 expected_tsid, expected_dps):
      self.assertEqual(tsdd_to_verify.get_timeseries_id(), expected_tsid)

      # Construct a dps dict by iterating over the tsdd object. Verify it
      # matches supplied datapoints.
      result_dps = {kk:vv for kk, vv in tsdd_to_verify}
      self.assertEqual(result_dps, expected_dps) # verify data point

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_single_metric_query_response(self, mock_get):
      host, port, metric, query_filters, aggregator, start, end = \
        hh.get_dummy_query_params()
      expected_dps = hh.get_sorted_datapoints()

      input_tsid = ts_id.TimeseriesID(metric, query_filters)
      api = query_api.QueryApi(host, port, start, end, [input_tsid], aggregator)
      retval = api.populate_ts_data()  # FIXME: I'm conflicted whether to use
                                       # exceptions or return value here !!
      self.assertTrue(retval == 0)  # eok

      # Data population was successful... good ! Now we can peek/poke at the
      # result set.
      tsdd_list = api.get_result_set()
      self.assertEqual(len(tsdd_list), 1)  # Expect exctly 1 object in the list.
      self.__verify_tsdd_result_obj(tsdd_list[0], input_tsid, expected_dps)

      # Assert that our mocked method was called with the right parameters
      self.assertIn(mock.call(hh.get_url_for_dummy_query_params()), \
                              mock_get.call_args_list)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_unknown_metric_query_404_response(self, mock_get):
      host, port, IGNORED, query_filters, aggregator, start, end = \
        hh.get_dummy_query_params()

      input_tsid = ts_id.TimeseriesID("404metric", query_filters)
      api = query_api.QueryApi(host, port, start, end, [input_tsid], aggregator)
      retval = api.populate_ts_data()  # FIXME: I'm conflicted whether to use
                                       # exceptions or return value here !!
      self.assertEqual(retval, -1)  # HTTP error
      self.assertEqual(api.http_status_code, 404)

      '''
      FIXME: Fix the expected URL based on "404metric" being supplied.
      self.assertIn(mock.call(hh.get_url_for_dummy_query_params()), \
                              mock_get.call_args_list)
      '''

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_single_metric_query_bad_json_response(self, mock_get):
      host, port, IGNORED, query_filters, aggregator, start, end = \
        hh.get_dummy_query_params()

      input_tsid = ts_id.TimeseriesID("truncated_json_metric", query_filters)
      api = query_api.QueryApi(host, port, start, end, [input_tsid], aggregator)
      retval = api.populate_ts_data()  # FIXME: I'm conflicted whether to use
                                       # exceptions or return value here !!
      self.assertEqual(retval, -2)  # Error decoding JSON
      self.assertEqual(api.http_status_code, 200)

      '''
      FIXME: Fix the expected URL based on "404metric" being supplied.
      self.assertIn(mock.call(hh.get_url_for_dummy_query_params()), \
                              mock_get.call_args_list)
      '''

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_single_metric_RATE_query_response(self, mock_get):
      host, port, metric, query_filters, aggregator, start, end = \
        hh.get_dummy_query_params()
      expected_dps = hh.get_sorted_datapoints_for_rate() # rate datapoints.

      input_tsid = ts_id.TimeseriesID(metric, query_filters)
      api = query_api.QueryApi(host, port, start, end, \
                               [input_tsid], aggregator, flag_compute_rate=True)
      retval = api.populate_ts_data()
      self.assertTrue(retval == 0)

      # Data population was successful... good ! Now we can peek/poke at the
      # result set.
      tsdd_list = api.get_result_set()
      self.assertEqual(len(tsdd_list), 1)  # Expect exctly 1 object in the list.
      self.__verify_tsdd_result_obj(tsdd_list[0], input_tsid, expected_dps)

      # Assert that our mocked method was called with the right parameters
      self.assertIn(mock.call(hh.get_url_for_dummy_query_params_with_rate()), \
                              mock_get.call_args_list)

    #
    # RESUME HERE:
    #  1. Add more tests !!!!
    #  2. Add negative tests.
    #  3. Change error returns to exceptions.

if __name__ == '__main__':
    unittest.main()
