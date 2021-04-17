'''
    Test cases for IntersectTimeseries

    IntersectTimeseries is a complicated beast to test.

    Hence we follow a pyramid test strategy for IntersectTimeseries testing.
    This is just a mental model to work with when reading the test cases in
    this file. This mental model is expected to come in handy with tests at
    some layer start breaking OR if you want to add new tests.

    The pyramid is *NOT* a reflection of how many test cases are written for
    each layer of the pyramid.

    This is the pyramid:
                          NegativeTests
                    4SeriesWith_ 4SeriesWith_
                3SeriesWith_ 2SeriesWith_ 2SeriesWith_
                2SeriesWith_ 2SeriesWith_ 2SeriesWith_
            WindowComparison  WindowComparison  WindowComparison

    The tests in this file use the string from layer description as a part
    of the test name. Trying doing a seach for the string "WindowComparison"
    in this file to see what this means.
'''

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../argus_quilt')))
from intersect_primitive import IntersectTimeseries as ITim
from time_windows import TimeWindowSequence

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

    def testEmptyTimeWindowSequence_EpectFailure(self):
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

        expected_residue_result = (None, None, ITim.TimeWindowId.EXACT_MATCH)
        self.assertEqual(expected_residue_result, l_residue)
        self.assertEqual(win1, overlap)
        self.assertEqual(win2, overlap)
        self.assertEqual(expected_residue_result, r_residue)


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

    def test_Intersect_2_Identical_Series(self):
        series1 = TimeWindowSequence([(1, 7), (10, 16)])
        series2 = TimeWindowSequence([(1, 7), (10, 16)])
        expected_result = TimeWindowSequence([(1, 7), (10, 16)])
        intersect = ITim([series1, series2])
        self.assertEqual(expected_result.get_time_windows(),
                         intersect.result.get_time_windows())

    def test_Intersect_Series_With_Itself(self):
        series = TimeWindowSequence([(1, 7), (10, 16)])
        intersect = ITim([series, series])
        self.assertEqual(series.get_time_windows(),
                         intersect.result.get_time_windows())

    def test_2SeriesWith_2WindowSequencesEach_Subtests(self):
        '''
           For series with window sequences we want to make sure all
           permutations of the 6 window comparison cases are well tested.

           The 6 window comparison cases are {2a, 2b, 3a, 3b, 4a, 4b}
           That gives 36 different permutations:
             (2a,2a)  (2a,2a)  (3a,2a)  (3b, 2a)  (4a, 2a)  (4b, 2a)
             (2a,2b)  (2b,2b)  (3a,2b)  (3b, 2b)  ....
             (2a,3a)  (2b,3a)  (3a,3a)  ...
             (2a,3b)  (2b,3b)  (3a,3b)  ...
             (2a,4a)  (2b,4a)  (3a,4a)  ...    <self-explanatory>
             (2a,4b)  (2b,4b)  (3a,4b)

             We get 36 such pairs.


           What does a pair like this (2a,2a) exactly mean ?
           ------------------------------------------------
           It means two time series constructed using the case 2a patterns
           back to back. Lets construct this one step at a time to understand
           whats happening here.

           Consider the example below to understand (2a, 2a).

             Pictorially:
             series1:         4           10  11          17
                        *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
             series2:   1           7 8             14

             Formally:
               series1 consists of 2 time windows = [(4,10), (11,17)]
               series2 consists of 2 time windows = [(1, 7), (8, 14)]

             If you line up the time windows *vertically* one below the other
             (as shown below), you can see that these are instances of window
             comparison of type 2a:
                           Case2a   Case2a
               series1 = [ (4, 10), (11,17) ]
               series2 = [ (1, 7) , (8, 14) ]

             Thus this a permutatin (2a, 2a).

             You can now see how other permutations would look.

           What is inter_window_gap ?
           --------------------------
           When generating a test timeseries, when we construct the sequence of
           windows, we far apart the windows are placed. This distance is the
           inter_window_gap (iwg).

               series1 with iwg of 0  = [ (4, 10), (10,17), (17,20)... ]
               series1 with iwg of 1  = [ (4, 10), (11,17), (18,21)... ]
               series1 with iwg of 5  = [ (4, 10), (15,21), (26,29)... ]
               series1 with iwg of 10 = [ (4, 10), (20,17), (27,30)... ]
               iwg can be random (example not shown).


           ----------------------------------------------------------------
           That is because it wont generate any residue. What we're really
           interetsed in testing out the impact of a residue generated in the
           (i-1)th iteration on the window comparison in the i-th iteration.

        '''
        test_data = [
                #   {2a, 2a} with iwg = 0
                (TimeWindowSequence([(4, 10), (10, 16)]),  # series #1
                 TimeWindowSequence([(1, 7),  (7, 14)]),   # series #2
                 TimeWindowSequence([(4, 7), (7,10), (10,14)]) # result
                ),
                #   {2a, 2a} with iwg = 1
                (TimeWindowSequence([(4, 10), (11, 17)]),  # series #1
                 TimeWindowSequence([(1, 7),  (8, 14)]),   # series #2
                 TimeWindowSequence([(4, 7), (8,10), (11,14)])  # result
                ),
            ]
        for tc in test_data:
            series1, series2, expected_result = tc
            intersect = ITim([series1, series2])
            actual_result = intersect.result
            self.assertEqual(expected_result.get_time_windows(),
                             actual_result.get_time_windows())
            print("\n%s" % series1.get_time_windows())
            print(series2.get_time_windows())
            print(actual_result.get_time_windows())

    def test_2SeriesWith_3WindownSequencesInEach(self):
        pass

    def test_2SeriesWith_N_WindowSequencesInEach(self):
        pass

    def test_3SeriesWith_2WindowSequencesInEach(self):
        pass

    def test_3SeriesWith_3WindownSequencesInEach(self):
        pass

    def test_3SeriesWith_N_WindowSequencesInEach(self):
        pass
