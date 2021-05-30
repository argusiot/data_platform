# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import exceptions as tal_err
import json
import unittest
import hashlib

class TimeseriesID_Tests(unittest.TestCase):
    """Test cases for class TimeseriesID"""
    def test_simple(self):
      # Input params (also used for verification of some output values).
      metric_id = "metric_foo"
      filters = {"tag1":"value1", "tag2":"value2"}

      # Get a TimeseriesID object.
      tsid = argus_tal.timeseries_id.TimeseriesID(metric_id, filters)

      # Now verify its fields.
      self.assertEqual(tsid.metric_id, metric_id)  # Metric id must match
      self.assertEqual(filters, tsid.filters)

    def test_fqid_stability(self):
        tsid1 = argus_tal.timeseries_id.TimeseriesID( \
               "metric_foo",  {"tag1":"value1", "tag2":"val"})
        tsid2 = argus_tal.timeseries_id.TimeseriesID( \
                "metric_foo",  {"tag1":"value1", "tag2":"val"})
        self.assertEqual(tsid1.fqid, tsid2.fqid)
        self.assertEqual(hash(tsid1), tsid1.fqid)
        self.assertEqual(hash(tsid2), tsid2.fqid)

    def test_NO_wildcard_astrisk(self):
      try:
        tsid = argus_tal.timeseries_id.TimeseriesID( \
               "metric_foo",  {"tag1":"*", "tag2":"value2"})
      except tal_err.WildcardedTimeseriesId:
        pass
      else:
        # If we reached here it means the "tag1":"*" is being accepted.
        # Thats a bug.
        self.assertFalse(True) # We should never reach here.

      try:
        tsid = argus_tal.timeseries_id.TimeseriesID( \
               "metric_foo",  {"tag1":"value1", "tag2":"val*"})
      except tal_err.WildcardedTimeseriesId:
        pass
      else:
        # If we reached here it means the "tag2":"val*" is being accepted.
        # Thats a bug.
        self.assertFalse(True) # We should never reach here.

      try:
        tsid = argus_tal.timeseries_id.TimeseriesID( \
               "metric_foo",  {"tag1":"*ue*", "tag2":"value2"})
      except tal_err.WildcardedTimeseriesId:
        pass
      else:
        # If we reached here it means the "tag1":"*ue*" is being accepted.
        # Thats a bug.
        self.assertFalse(True) # We should never reach here.

    def test_equality(self):
      metric_id = "metric_foo"
      filters = {"tag1":"value1", "tag2":"value2"}
      tsid1 = argus_tal.timeseries_id.TimeseriesID(metric_id, filters)
      tsid2 = argus_tal.timeseries_id.TimeseriesID(metric_id, filters)
      self.assertEqual(tsid1, tsid2)

    def test_inequality_due_to_metric(self):
      tsid1 = argus_tal.timeseries_id.TimeseriesID( \
          "metric_FOO", {"tag1":"value1", "tag2":"value2"})
      tsid2 = argus_tal.timeseries_id.TimeseriesID( \
          "metric_BAR", {"tag1":"value1", "tag2":"value2"})
      self.assertNotEqual(tsid1, tsid2)

    def test_inequality_due_to_filters(self):
      tsid1 = argus_tal.timeseries_id.TimeseriesID( \
          "metric_id", {"tag1":"FOO", "tag2":"value2"})
      tsid2 = argus_tal.timeseries_id.TimeseriesID( \
          "metric_id", {"tag1":"BAR", "tag2":"value2"})
      self.assertNotEqual(tsid1, tsid2)

if __name__ == '__main__':
    unittest.main()
