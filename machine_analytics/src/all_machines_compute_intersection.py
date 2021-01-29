'''
    Class to compute "intersection" of timeseries data.

    Input: A list of FilteredTimeseries objects
    Output: A FilteredTimeseries object containing only time windows where
            *all* the supplied objects had 'fired'.
'''

from all_machines_filter_primitive import FilteredTimeseries

class IntersectTimeseries(object):
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
          -- residue_window: a boolean value set to:
             True: If the L-Residue window comes from window1
             False: If the L-Residue window comes from window2
             None: If there's exact overlap

        Input:
        ------
        Two time windows w1 and w2 defined by their respective start and end
        times.
                                 w1 = (st1, et1)
                                 w2 = (st2, et2)

        Result semantics:
        -----------------
        Possible overlap patterns between w1 and w2. Note that we're only
        looking at temporal overlap here between the 2 windows of time.

            Case 1: Full overlap
                                 w1  *************

                                 w2  *************

            Case 2: Partial overlap
                        Case2a              |                Case2b
            w1          *************       | w1 *************
                                            |
            w2  *************               | w2        *************


            Case 3: No overlap
                        Case3a              |                Case3b
            w1                ************* | w1 *************
                                            |
            w2 *************                | w2                 *************

        Output:
        -------
            3 time windows dubbed as L-Residue, Overlap & R-Residue

            L-Residue: Residue to the left of the overlapping time window.
            Overlap: Overlapping time window.
            R-Residue: Residue to the right of the overlapping time window.
        '''
        st1, et1 = window1
        st2, et2 = window2
        l_residue = overlap = r_residue = None
        residue_window = None

        if st1 == st2 and et1 == et2:
            # This handles the Full Overlap case.
            overlap = (st1, et1)
        else:
            # We're now only dealing with Partial Overlap or No Overlap cases.
            input_windows = [st1, et1, st2, et2]
            input_windows.sort()

            if input_windows == [st2, st1, et2, et1]:   # Case 2a
                #         st1 ************* et1
                # st2 ************ et2
                l_residue = (st2, st1)
                overlap = (st1, et2)
                r_residue = (et2, et1)
                residue_window = False
            elif input_windows == [st2, st1, et2, et1]: # Case 2b
                # st1 ************* et1
                #        st2 ************ et2
                l_residue = (st1, st2)
                overlap = (st2, et1)
                r_residue = (et1, et2)
                residue_window = True
            elif input_windows == [st2, st1, et2, et1]: # Case 3a
                #                        st1 ************* et1
                # st2 ************ et2
                l_residue = (st2, et2)
                r_residue = (st1, et1)
                residue_window = False
            else:
            elif input_windows == [st2, st1, et2, et1]: # Case 3b
                # st1 ************* et1
                #                          st2 ************ et2
                l_residue = (st1, et1)
                r_residue = (st2, et2)
                residue_window = True
                assert(False)  # Should never happen

        return l_residue, overlap, r_residue, residue_window


    def compute(self):
         # pass
         # Work out details.
