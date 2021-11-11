#!/usr/bin/python3
'''
  coil_number_query.py

  Skeletal tool should how to query by coil number, analyse the results and
  then do more fun stuff...

  Note: The querying assumptions made here are POC grade. If the initial query
        fails that needs to be handled more gracefully.
'''

import argparse
from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
from argus_tal import query_urlgen as qurlgen
from argus_tal import timeseries_datadict as tsd
from argus_tal.timeseries_datadict import LookupQualifier as LQ
from collections import OrderedDict
import datetime
import itertools
import pandas as pd
import pickle

'''
   Helper method.

   Input: Single timeseries ID, start_time & end_time
   Output: A tuple: (TimeseriesDataDict, Dataframe). Both contain same data.
'''
def __query_and_get_result(tseries_id, start_time, end_time, tsdb_host, tsdb_port, rate_query=False):
  start_timestamp = ts.Timestamp(start_time)
  end_timestamp = ts.Timestamp(end_time)

  # Observe that tseries_id is supplied as a list because can query multiple
  # timeseries at the same time (for the same time window).
  value_query = query_api.QueryApi(
          tsdb_host, tsdb_port,
          start_timestamp, end_timestamp,
          [tseries_id],
          bt.Aggregator.NONE,
          rate_query,   # Controls whether this a rate vs regular query.
          flag_ms_response=True
        )
  rv = value_query.populate_ts_data()
  assert rv == 0

  df_map = value_query.get_result_as_dataframes()
  tsdd_map = value_query.get_result_map()

  # Return tuple of results (TSDD object, dataframe).
  return tsdd_map[tseries_id.fqid], df_map[tseries_id.fqid]


'''
   Check if the supplied coil_num is consistent in the timestamp range supplied.

   Return True if coil_num is consistent, False otherwise.
'''
def __audit_coil_number_index(time_ranges, coil_number_dict):
    print("Auditing coil_number_dict")
    print("Skipping time ranges audit i.e. ignoring gaps in time ranges.\n"
          "As a result some audit failures may not be legitimate.")
    failed_audit = 0
    failed_coils = []
    coil_number_list = list(coil_number_dict.items())
    for ii in range(0, len(coil_number_list) - 1):
        cur_coil, (cur_start, cur_end) = coil_number_list[ii]
        next_coil, (next_start, next_end) = coil_number_list[ii + 1]
        if cur_end != next_start:
            failed_audit = failed_audit + 1
            failed_coils.append(int(cur_coil))
    print("Total coils: %d, Possible audit failures: %d\n" % (len(coil_number_dict), failed_audit))
    print("List of failed coil IDs: %s" % str(cur_coil))


'''
Phase 1:
1. Generate dataframe out of rate_result_list.
2. Filter out all rows with "value != 0" to get a data frame back.
3. In the resulting dataframe, process successive pairs of rows gathering
   timestamps. Each pair corresponds to the time range over which the same
   coil number exists.
4. Audit result from previous step.
5. If audit passes, Store in dict: coil_num -> (start, end).
   If audit fails, we report failure and continue processing.

Side effects of this method:
  For each coil number in the (start_time, end_time) range the dict will
  get updated as follows:
  coil_number_dict[coil_number] = (coil start, coil end)
'''
def process_time_window(context, tsdb_host, tsdb_port, tseries_id,
                        start_time, end_time):
    '''
    Step 1: Get value and rate query results for Coil number in supplied time window.
    '''
    values_tsdd, values_df = __query_and_get_result(tseries_id,
            start_time, end_time, tsdb_host, tsdb_port)
    rate_tsdd, rate_df = __query_and_get_result(tseries_id,
            start_time, end_time, tsdb_host, tsdb_port, rate_query=True)
    if len(values_tsdd) == 0:
        print("Skipping empty response")
        return end_time

    '''
     Step 2: The coil number is rising* step function. Consequently the values in
             the rate query result will contain just a sequence like this:
             [0, 0, 0, 0, NZ, 0, 0, 0, 0, NZ, ...]

             0 indicates no change in coil number from time stamp.
             NZ is a non-zero value when the coil number changed.

             Whenever the value is 0, it corresponds to a steady "level" of the
             step function. The NZ value corresponds to the edge.

             In this steo, we need the timestamps corresponding to all the NZ
             values i.e. the edges. Hence the variable below 'edges_df'.

             *Note: Handling coil number wrap around
             The coil number wraps around at 499,999 and goes to 200,000.
             That still gets handled here.
    '''
    edges_df = rate_df[rate_df['result'] != 0]

    for ii in range(len(edges_df)):
        # We do some cross-referencing here. The cross referencing works
        # because we're guaranteed that the reponses to the rate_query and
        # value_query are timestamp aligned.
        #
        # Use the timestamp from the edge_df (which is derived from rate_query)
        # to lookup values_tsdd and get the coil_number.
        _, coil_num = values_tsdd.get_datapoint(edges_df.iloc[ii]['timestamp'],
                                             tsd.LookupQualifier.EXACT_MATCH)
        if context['coil_num_start_ts'] == -1.0:
            context['coil_num_start_ts'] = edges_df.iloc[ii]['timestamp']
            context['coil_num'] = coil_num
        else:
            # Finish processing coil being tracked.
            coil_num_start_ts, coil_num_end_ts = (context['coil_num_start_ts'],
                                                  edges_df.iloc[ii]['timestamp'])
            context['cn_dict'][coil_num] = (coil_num_start_ts, coil_num_end_ts)

            # Start tracking next coil.
            context['coil_num_start_ts'] = edges_df.iloc[ii]['timestamp']
            context['coil_num'] = coil_num

    # Returns: the last time stamp for which edge was detected.
    return edges_df.iloc[-1]['timestamp']

