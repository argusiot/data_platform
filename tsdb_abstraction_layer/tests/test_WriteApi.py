# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal.write import WriteApi
from argus_tal import timeseries_id as ts_id
from . import helpers as hh

import unittest

#import requests
from unittest import mock


# This method will be used by the mock to replace requests.get
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, status_code):
            self.__status_code = status_code

        @property
        def status_code(self):
            return self.__status_code

        @property
        def ok(self):
            return self.status_code == 200

    code = None
    if args[0] == hh.get_write_url():
        code = 200
    return MockResponse(200)


class WriteApi_Tests(unittest.TestCase):
    # Object under test: o_u_t

    @mock.patch('requests.post', side_effect=mocked_requests_post)
    def test_single_write_EXPECT_SUCCESS(self, mock_post):
      host, port, metric, tags, timestamp, value = hh.get_dummy_write_params()

      o_u_t = WriteApi(host, port)

      tsid_obj = ts_id.TimeseriesID(metric, tags)
      resp_code = o_u_t.write_ts(tsid_obj, timestamp, value)

      '''Verification
      Verify that requests.post() was called to actually write to the TSDB.

      Also verify that the params supplied to the post method meet expectation.
      '''
      self.assertEqual(resp_code.status_code, 200)

      # We expect exactly 1 call to requests.post()
      self.assertEqual(len(mock_post.mock_calls), 1)

      # Lets retrieva and unpack the call object to peek/poke at it.
      call_obj = mock_post.mock_calls[0]
      name, positional_args, named_args = call_obj

      # Verify positional and named arguments.
      self.assertEqual(positional_args[0], hh.get_write_url())
      self.assertEqual(named_args['data'], hh.get_dummy_post_data())
      self.assertEqual(named_args['headers'], hh.get_dummy_post_headers())

    @mock.patch('requests.post', side_effect=mocked_requests_post)
    def test_single_write_EXPECT_FAILURE(self, mock_post):
      # Add test cases to exercise the error code paths in write.py
      # We'll have to model the errors exhibited by the HTTP layer and also
      # those exhibited by OpenTSDB for badly constructed write responses.
      pass

if __name__ == '__main__':
    unittest.main()
