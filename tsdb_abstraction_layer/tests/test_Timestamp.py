# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import exceptions as tal_err

import unittest


class Timestamp_Tests(unittest.TestCase):
    """Test cases for class Timestamp"""
    def test_integer_as_ts(self):
      ts = argus_tal.timestamp.Timestamp(123456789)
      self.assertEqual(ts.value, 123456789)

    def test_string_as_ts(self):
      ts = argus_tal.timestamp.Timestamp('123456789')
      self.assertEqual(ts.value, 123456789)

    def test_conversion_to_string(self):
      ts = argus_tal.timestamp.Timestamp('123456789')
      self.assertEqual(str(ts), "123456789")

    def test_equality(self):
      ts1 = argus_tal.timestamp.Timestamp('123456789')
      ts2 = argus_tal.timestamp.Timestamp('123456789')
      self.assertEqual(ts1, ts2)

    def test_inequality(self):
      ts1 = argus_tal.timestamp.Timestamp('123456789')
      ts2 = argus_tal.timestamp.Timestamp('987654321')
      self.assertNotEqual(ts1, ts2)

    def test_verbose_string_as_ts(self):
      try:
        ts = argus_tal.timestamp.Timestamp('June 4, 2020 12:16:26')
      except tal_err.InvalidTimestampFormat:
        pass

    def test_negative_ts(self):
      try:
        ts = argus_tal.timestamp.Timestamp(-1)
      except tal_err.NegativeTimestamp:
        pass


if __name__ == '__main__':
    unittest.main()