# start & end time are in seconds since epoch
def generate_coil_number_idx(coil_number_dict, tsdb_host, tsdb_port,
                             start_time, end_time):
  tseries_id = ts_id.TimeseriesID("poc.v3.coil.number", {"machine_id":"900-18"})
  delta = 86400 * 1000 # Milliseconds in a day
  q_start = start_time * 1000
  end_time = end_time * 1000

  window_count = 1

  # Setup the context here that will get used across call to process_time_window
  context = {
      'cn_dict': coil_number_dict,  # result: Stores coil number->(start, end)
                                    #         as they are detected.
                                    #
      'coil_num_start_ts' : -1,     # tracker: Stores start timestamp for coil
      'coil_num': -1                #          and associated coil number.
  }
  while True:
      q_end = q_start + delta
      print("\t[Window %d] Processing time range: %d %d upto %d" %
              (window_count, q_start, q_end, end_time))
      next_start = process_time_window(context,
              tsdb_host, tsdb_port, tseries_id, q_start, q_end)
      if q_end >= end_time or next_start == q_start:
          break
      q_start = next_start
      window_count = window_count + 1

  return

def main():
  parser = argparse.ArgumentParser(description='Plot a cobble tail')
  parser.add_argument('--TSDB_host', type=str, help='TSDB hostname or IP addr',
                      default="localhost")
  parser.add_argument('--TSDB_port', type=int, help="TSDB TCP por number",
                      default=4242)
  args = parser.parse_args()

  print("Connecting to TSDB at %s:%d" % (args.TSDB_host, args.TSDB_port))

  # Stores the result
  coil_number_dict = OrderedDict()

  time_ranges = [
          ("02-01-2021 00:00:00", "02-01-2021 23:59:59"),    # skip 2/2-2/3
          ("02-04-2021 00:00:00", "02-27-2021 23:59:59"),    # skip 2/28 & entire March
          ("04-01-2021 00:00:00", "04-13-2021 23:59:59"),  # skip 4/14
          ("04-15-2021 00:00:00", "04-27-2021 23:59:59"),  # skip 4/28
          ("04-29-2021 00:00:00", "05-12-2021 23:59:59"),    # skip 5/13-5/19 -- 2 diff problems ...1 problem is that there's no change in coiler ID over entire range.
          ("05-20-2021 00:00:00", "05-22-2021 23:59:59"),    # skip 5/22
          ("05-24-2021 00:00:00", "05-31-2021 23:59:59"),
      ]
  format_str = "%m-%d-%Y %H:%M:%S"
  for (start_time_str, end_time_str) in time_ranges:
      print("Generating coil number index from %s to %s" % (start_time_str,
                                                            end_time_str))
      generate_coil_number_idx(coil_number_dict,
          args.TSDB_host, args.TSDB_port,
          datetime.datetime.strptime(start_time_str, format_str).timestamp(),
          datetime.datetime.strptime(end_time_str, format_str).timestamp())

  __audit_coil_number_index(time_ranges, coil_number_dict)

  pickle_file = "CoilNumberIndex.pickle"
  print("Picking coil number index into %s" % pickle_file)

  with open(pickle_file, 'wb') as handle:
    pickle.dump(coil_number_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

  with open(pickle_file, 'rb') as handle:
    tmp_cn_dict = pickle.load(handle)

  assert tmp_cn_dict == coil_number_dict

if __name__ == "__main__":
  # execute only if run as a script
  main()
