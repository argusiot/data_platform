'''
   class StateSetProcessor

   This class builds a StateSetProcessor object from the supplied JSON
   description of a state set 

   See $HOME/data_platform/design_docs/README.quilt_and_applique_infra_design
   for details.
'''
from collections import OrderedDict

import requests
import json
import time

from argus_tal import timeseries_id as ts_id
from argus_tal import query_api
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
from argus_tal.timeseries_datadict import LookupQualifier, TimeseriesDataDict


class StateSetProcessor(object):
    def __init__(self, name, temporal_state_obj_list,
                 tsdb_hostname_or_ip, tsdb_port, flag_msec_query_response):

        self.__name = str(name)

        # List of temporal state objects.
        self.__temporal_state_obj_list = temporal_state_obj_list

        # Used for connecting to the TSDB to R/W:
        #   - reads are done to query data for temporal state computation.
        #   - writes are done to write the state computation result.
        self.__tsdb_hostname_or_ip = tsdb_hostname_or_ip
        self.__tsdb_port_num = tsdb_port

        # Flag to control the granularity at which we want the response to be
        self.__flag_msec_response = flag_msec_query_response

        # Optimization:
        # Collect all the timeseries IDs in a set. Later when we peridiocally
        # query for this ts_ids, having them in a single set allows for
        # making a single query to get their data.
        self.__read_tsids = set()
        for t_state in temporal_state_obj_list:
            for ts_id in t_state.read_tsid_list:
                self.__read_tsids.add(ts_id)

    '''
    As the name suggests, this is intended to be used for "one shot" state
    set computation processing for the supplied query time window.

      q_start_time, q_end_time:
          The time window to be used for doing the query.

      output_granularity_in_sec:
          This governs the granularity at which the state set processing
          results are computed and written back to the TSDB.

      Example:
            Say following values are supplied:
            q_start_time = 2/2/2021 00:01:00
            q_end_time = 2/2/2021 00:02:00  (difference is 1hr)
            output_granularity_in_sec = 10sec

            With these parameter values, one_shot() will query data for the 1hr
            time window (from start to end time). Within that query result, it
            will compute the first state sets at "start_time + 10sec" and then
            for every 10sec after that until it exceeds end_time.
    '''

    def getTimeSeriesData(self, list_ts_ids, start_timestamp, end_timestamp):
        foo = query_api.QueryApi(
            self.__tsdb_hostname_or_ip, self.__tsdb_port_num,
            start_timestamp, end_timestamp,
            list_ts_ids,
            bt.Aggregator.NONE,
            flag_ms_response=self.__flag_msec_response
        )

        rv = foo.populate_ts_data()
        assert rv == 0

        result_map = foo.get_result_map()

        return result_map

    def push_data(self, timestamp, metric, state, value):
        url = 'http://%s:%d/api/put' % (self.__tsdb_hostname_or_ip,
                                        self.__tsdb_port_num)
        headers = {'content-type': 'application/json'}
        datapoint = {}
        datapoint['metric'] = metric
        datapoint['timestamp'] = timestamp
        datapoint['value'] = value
        datapoint['tags'] = {}
        datapoint['tags']['state'] = state
        response = requests.post(url, data=json.dumps(datapoint), headers=headers)
        return response, datapoint['timestamp']

    def __calculate_y_intercept(self, p1_coordinates, p2_coordinates, x_intercept):
        x1, y1 = p1_coordinates
        x2, y2 = p2_coordinates

        m = (y2 - y1) / (x2 - x1)
        c = y1 - (m * x1)
        y_intercept = (m * x_intercept) + c
        return y_intercept

    def build_sync_interpolated_data(self, start_timestamp, end_timestamp, periodicity):
        tsdd_map = self.getTimeSeriesData(list(self.__read_tsids), start_timestamp, end_timestamp)
        result_map = {}

        # FIXME: This is a short term hack and needs more thoughts. We assume
        # that if data is being requested at msec granularity, then:
        # a) there is no data loss
        # b) data across different timeseries is synchronized
        # ....hence we don't need to run build_sync_interpolated_data() and
        # simply return the query response as is.
        if self.__flag_msec_response:
            for fqid, tsdd in tsdd_map.items():
                tsid = tsdd.get_timeseries_id()
                result_map.update({tsid.fqid: tsdd})
            return result_map


        for fqid, tsdd in tsdd_map.items():
            data_points = OrderedDict()
            tsid = tsdd.get_timeseries_id()
            prev_element = (0, 0)
            for cur_index, (key, value) in enumerate(tsdd):
                if cur_index == 0:  # Filling gap between start_time and first available datapoint
                    if key == start_timestamp.value:
                        data_points.update({key: value})
                    else:
                        # TBD Note:No Interpolation possible for the start gap
                        data_points.update({key: value})
                elif cur_index == len(tsdd) - 1:  # Filling gap between end_time and last available datapoint
                    if key == end_timestamp.value:
                        data_points.update({key: value})
                    else:
                        # TBD Note:No Interpolation possible for the end gap
                        data_points.update({key: value})
                else:  # Interpolate all other elements as per periodicity
                    if key - prev_element[0] == periodicity:
                        data_points.update({key: value})
                    else:
                        required_key = prev_element[0] + periodicity
                        while required_key < key:
                            data_points.update(
                                {required_key: self.__calculate_y_intercept(prev_element, (key, value), required_key)})
                            required_key += periodicity
                        data_points.update({key: value})
                prev_element = (key, value)

            updated_tsdd = TimeseriesDataDict(tsid, data_points)
            result_map.update({tsid.fqid: updated_tsdd})

        return result_map

    def one_shot(self, start_time, end_time, output_granularity_in_sec):
        total_missed_time = 0  # Temporary test variable
        current_time = start_time
        while current_time < end_time:
            current_period_end_time = current_time + output_granularity_in_sec
            start_timestamp = ts.Timestamp(current_time)
            end_timestamp = ts.Timestamp(current_period_end_time)
            result_map = self.build_sync_interpolated_data(start_timestamp, end_timestamp, 1)
            # result_map = self.getTimeSeriesData(list(self.__read_tsids), start_timestamp, end_timestamp)
            #
            #
            # min_ending_time_set = set()
            # for key, value in result_map.items():
            #     t = value.get_max_key()
            #     min_ending_time_set.add(t)
            #
            # min_end_ts = min(min_ending_time_set)
            # end_timestamp = ts.Timestamp(min_end_ts)
            # result_map = self.getTimeSeriesData(list(self.__read_tsids), start_timestamp, end_timestamp)

            time_spent_list = []
            error = False
            for t_state in self.__temporal_state_obj_list:
                try:
                    time_spent = t_state.do_computation(result_map)
                    time_spent_list.append((t_state.write_tsid.metric_id,
                                            t_state.write_tsid.filters.get('state_label'), time_spent))
                    # self.push_data(min_end_ts, t_state.write_tsid.metric_id,
                    #                t_state.write_tsid.filters.get('state_label'), time_spent)
                except ValueError as e:
                    print(e)
                    print("ERROR: Processing Start:" + str(current_time) + " End:" + str(current_period_end_time))
                    error = True
                    self.push_data(current_period_end_time, t_state.write_tsid.metric_id,
                                   'SystemError', current_period_end_time - current_time)
                    break

            if not error:
                total_time = current_period_end_time - current_time
                for element in time_spent_list:
                    self.push_data(current_period_end_time, element[0], element[1], element[2])
                    total_time -= int(element[2])
                if total_time != 0:
                    print("STATE ERROR: Time unaccounted for between Start:" + str(current_time) + " End:" + str(
                        current_period_end_time))
                    total_missed_time += total_time
            current_time = current_period_end_time
        return

    '''
    This call blocks to never return. Every 'periodicity_in_sec' this method:
       - does a query,
       - computes state set using query result,
       - writes the result back to TSDB

    FIXME: Parag to remove this "blocking_start" restriction later once he's
           wrapped his head around Python's asyncio primitivies. For now, we
           live with this.
    '''

    def blocking_start(self, periodicity_in_sec):
        while True:
            start_time = time.time()
            end_time = start_time + periodicity_in_sec
            self.one_shot(start_time, end_time, periodicity_in_sec)
            time.sleep(periodicity_in_sec)
            pass
        return

    def async_start(self, periodicity_in_sec):
        # Currently unsupported.
        raise Exception("Unsupported")

    @property
    def name(self):
        return self.__name

    # This method is meant to be used for testing only. Should NOT be used in
    # production code.
    def _get_temporal_obj_list(self):
        return self.__temporal_state_obj_list
