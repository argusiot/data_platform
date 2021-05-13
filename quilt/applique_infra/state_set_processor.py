'''
   class StateSetProcessor

   This class builds a StateSetProcessor object from the supplied JSON
   description of a state set 

   See $HOME/data_platform/design_docs/README.quilt_and_applique_infra_design
   for details.
'''
import requests
import json
import time

from argus_tal import timeseries_id as ts_id
from argus_tal import query_api
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt


class StateSetProcessor(object):
    def __init__(self, name, temporal_state_obj_list, tsdb_url):

        self.__name = str(name)

        # List of temporal state objects.
        self.__temporal_state_obj_list = temporal_state_obj_list

        # TSDB URL to be used for doing -- reading & writing to the TSDB
        #   - reads are done to query data for temporal state computation.
        #   - writes are done to write the state computation result.
        self.__tsdb_url = tsdb_url

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
            "34.221.154.248", 4242,
            start_timestamp, end_timestamp,
            list_ts_ids,
            bt.Aggregator.NONE,
            False,
        )

        rv = foo.populate_ts_data()
        assert rv == 0

        result_map = foo.get_result_map()

        return result_map

    def push_data(self, timestamp, metric, state, value):
        url = 'http://34.221.154.248:4242/api/put'
        headers = {'content-type': 'application/json'}
        datapoint = {}
        datapoint['metric'] = metric
        datapoint['timestamp'] = timestamp
        datapoint['value'] = value
        datapoint['tags'] = {}
        datapoint['tags']['state'] = state
        # response = requests.post(url, data=json.dumps(datapoint), headers=headers)
        # return response, datapoint['timestamp']

    def one_shot(self, start_time, end_time, output_granularity_in_sec):

        current_time = start_time
        while current_time < end_time:
            start_timestamp = ts.Timestamp(current_time)
            end_timestamp = ts.Timestamp(current_time + output_granularity_in_sec)
            result_map = self.getTimeSeriesData(list(self.__read_tsids), start_timestamp, end_timestamp)

            min_ending_time_set = set()
            for key, value in result_map.items():
                t = value.get_max_key()
                min_ending_time_set.add(t)

            min_end_ts = min(min_ending_time_set)
            end_timestamp = ts.Timestamp(min_end_ts)
            result_map = self.getTimeSeriesData(list(self.__read_tsids), start_timestamp, end_timestamp)

            for t_state in self.__temporal_state_obj_list:
                try:
                    time_spent = t_state.do_computation(result_map)
                    print(time_spent)
                    self.push_data(end_timestamp, t_state.write_tsid.metric_id,
                                   t_state.write_tsid.filters.get('state_label'), time_spent)
                except ValueError as e:
                    print(e)
                    self.push_data(end_timestamp, t_state.write_tsid.metric_id,
                                   'SystemError', min_end_ts - current_time)
            current_time = min_end_ts
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
