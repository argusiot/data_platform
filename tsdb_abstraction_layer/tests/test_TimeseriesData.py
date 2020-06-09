# -*- coding: utf-8 -*-

from .context import argus_tal

import unittest


class TimeseriesData_TestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_timeseriesdata(self):
      api = argus_tal.query_api.TimeseriesData()
      self.assertEqual(api.hello(), "Hello from TimeseriesData")

if __name__ == '__main__':
    unittest.main()
