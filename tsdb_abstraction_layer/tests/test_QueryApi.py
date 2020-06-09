# -*- coding: utf-8 -*-

from .context import argus_tal

import unittest


class QueryApi_TestSuite(unittest.TestCase):
    """Advanced test cases."""

    def test_query_api(self):
      api = argus_tal.query_api.QueryApi()
      self.assertEqual(api.hello(), "Hello from QueryApi")


if __name__ == '__main__':
    unittest.main()
