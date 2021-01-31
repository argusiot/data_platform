'''
    Class to compute "intersection" of timeseries data.

    Input: A list of FilteredTimeseries objects
    Output: A FilteredTimeseries object containing only time windows where
            *all* the supplied objects had 'fired'.
'''

from all_machines_filter_primitive import FilteredTimeseries

class IntersectTimeseries(object):

    '''
    TimeWindowId is used to annotate the L- and R- residues returned by
    _compare_time_windows. This use of an enum here is primarily for making
    code more readable so that the algorithm is easily understood.
    '''
    class TimeWindowId(Enum):
        W1 = 1,
        W2 = 2

    def __init__(self, filterd_ts_obj_list):
        for obj in filtered_ts_obj_list:
            assert isinstance(obj) == FilteredTimeseries

        self.__filterd_ts_obj_list = filterd_ts_obj_list
        self.__result = None

    def _compare_time_windows(self, window1, window2):
        '''
        Objective:
        ----------
        Compare 2 time windows determine how much overlap exists between the
        supplied time windows. The method returns:
          -- 3 time windows viz.  L-Residue, Overlap, R-Residue
             See details below for their semantics.
          -- r_residue_in_window_1:
             A tri-state boolean value set to:
             True: If the R-Residue window comes from window1
             False: If the R-Residue window comes from window2
             None: If there's exact overlap

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
        '''
        st1, et1 = window1
        st2, et2 = window2
        l_residue = overlap = r_residue = None
        r_residue_in_window_1 = None

        if st1 == st2 and et1 == et2:
            # This handles Case 1 - Exact match.
            overlap = (st1, et1)
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

            Case 4a: Subsume
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


    def compute(self):
         # pass
         # Work out details.
