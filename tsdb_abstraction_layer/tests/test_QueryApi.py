# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from . import helpers as hh

import unittest

#import requests
from unittest import mock


'''
# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == 'http://someurl.com/test.json':
        return MockResponse({"key1": "value1"}, 200)
    elif args[0] == 'http://someotherurl.com/anothertest.json':
        return MockResponse({"key2": "value2"}, 200)

    return MockResponse(None, 404)
'''


class QueryApi_Tests(unittest.TestCase):
    """Advanced test cases."""

    def test_hello(self):
      host, port, metric, query_filters, aggregator, start, end = \
        hh.get_dummy_query_params()

      api = query_api.QueryApi(host, port, start, end, \
                               [ts_id.TimeseriesID(metric, query_filters)], \
                               aggregator)
      self.assertEqual(api.hello(), "Hello from QueryApi")

'''
    # We patch 'requests.get' with our own method. The mock object is passed in to our test case method.
    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_fetch(self, mock_get):
        # Assert requests.get calls
        mgc = MyGreatClass()
        json_data = mgc.fetch_json('http://someurl.com/test.json')
        self.assertEqual(json_data, {"key1": "value1"})
        json_data = mgc.fetch_json('http://someotherurl.com/anothertest.json')
        self.assertEqual(json_data, {"key2": "value2"})
        json_data = mgc.fetch_json('http://nonexistenturl.com/cantfindme.json')
        self.assertIsNone(json_data)

        # We can even assert that our mocked method was called with the right parameters
        self.assertIn(mock.call('http://someurl.com/test.json'), mock_get.call_args_list)
        self.assertIn(mock.call('http://someotherurl.com/anothertest.json'), mock_get.call_args_list)

        self.assertEqual(len(mock_get.call_args_list), 3)
'''

if __name__ == '__main__':
    unittest.main()
