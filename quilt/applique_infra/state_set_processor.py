'''
   class StateSetProcessor

   This class builds a StateSetProcessor object from the supplied JSON
   description of a state set 

   See $HOME/data_platform/design_docs/README.quilt_and_applique_infra_design
   for details.
'''

from argus_tal.timeseries_id import TimeseriesID

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
    def one_shot(self, start_time, end_time, output_granularity_in_sec):

        # VISHWAS to fill in

        # 1. For read (i.e query): using self.__read_tsids
        # 2. Query results can be obtained as a map using get_result_map()
        # 3. Iterate over all the temporal state objects to allow them compute
        #    "time spent in state". *Use the result_map from step #2.
        # 4. Write the result from each state computation into TSDB.
        #    For write: use self.__temporal_state_obj_list[idx].write_tsid
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
            # 1. start_time = Get current time
            # 2. end_time = start_time - periodicity_in_sec
            # 3. self.one_shot(start_time, end_time, periodicity_in_sec)
            # 4. sleep(periodicity_in_sec)
            pass
        return # should never reach here

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
