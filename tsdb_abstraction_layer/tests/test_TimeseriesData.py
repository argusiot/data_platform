# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import timeseries_data as tsd

import unittest


class TimeseriesData_TestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_timeseriesdata(self):
      api = tsd.TimeseriesData()
      self.assertEqual(api.hello(), "Hello from TimeseriesData")

if __name__ == '__main__':
    unittest.main()
