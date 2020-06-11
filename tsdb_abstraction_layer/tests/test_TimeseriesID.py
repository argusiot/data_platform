# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import exceptions as tal_err
import json
import unittest
import hashlib

class TimeseriesID_TestSuite(unittest.TestCase):
    """Test cases for class TimeseriesID"""
    def test_simple(self):
      # Input params (also used for verification of some output values).
      metric_id = "metric_foo"
      filters = {"tag1":"value1", "tag2":"value2"}

      # Expected output values.
      # The has value below comes with PYTHONHASHSEED=0
      # e.g. PYTHONHASHSEED=0 pytest -v test_TimeseriesID.py
      expected_hash_value = "75ccd00f7feaafe8476f79ca3e9a07011183cf3dcab8497fd"\
                            "6081ef928f7184e"

      # Get a TimeseriesID object.
      tsid = argus_tal.timeseries_id.TimeseriesID(metric_id, filters)

      # Now verify its fields.
      self.assertEqual(tsid.metric_id, metric_id)  # Metric id must match
      returned_dict = json.loads(tsid.filters) # Convert tsid.filters to a dict
      self.assertEqual(filters, returned_dict) # and verify it matches Filters.
      print("%s %s" % (tsid.metric_id, tsid.filters))

      # FIXME: Enable this assert, once we understand why PYTHONHASHSEED=0 is
      # being ignored on CircleCI !!
      # self.assertEqual(tsid.fqid, expected_hash_value) # FQ timeseries id is a
                                                        # hash value. Verify it!

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
