# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import query_api

import unittest


class QueryApi_TestSuite(unittest.TestCase):
    """Advanced test cases."""

    def test_query_api(self):
      api = query_api.QueryApi()
      self.assertEqual(api.hello(), "Hello from QueryApi")


if __name__ == '__main__':
    unittest.main()
