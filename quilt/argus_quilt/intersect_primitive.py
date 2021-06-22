'''
    Class to compute "intersection" of timeseries data.

    Input: A list of TimeWindowSequence objects.
    Output: A FilteredTimeseries object containing only time windows where
            *all* the supplied objects had 'fired'.
'''

from .time_windows import TimeWindowSequence
from collections import deque
from enum import Enum

class IntersectTimeseries(object):

    '''
    TimeWindowId is used to annotate the L- and R- residues returned by
    _compare_time_windows. This use of an enum here is primarily for making
    code more readable so that the algorithm is easily understood.

    EXACT_MATCH is used when the 2 supplied time windows exactly i.e. full
    overlap and there are no residues.
    '''
    class TimeWindowId(Enum):
        W1 = 1,
        W2 = 2
        EXACT_MATCH = 3

    # NOTE: This is a class method (not an object method). We have done this
    # purely for the convenince of being able to test this independently AND
    # making it class method was not (adversely) affecting the class
    # usage/abstraction in any way.
    def compare_time_windows(window1, window2):
        '''
        Objective:
        ----------
        Compare 2 time windows determine how much overlap exists between the
        supplied time windows.

        Input:
        ------
        Two time windows w1 and w2 defined by their respective start and end
        times.
                                 w1 = (st1, et1)
                                 w2 = (st2, et2)

        Patterns being sought out:
        --------------------------
        Comparing 2 time windows, only 4 possibilities exist:
            Case 1: Exact match
            Case 2: Partial overlap
            Case 3: No overlap
            Case 4: Subsume
        This method identifies which case is met by the supplied time windows.
        See ASCII art patterns below.

        Return:
        -------
        A tuple of 3 time windows: L-Residue, Overlap, R-Residue

        L-Residue: Residue to the left of the overlapping time window.
        Overlap: Overlapping time window.
        R-Residue: Residue to the right of the overlapping time window.

        Each of the 3 time windows are themselves returned as tuples of the
        following format:
           Overlap window: (start_time, end_time)
           Residue windows: (start_time, end_time, time_window_identifier)

           time_window_identifier is of type TimeWindowId.
        '''
        st1, et1 = window1
        st2, et2 = window2
        l_residue = overlap = r_residue = None
        r_residue_in_window_1 = None

        TWindow = IntersectTimeseries.TimeWindowId
        if st1 == st2 and et1 == et2:
            # This handles Case 1 - Exact match.
            overlap = (st1, et1)
            l_residue = r_residue = (None, None, TWindow.EXACT_MATCH)
        else:
            #...this handles all the remaining cases.
            input_windows = [st1, et1, st2, et2]
            input_windows.sort()

            '''
            Timestamp pattern we expect to find in the sorted input_windows
            array.

            Case 2a: Partial overlap
                      st1 ************* et1
              st2 ************ et2

            Case 2b: Partial overlap
              st1 ************* et1
                     st2 ************ et2

            Case 3a: No overlap
                                    st1 ************* et1
              st2 ************ et2

            Case 3b: No overlap
              st1 ************* et1
                                       st2 ************ et2

            Case 4a: Subsume
              st1 *************************** et1
                       st2 ************ et2

            Case 4b: Subsume
                       st1 ************ et1
              st2 *************************** et2
            '''
            # shorten name for readability
            TWindow = IntersectTimeseries.TimeWindowId

            if input_windows == [st2, st1, et2, et1]:   # Case 2a
                l_residue = (st2, st1, TWindow.W2)
                overlap = (st1, et2)
                r_residue = (et2, et1, TWindow.W1)
            elif input_windows == [st1, st2, et1, et2]: # Case 2b
                l_residue = (st1, st2, TWindow.W1)
                overlap = (st2, et1)
                r_residue = (et1, et2, TWindow.W2)
            elif input_windows == [st2, et2, st1, et1]: # Case 3a
                l_residue = (st2, et2, TWindow.W2)
                r_residue = (st1, et1, TWindow.W1)
            elif input_windows == [st1, et1, st2, et2]: # Case 3b
                l_residue = (st1, et1, TWindow.W1)
                r_residue = (st2, et2, TWindow.W2)
            elif input_windows == [st1, st2, et2, et1]: # Case 4a
                l_residue = (st1, st2, TWindow.W1)
                overlap = (st2, et2)
                r_residue = (et2, et1, TWindow.W1)
            elif input_windows == [st2, st1, et1, et2]: # Case 4b
                l_residue = (st2, st1, TWindow.W2)
                overlap = (st1, et1)
                r_residue = (et1, et2, TWindow.W2)
            else:
                assert(False)  # Should never happen

        return l_residue, overlap, r_residue


    def __init__(self, twin_series_obj_list):
        # Need at least 2 timeseries to be supplied for computing intersection.
        assert(len(twin_series_obj_list) >= 2)

        # Ensure each object in the list of of TimeWindowSequence type
        for obj in twin_series_obj_list:
            assert(isinstance(obj, TimeWindowSequence))

        # Prepare the result
        self.__twin_series_result = self._compute(twin_series_obj_list)


    # This is the heart of the 'Quilt Algorithm'. All the cool prep work done
    # in tranforming the timeseries into a step function now gets used to
    # compute the intersection. Follow along ...
    def _compute(self, twin_series_obj_list):
        if len(twin_series_obj_list) == 1:
            return twin_series_obj_list[0]

        '''
        Objective:
        ---------
        Compute overlapping segments of time across all the TimeWindowSequence
        objects stored in __twin_series_obj_list.

        The heart of the algorithm is to iterate over all the twin_series
        objects and do a litte "intersection computation" in every iteration.

        The 'intersection computation' in the i-th iteration uses 2 things:
           (1) the i-th twin_series i.e. twin_series_obj_list[i], AND
           (2) the cummulative result computed thus far (i.e. from iterations
               [0, i-1]). We store the cummulative result below in the variable
               'result'.

        What is the 'intersection computation' ?
        ----------------------------------------
          Each 'intersection computation' takes 2 time series windows as
          input.

          The intersection computation is easier to follow along if we
          consider each time window series as a queue. Thus we have 2 queues,
          (say Q1 & Q2) one for each time window series.

          The intersection computation requires us to iterate over both queues
          and 'intersect' the time windows at the head Q1 & Q2.

          'intersect':
          ============
              The 'intersect computation' then reduces to comparing the 2 time
              at the head of Q1 & Q2. See _compare_time_windows for how that is
              done.

              The outcome of each 'intersect' is a left_residue, an overlapping
              section and a right_residue.

              The overlap gets appended to the result. The left_residue is
              discarded. The right_residue is added back to the HEAD of the
              queue (i.e. time window series) it came from.

          Whats the intuition here?
          =========================
              Handling of the overlap is easy to understand. It is "the"
              actual intersection result between the 2 windows. So that goes
              to the result.

              However you can get residues on either side (see the ASCII art
              _compare_time_windows to understand this better).

              Note that the right residue simply gets processed in the next
              iteration i.e. we dont lose it.

              However, discarding the the left residue needs a little
              explanation. ADD EXPLANATION !!!
        '''

        # shorten name for readability
        TWindow = IntersectTimeseries.TimeWindowId

        tws1_q = deque(twin_series_obj_list[0].get_time_windows())
        for tws_idx in range(1, len(twin_series_obj_list)):
            tws2_q = deque(twin_series_obj_list[tws_idx].get_time_windows())

            # Collects the result of intersection between tws1 & tws2.
            result = []
            while tws1_q and tws2_q:
                window1 = tws1_q.popleft()
                window2 = tws2_q.popleft()
                l_residue, overlap, r_residue = __class__.compare_time_windows(
                        window1, window2)

                # Process l_residue -- do nothing i.e. discard it.

                # Process overlap: Append to result
                if overlap != None:
                  result.append(overlap)

                # Process r_residue:
                # re-insert the time residual time window to the head of the
                # queue it came from.
                st_time, end_time, win = r_residue
                if win == TWindow.W1:
                    tws1_q.insert(0, (st_time, end_time))  # Enque at q head
                elif win == TWindow.W2:
                    tws2_q.insert(0, (st_time, end_time))  # Enque at q head
                elif win == TWindow.EXACT_MATCH:
                    # No residue processing needed
                    pass
                else:
                    assert(False)  # Should never happen

            # result from this iteration becomes tws1_q for next iteration.
            # Thus the result propgates through iterations comparing result of
            # previous intersections with current tws.
            tws1_q = deque(result)

        return TimeWindowSequence(list(tws1_q))


    @property
    def result(self):
        return self.__twin_series_result
