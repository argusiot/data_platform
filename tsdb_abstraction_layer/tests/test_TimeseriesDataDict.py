# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import timeseries_datadict as tsd
from argus_tal import timeseries_id as tid
from . import helpers as hh
import itertools
import unittest


class TsDataDict_Tests(unittest.TestCase):
    """Basic test cases."""
    def __init__(self, *args, **kwargs):
      super(TsDataDict_Tests, self).__init__(*args, **kwargs)
      # Single place to initialize all the parameters needed for each test.
      self.__host, self.__port, self.__metric, self.__ts_filters, \
      self.__qualifier, self.__start, self.__end = hh.get_dummy_query_params()
      self.__sorted_dps = hh.get_sorted_datapoints();
      self.__UNsorted_dps = hh.get_UNsorted_datapoints();
      self.__keys_as_str_dps = hh.get_string_datapoints();
      self.assertNotEqual(len(self.__sorted_dps), 0) # ensure non-empty testdata !

      # See 'Lookup qualifier test matrix' below
      self.__k_0, self.__v_0 = hh.get_smallest_key_and_its_value()
      self.__k_Max, self.__v_Max = hh.get_largest_key_and_its_value() 
      self.__k_lt_k_0 = int(self.__k_0/2)   # "key less than key 0"
      self.__k_gt_k_Max = self.__k_Max * 2  # "key greater than key Max"
      self.__k_Arb, self.__v_Arb = hh.get_arbit_key_and_value()
      self.__k_betn_0_and_1 = self.__k_0 + 5
      self.__k_betn_Max_minus_1_and_Max  = self.__k_Max - 5
      self.__k_betn_i_and_j = self.__k_Arb + 5
      self.__k_i, self.__v_i = self.__k_Arb, self.__v_Arb
      self.__k_j, self.__v_j = self.__k_Arb + hh.get_distance(), \
                               self.__v_Arb + hh.get_distance()
      # We're slightly cheating here for __[kv]_1 computation by asuming that
      # those values are always get_distance() apart from __[kv]_0. Its ok!
      self.__k_1, self.__v_1 = self.__k_0 + hh.get_distance(), \
                               self.__v_0 + hh.get_distance()
      self.__k_Max_minus_1, self.__v_Max_minus_1 =  \
          self.__k_Max - hh.get_distance(), self.__v_Max - hh.get_distance()

      # Setup indices (assuming keys are in sorted order)
      self.__k_0_dp_idx = 0   # index corresponding to self.__k_0
      self.__k_1_dp_idx = 1   # index corresponding to self.__k_1
      self.__k_Max_dp_idx = len(self.__sorted_dps) - 1

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
    def test_empty_and_check_tsdd_length(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), {})  # dps empty.
      self.assertTrue(ts_dd.is_empty())
      self.assertEqual(len(ts_dd), 0)

    def test_Not_empty_and_check_tsdd_length(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      self.assertFalse(ts_dd.is_empty())
      self.assertEqual(len(ts_dd), len(self.__sorted_dps))


    ###########################################################################
    # Triplets of {get_min_key(), get_max_key()} tests for sorted,
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

    ###########################################################################
    # Iterator tests.
    ###########################################################################
    def __verify_full_iteration(self, ts_dd):
      keys_returned = []
      for key, value in ts_dd:
        keys_returned.append(key)  # save key for later verification.
        self.assertEqual(value, self.__sorted_dps[key])  # verify value.

      # Verify that we got all the keys we expected AND in the right order.
      self.assertEqual(keys_returned, sorted(self.__sorted_dps.keys()))

    def test_iterator_full_with_value_check(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      self.__verify_full_iteration(ts_dd)

    # By design, the iterate operation creates state in the object (i.e it has
    # side effects). We want to ascertain that any side effects from prev
    # iteration are cleaned up (i.e. iteration is idempotent).
    def test_iterator_repeated_iterations(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      self.__verify_full_iteration(ts_dd) # 1 of 3
      self.__verify_full_iteration(ts_dd) # 2 of 3
      self.__verify_full_iteration(ts_dd) # 3 of 3

    def test_iterator_empty_dps(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), {})
      keys_returned = []
      for key, value in ts_dd:
        keys_returned.append(key)  # save key for later verification.
      self.assertEqual(len(keys_returned), 0)

    ###########################################################################
    # Lookup qualifier tests
    ###########################################################################
    '''
    Lookup qualifier test matrix:
    =============================

    The tests assume that keys in the timeseries data dictionary are unique and
    totally orderded such that:
        k_0 < k_1 < k_2 < ....... < k_Max-1 < k_Max
        Corresponding values would be: v[k_0], v[k_1], ...v[k_Max]

     For ease of readability in the table below we use following:
       smallest key = k_0
       largest key = k_Max
       arbitrary non-boundary key = k_Arb 

     Sr    Supplied                Lookup qualifier and value returned
     No     key                E_M      N_LG      N_LG_W    N_SM     N_SM_W
     1. less than k_0         None     v[k_0]    v[k_0]    None       v[k_0]
     2. gt than k_Max         None     None      v[k_Max]  v[k_Max]   v[k_Max]
     4. equals k_0            v[k_0]   v[k_0]    v[k_0]    v[k_0]     v[k_0]
     5. equals k_Max          v[k_Max] v[k_Max]  v[k_Max]  v[k_Max]   v[k_Max]
     6. equals k_Arb          v[k_Arb] v[k_Arb]  v[k_Arb]  v[k_Arb]   v[k_Arb]
     7. betn k_0 and k_1      None     v[k_1]    v[k_1]    v[k_0]     v[k_0]
     8. betn k_Max-1 & k_Max  None     v[k_Max]  v[k_Max]  v[k_Max-1] v[k_Max-1]
     9. betn k_i and k_j      None     v[k_j]    v[k_j]    v[k_i]     v[k_i]
        (i < j &&
         0 < i, j < Max)
    '''

    def test_lookup_qualifer_test_matrix_EXACT_MATCH_column(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      sub_testcase_data = [
         # sub-test label , input key, expected key, expected value
         ("lt than k_0",   self.__k_lt_k_0,   self.__k_lt_k_0,   None), \
         ("gt than k_Max", self.__k_gt_k_Max, self.__k_gt_k_Max, None), \
         ("equals k_0",    self.__k_0,        self.__k_0,        self.__v_0), \
         ("equals k_Max",  self.__k_Max,      self.__k_Max,      self.__v_Max), \
         ("equals k_Arb",  self.__k_Arb,      self.__k_Arb,      self.__v_Arb), \
         ("betn k_0 and k_1", self.__k_betn_0_and_1, \
                              self.__k_betn_0_and_1, None), \
         ("betn k_Max-1 and k_Max", self.__k_betn_Max_minus_1_and_Max, \
                                    self.__k_betn_Max_minus_1_and_Max, None), \
         ("betn k_i and k_j", self.__k_betn_i_and_j, \
                              self.__k_betn_i_and_j, None), \
      ]
      for testdata in sub_testcase_data:
        test_label, input_key, rv_expected_key, rv_expected_value = testdata
        with self.subTest(test_label=test_label):
          kk, vv = ts_dd.get_datapoint(input_key, \
                                       tsd.LookupQualifier.EXACT_MATCH)
          self.assertEqual((kk, vv), (rv_expected_key, rv_expected_value), \
                           test_label)
          
    def test_lookup_qualifer_test_matrix_NEAREST_LARGER_column(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      sub_testcase_data = [
         # sub-test label ,   input key,        expected key,     expected value
         ("lt than k_0",      self.__k_lt_k_0,   self.__k_0,        self.__v_0), \
         ("gt than k_Max",    self.__k_gt_k_Max, self.__k_gt_k_Max, None), \
         ("equals k_0",       self.__k_0,        self.__k_0,        self.__v_0), \
         ("equals k_Max",     self.__k_Max,      self.__k_Max,      self.__v_Max), \
         ("equals k_Arb",     self.__k_Arb,      self.__k_Arb,      self.__v_Arb), \
         ("betn k_0 and k_1", self.__k_betn_0_and_1, self.__k_1,    self.__v_1), \
         ("betn k_Max-1 and k_Max", self.__k_betn_Max_minus_1_and_Max, \
                                    self.__k_Max, self.__v_Max), \
         ("betn k_i and k_j", self.__k_betn_i_and_j, self.__k_j,    self.__v_j), \
      ]
      for testdata in sub_testcase_data:
        test_label, input_key, rv_expected_key, rv_expected_value = testdata
        with self.subTest(msg=test_label):
          kk, vv = ts_dd.get_datapoint(input_key, \
                                       tsd.LookupQualifier.NEAREST_LARGER)
          self.assertEqual((kk, vv), (rv_expected_key, rv_expected_value), \
                           test_label)
          
    def test_lookup_qualifer_test_matrix_NEAREST_LARGER_WEAK_column(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      sub_testcase_data = [
         # sub-test label ,   input key,        expected key,    expected value
         ("lt than k_0",      self.__k_lt_k_0,   self.__k_0,     self.__v_0), \
         ("gt than k_Max",    self.__k_gt_k_Max, self.__k_Max,   self.__v_Max), \
         ("equals k_0",       self.__k_0,        self.__k_0,     self.__v_0), \
         ("equals k_Max",     self.__k_Max,      self.__k_Max,   self.__v_Max), \
         ("equals k_Arb",     self.__k_Arb,      self.__k_Arb,   self.__v_Arb), \
         ("betn k_0 and k_1", self.__k_betn_0_and_1, self.__k_1, self.__v_1), \
         ("betn k_Max-1 and k_Max", self.__k_betn_Max_minus_1_and_Max, \
                                    self.__k_Max, self.__v_Max), \
         ("betn k_i and k_j", self.__k_betn_i_and_j, self.__k_j,    self.__v_j), \
      ]
      for testdata in sub_testcase_data:
        test_label, input_key, rv_expected_key, rv_expected_value = testdata
        with self.subTest(test_label=test_label):
          kk, vv = ts_dd.get_datapoint(input_key, \
                                       tsd.LookupQualifier.NEAREST_LARGER_WEAK)
          self.assertEqual((kk, vv), (rv_expected_key, rv_expected_value), \
                           test_label)
          
    def test_lookup_qualifer_test_matrix_NEAREST_SMALLER_column(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      sub_testcase_data = [
         # sub-test label ,   input key,        expected key,     expected value
         ("lt than k_0",      self.__k_lt_k_0,   self.__k_lt_k_0,   None), \
         ("gt than k_Max",    self.__k_gt_k_Max, self.__k_Max,      self.__v_Max), \
         ("equals k_0",       self.__k_0,        self.__k_0,        self.__v_0), \
         ("equals k_Max",     self.__k_Max,      self.__k_Max,      self.__v_Max), \
         ("equals k_Arb",     self.__k_Arb,      self.__k_Arb,      self.__v_Arb), \
         ("betn k_0 and k_1", self.__k_betn_0_and_1, self.__k_0,    self.__v_0), \
         ("betn k_Max-1 and k_Max", self.__k_betn_Max_minus_1_and_Max, \
                                    self.__k_Max_minus_1, self.__v_Max_minus_1), \
         ("betn k_i and k_j", self.__k_betn_i_and_j, self.__k_i,    self.__v_i), \
      ]
      for testdata in sub_testcase_data:
        test_label, input_key, rv_expected_key, rv_expected_value = testdata
        with self.subTest(msg=test_label):
          kk, vv = ts_dd.get_datapoint(input_key, \
                                       tsd.LookupQualifier.NEAREST_SMALLER)
          self.assertEqual((kk, vv), (rv_expected_key, rv_expected_value), \
                           test_label)
     
    def test_lookup_qualifer_test_matrix_NEAREST_SMALLER_WEAK_column(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      sub_testcase_data = [
         # sub-test label ,   input key,        expected key,     expected value
         ("lt than k_0",      self.__k_lt_k_0,   self.__k_0,        self.__v_0), \
         ("gt than k_Max",    self.__k_gt_k_Max, self.__k_Max,      self.__v_Max), \
         ("equals k_0",       self.__k_0,        self.__k_0,        self.__v_0), \
         ("equals k_Max",     self.__k_Max,      self.__k_Max,      self.__v_Max), \
         ("equals k_Arb",     self.__k_Arb,      self.__k_Arb,      self.__v_Arb), \
         ("betn k_0 and k_1", self.__k_betn_0_and_1, self.__k_0,    self.__v_0), \
         ("betn k_Max-1 and k_Max", self.__k_betn_Max_minus_1_and_Max, \
                                    self.__k_Max_minus_1, self.__v_Max_minus_1), \
         ("betn k_i and k_j", self.__k_betn_i_and_j, self.__k_i,    self.__v_i), \
      ]
      for testdata in sub_testcase_data:
        test_label, input_key, rv_expected_key, rv_expected_value = testdata
        with self.subTest(msg=test_label):
          kk, vv = ts_dd.get_datapoint(input_key, \
                                       tsd.LookupQualifier.NEAREST_SMALLER_WEAK)
          self.assertEqual((kk, vv), (rv_expected_key, rv_expected_value), \
                           test_label)
          
    '''
      Note on itertools.islice() usage and testing:
        test_iter_slice_both_bounds() supplies both start and stop to islice().
        test_iter_slice_using_stop_only() supplies only stop to islice().

      One islice() quirk:
         By Pythonic design, iterating using islice happens over the range
         [start_idx, end_idx). Notice that end_idx is open interval, as a result
         we have to add 1 to the value returned by get_iter_slice() to the end
         index when calling islice(). This is a little clunky. Need to come up
         with a better way to solve this.
    '''
    def test_iter_slice_both_bounds(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      sub_testcase_data = [
         # sub-test label , key1, lk_qual1, key2, lookup_qual2, idx1, idx2
         ("EXACT_MATCH:iter 0 to k_Max", \
                 self.__k_0, tsd.LookupQualifier.EXACT_MATCH, \
                 self.__k_Max, tsd.LookupQualifier.EXACT_MATCH, \
                 self.__k_0_dp_idx, self.__k_Max_dp_idx), \
         ("EXACT_MATCH:iter 1 thru k_Max-1", \
                 self.__k_1, tsd.LookupQualifier.EXACT_MATCH, \
                 self.__k_Max_minus_1, tsd.LookupQualifier.EXACT_MATCH, \
                 self.__k_0_dp_idx + 1, self.__k_Max_dp_idx - 1), \
         ("LARGER:iter 0 to k_Max", \
                 self.__k_betn_0_and_1, tsd.LookupQualifier.NEAREST_LARGER, \
                 self.__k_Max, tsd.LookupQualifier.EXACT_MATCH, \
                 self.__k_1_dp_idx, self.__k_Max_dp_idx), \
         ("iterate empty", self.__k_0/2, tsd.LookupQualifier.EXACT_MATCH, \
                      self.__k_0/2, tsd.LookupQualifier.EXACT_MATCH, \
                      None, None)
      ]
      for tda in sub_testcase_data:
        test_label, key1, lk_qual1, key2, lookup_qual2, res_idx1, res_idx2 = tda
        with self.subTest(msg=test_label):
          idx1, idx2 = ts_dd.get_iter_slice(key1, lk_qual1, key2, lookup_qual2)

          # Verify that:
          # 1) the ranges of start and end indices are as expected !
          # 2) the keys between idx1 & idx2 match keys_returned
          # 3) the values returned for each key between idx1 & idx2 match
          #    expected value.
          self.assertEqual((idx1, idx2), (res_idx1, res_idx2), test_label)
          if (idx1, idx2,) == (None, None):
            continue

          # Using helper, get a slice of datapoints from start_idx to end_idx.
          slice_of_dps = hh.get_datapoint_slice(idx1, idx2+1)

          keys_returned = []
          # NOTICE HOW WE NEED idx2+1 below because of islice behaviour
          for kk,vv in itertools.islice(ts_dd, idx1, idx2+1):
            keys_returned.append(kk)
            self.assertEqual(vv, slice_of_dps[kk], test_label)  # verify value.

          # Verify key count and order
          self.assertEqual(keys_returned, sorted(slice_of_dps.keys()), test_label)

    def test_iter_slice_using_stop_only(self):
      ts_dd = tsd.TimeseriesDataDict( \
        tid.TimeseriesID(self.__metric, self.__ts_filters), self.__sorted_dps)
      ignored, end_idx = ts_dd.get_iter_slice(   # retrive start index
         self.__k_0, tsd.LookupQualifier.EXACT_MATCH, \
         self.__k_Max, tsd.LookupQualifier.EXACT_MATCH)
      keys_returned = []  # to verify count and order of keys returned.
      # Now iterate ...NOTICE: we do not supply end to islice().
      for kk,vv in itertools.islice(ts_dd, end_idx+1):
        keys_returned.append(kk)
        self.assertEqual(vv, self.__sorted_dps[kk])  # verify each value
      # verify keys
      self.assertEqual(keys_returned, sorted(self.__sorted_dps.keys()))

if __name__ == '__main__':
    unittest.main()
