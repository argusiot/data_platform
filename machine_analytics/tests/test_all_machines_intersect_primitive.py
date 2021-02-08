'''
    Test cases for IntersectTimeseries
'''

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from all_machines_intersect_primitive import IntersectTimeseries as ITim, TimeWindowSequence

'''
from argus_tal import timeseries_id as ts_id
from argus_tal import query_api
from argus_tal import basic_types as bt
from argus_tal import timestamp as ts
from argus_tal import query_urlgen as qurlgen
'''

import unittest
from unittest.mock import Mock, patch

class IntersectTimeseries_Tests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(IntersectTimeseries_Tests, self).__init__(*args, **kwargs)

        # setup test parameters for all test cases
        self.__empty_tw_seq = TimeWindowSequence([])

    def testEmptyTimeWindowSequence_ExpectFailure(self):
        try:
            dummy = IntersectTimeseries(self.__empty_tw_seq)
        except:
            return
        assert(False) # Should never get here

    def testWindowComparison_Case1_FullOverlap(self):
        # win1:           4     7
        #           *-*-*-*-*-*-*-*-*-*-*-*-*-*
        # win2:           4     7
        win1 = win2 = (4,7)
        l_residue, overlap, r_residue = ITim.compare_time_windows(win1, win2)
        self.assertEqual(None, l_residue)
        self.assertEqual(win1, overlap)
        self.assertEqual(win2, overlap)
        self.assertEqual(None, r_residue)


    def testWindowComparison_Case2a_PartialOverlap(self):
        # win1:           4           10
        #           *-*-*-*-*-*-*-*-*-*-*-*-*-*
        # win2:     1           7
        win1 = (4,10)  # (start_time, end_time)
        win2 = (1,7)
        l_residue, overlap, r_residue = ITim.compare_time_windows(win1, win2)
        self.assertEqual(l_residue, (1, 4, ITim.TimeWindowId.W2))
        self.assertEqual(overlap, (4, 7))
        self.assertEqual(r_residue, (7, 10, ITim.TimeWindowId.W1))

    def testWindowComparison_Case2b_PartialOverlap(self):
        # win1:     1           7
        #           *-*-*-*-*-*-*-*-*-*-*-*-*-*
        # win2:           4           10
        win1 = (1,7)  # (start_time, end_time)
        win2 = (4,10)
        l_residue, overlap, r_residue = ITim.compare_time_windows(win1, win2)
        self.assertEqual(l_residue, (1, 4, ITim.TimeWindowId.W1))
        self.assertEqual(overlap, (4, 7))
        self.assertEqual(r_residue, (7, 10, ITim.TimeWindowId.W2))

    def testWindowComparison_Case3a_NoOverlap(self):
        # win1:               6       10
        #           *-*-*-*-*-*-*-*-*-*-*-*-*-*
        # win2:     1       5
        win1 = (6,10)  # (start_time, end_time)
        win2 = (1,5)
        l_residue, overlap, r_residue = ITim.compare_time_windows(win1, win2)
        self.assertEqual(l_residue, (1, 5, ITim.TimeWindowId.W2))
        self.assertEqual(overlap, None)
        self.assertEqual(r_residue, (6, 10, ITim.TimeWindowId.W1))

    def testWindowComparison_Case3b_NoOverlap(self):
        # win1:     1       5
        #           *-*-*-*-*-*-*-*-*-*-*-*-*-*
        # win2:               6       10
        win1 = (1,5)  # (start_time, end_time)
        win2 = (6,10)
        l_residue, overlap, r_residue = ITim.compare_time_windows(win1, win2)
        self.assertEqual(l_residue, (1, 5, ITim.TimeWindowId.W1))
        self.assertEqual(overlap, None)
        self.assertEqual(r_residue, (6, 10, ITim.TimeWindowId.W2))

    def testWindowComparison_Case4a_Subsume(self):
        # win1:     1                 10
        #           *-*-*-*-*-*-*-*-*-*-*-*-*-*
        # win2:         3       7
        win1 = (1,10)  # (start_time, end_time)
        win2 = (3,7)
        l_residue, overlap, r_residue = ITim.compare_time_windows(win1, win2)
        self.assertEqual(l_residue, (1, 3, ITim.TimeWindowId.W1))
        self.assertEqual(overlap, (3,7))
        self.assertEqual(r_residue, (7, 10, ITim.TimeWindowId.W1))

    def testWindowComparison_Case4b_Subsume(self):
        # win1:         3       7
        #           *-*-*-*-*-*-*-*-*-*-*-*-*-*
        # win2:     1                 10
        win1 = (3,7)  # (start_time, end_time)
        win2 = (1,10)
        l_residue, overlap, r_residue = ITim.compare_time_windows(win1, win2)
        self.assertEqual(l_residue, (1, 3, ITim.TimeWindowId.W2))
        self.assertEqual(overlap, (3,7))
        self.assertEqual(r_residue, (7, 10, ITim.TimeWindowId.W2))

