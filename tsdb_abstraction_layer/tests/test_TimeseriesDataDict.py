# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import timeseries_datadict as tsd
from argus_tal import timeseries_id as tid
from . import helpers as hh

import unittest


class TimeseriesData_TestSuite(unittest.TestCase):
    """Basic test cases."""
    def __init__(self, *args, **kwargs):
      super(TimeseriesData_TestSuite, self).__init__(*args, **kwargs)
      # Single place to initialize all the parameters needed for each test.
      self.__host, self.__port, self.__metric, self.__ts_filters, \
      self.__qualifier, self.__start, self.__end = hh.get_dummy_query_params()
      self.__sorted_dps = hh.get_sorted_datapoints();
      self.__UNsorted_dps = hh.get_UNsorted_datapoints();
      self.__keys_as_str_dps = hh.get_string_datapoints();
      self.assertNotEqual(len(self.__sorted_dps), 0) # ensure non-empty testdata !

    def test_hello(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      self.assertEqual(ts_dd.hello(), "Hello from TimeseriesDataDict")

    ###########################################################################
    # Get timeseries ID
    ###########################################################################
    def test_ts_id(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      self.assertEqual(ts_dd.get_timeseries_id(), \
                       tid.TimeseriesID(self.__metric, self.__ts_filters))

    ###########################################################################
    # Trivial tests for empty / non-empty
    ###########################################################################
    def test_empty(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), {})  # dps empty.
      self.assertTrue(ts_dd.is_empty())

    def test_Not_empty(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      self.assertFalse(ts_dd.is_empty())

    ###########################################################################
    # Triplets of {get_min_key(), get_max_key(), get_keys()} tests for sorted,
    # unsorted and keys with strings (in input data).
    ###########################################################################
    def test_get_min_key_pre_sorted_dataset(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      expected_smallest_key, value = hh.get_smallest_key_and_its_value()
      self.assertEqual(ts_dd.get_min_key(), expected_smallest_key)

    def test_get_max_key_pre_sorted_dataset(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      expected_largest_key, value = hh.get_largest_key_and_its_value()
      self.assertEqual(ts_dd.get_max_key(), expected_largest_key)

    def test_get_keys_pre_sorted_dataset(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      # Observe: We *still* sort the __sorted_dps.keys() before comparison
      # because the sorted order is only guaranteed by Python 3.6 and later.
      # See helpers.py for additional info.
      self.assertEqual(ts_dd.get_keys(), sorted(self.__sorted_dps.keys()))

    def test_get_min_key_UNsorted_dataset(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__UNsorted_dps)
      expected_smallest_key, value = hh.get_smallest_key_and_its_value()
      self.assertEqual(ts_dd.get_min_key(), expected_smallest_key)

    def test_get_max_key_UNsorted_dataset(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__UNsorted_dps)
      expected_largest_key, value = hh.get_largest_key_and_its_value()
      self.assertEqual(ts_dd.get_max_key(), expected_largest_key)

    def test_get_keys_UNsorted_dataset(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__UNsorted_dps)
      self.assertEqual(ts_dd.get_keys(), sorted(self.__UNsorted_dps.keys()))

    def test_get_min_key_dataset_with_string_keys(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), \
                         self.__keys_as_str_dps)
      expected_smallest_key, value = hh.get_smallest_key_and_its_value()
      self.assertEqual(ts_dd.get_min_key(), expected_smallest_key)

    def test_get_max_key_dataset_with_string_keys(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), \
                         self.__keys_as_str_dps)
      expected_largest_key, value = hh.get_largest_key_and_its_value()
      self.assertEqual(ts_dd.get_max_key(), expected_largest_key)

    def test_get_keys_dataset_with_string_keys(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), \
                         self.__keys_as_str_dps)
      numeric_keys = [int(kk) for kk in self.__keys_as_str_dps.keys()]
      self.assertEqual(ts_dd.get_keys(), sorted(numeric_keys))

    ###########################################################################
    # Iterator tests.
    ###########################################################################
    def test_iterate_full_with_value_check(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      keys_returned = []
      for key, value in ts_dd:
        keys_returned.append(key)  # save key for later verification.
        self.assertEqual(value, self.__sorted_dps[key])  # verify value.

      # Verify that we got all the keys we expected AND in the right order.
      self.assertEqual(keys_returned, sorted(self.__sorted_dps.keys()))

    def test_iterate_empty_dps(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), {})
      keys_returned = []
      for key, value in ts_dd:
        keys_returned.append(key)  # save key for later verification.
      self.assertEqual(len(keys_returned), 0)

    ###########################################################################
    # Lookup tests.
    # For easy reference:
    #   {1234560: "10", \
    #    1234561: "20", \
    #    1234562: "30", \
    #    1234563: "40", \
    #    1234564: "50", \
    #    1234565: "60"  \
    #   }
    ###########################################################################
    def test_lookup_test_lq_EXACT_MATCH_success(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      for test_ts, test_val in self.__sorted_dps.items():
        actual_ts, actual_val = \
          ts_dd.get_datapoint(test_ts, tsd.LookupQualifier.EXACT_MATCH)
        self.assertEqual((test_ts, test_val), (actual_ts, actual_val))

    def test_lookup_test_lq_EXACT_MATCH_faliure(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      for test_ts, test_val in self.__sorted_dps.items():
        oor_key = test_ts*2   # generate a dummy out-of-range key from test_ts
        actual_ts, actual_val = \
          ts_dd.get_datapoint(oor_key, tsd.LookupQualifier.EXACT_MATCH)
        self.assertEqual((oor_key, None), (actual_ts, actual_val))


    #####  RESUME HERE ########
    #####  RESUME HERE ########
    #####  RESUME HERE ########
    #####  RESUME HERE ########
    #####  RESUME HERE ########
    '''
    def test_lookup_test_lq_NEAREST_SMALLER_case5(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      # non boundary element
      test_ts = self.__sorted_dps.keys()[1]
      actual_ts, actual_val = \
        ts_dd.get_datapoint(test_ts + 5, tsd.LookupQualifier.NEAREST_SMALLER)
      self.assertEqual((test_ts, self.__sorted_dps[test_ts]),
                       (actual_ts, actual_val))

    def test_lookup_test_lq_NEAREST_SMALLER_case3(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      # boundary element on the lower side
      test_ts, value = hh.get_smallest_key_and_its_value()
      actual_ts, actual_val = \
        ts_dd.get_datapoint(test_ts + 5, tsd.LookupQualifier.NEAREST_SMALLER)
      self.assertEqual((test_ts, self.__sorted_dps[test_ts]),
                       (actual_ts, actual_val))

    def test_lookup_test_lq_NEAREST_SMALLER_out_of_lower_bound(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      # boundary element on the lower side
      test_ts, value = hh.get_smallest_key_and_its_value()
      actual_ts, actual_val = \
        ts_dd.get_datapoint(test_ts - 5, tsd.LookupQualifier.NEAREST_SMALLER)
      self.assertEqual((test_ts, self.__sorted_dps[test_ts]),
                       (actual_ts, None))

    def test_lookup_test_lq_NEAREST_LARGER(self):
      pass

    def test_lookup_test_lq_NEAREST_SMALLER_WEAK(self):
      pass

    def test_lookup_test_lq_NEAREST_LARGER_WEAK(self):
      pass
    '''
    

if __name__ == '__main__':
    unittest.main()
