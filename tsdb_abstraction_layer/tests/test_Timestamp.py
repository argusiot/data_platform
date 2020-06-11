# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import exceptions as tal_err

import unittest


class Timestamp_TestSuite(unittest.TestCase):
    """Test cases for class Timestamp"""
    def test_trivial_integer_ts(self):
      ts = argus_tal.timestamp.Timestamp(123456789)
      self.assertEqual(ts.value, 123456789)

    def test_epoch_time_string(self):
      ts = argus_tal.timestamp.Timestamp('123456789')
      self.assertEqual(ts.value, 123456789)

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
