# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import timeseries_data as tsd
from . import helpers as hh

import unittest


class TimeseriesData_TestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_timeseriesdata(self):
      host, port, metric, query_filters, qualifier, start, end = \
        hh.get_dummy_query_params()

      api = tsd.TimeseriesData(metric, query_filters, None)
      self.assertEqual(api.hello(), "Hello from TimeseriesData")

if __name__ == '__main__':
    unittest.main()
