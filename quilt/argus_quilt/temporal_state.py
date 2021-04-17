'''
   class TemporalState

   This class processes a single state

   See $HOME/data_platform/design_docs/README.quilt_and_applique_infra_design
   for details.
'''

import os
import uuid
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../core_src')))
from filter_primitive import FilterQualifier, FilteredTimeseries
from stepify import Stepify
from intersect_primitive import IntersectTimeseries

class TemporalState(object):
    '''
       state_label: A human readable string label for the state
       expression_list: A list of the form [(ts_id, operator, constant),...]

       Example:
       For state S1 defined as follows:
       S1 = ("melt_temperature{machine=foo}" > 100.0) &&
            ("melt_pressure{machine=foo}" > 12)

       state_label: "S1"
       expression list: [(ts_id1, ">", 100.0), (ts_id2, ">", 12)]

       where,
       ts_id1 = TimeseriesID("melt_temperature", "{machine: foo}")
       ts_id2 = TimeseriesID("melt_pressure", "{machine: foo}")
    '''
    def __init__(self, state_label, expression_list, output_tsid):
        self.__state_uuid = uuid.uuid4()
        self.__state_label = state_label
        self.__expression_list = list(expression_list) # clone

        # List of timeseries IDs from which to "read"
        self.__read_tsid_list = []
        for stmt in expression_list:
            ts_id, operator_str, filter_constant = stmt
            self.__read_tsid_list.append(ts_id)

        self.__intersect_result_t_win = None

        # The __write_tsid is not actually used anywhere within this class.
        # Turns out hanging the __write_tsid object off TemporalState is just
        # very convenient.
        self.__write_tsid = output_tsid

    @property
    def state_label(self):
        return self.__state_label

    # This method is expected to be used for *testing* only. Should not be used
    # in production code.
    def _get_expression_list(self):
        return self.__expression_list

    @property
    def read_tsid_list(self):
        return self.__read_tsid_list

    @property
    def uuid(self):
        return self.__state_uuid

    @property
    def write_tsid(self):
        return self.__write_tsid

    def get_time_spent_in_state(self):
        # Process self.__computation_result to compute time spent in this
        # state for previous incarnation of do_computation()
        # return self.__computation_result.add_windows()

        list_tup = self.__intersect_result_t_win.get_time_windows()
        totaltime = 0
        for tup in list_tup:
            if tup is not None:
                totaltime += tup[1] - tup[0]
        return totaltime

    def do_computation(self, query_result_map):
        t_window_obj_list = []
        for stmt in self.__expression_list:
            ts_id, oper_str, constant = stmt

            # Filter
            filtered_ts = FilteredTimeseries(query_result_map[ts_id.fqid],
                                             FilterQualifier(oper_str),
                                             constant)

            # Stepify
            stepified_ts = Stepify(filtered_ts)

            # Gather stepficiation result
            t_window_obj_list.append(stepified_ts.get_stepified_time_windows())

        intersect = IntersectTimeseries(t_window_obj_list)
        self.__intersect_result_t_win = intersect.result

        # Does it make sense to add this here ?
        # return self.__get_time_spent_in_state()

        return self.get_time_spent_in_state()
