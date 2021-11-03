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
   Input: Single timeseries ID, start_time & end_time
   Output: A single TimeseriesDataDict object
'''
def get_query_result_as_df(tseries_id, start_time, end_time, result_col_name="result",
                     host="localhost", tcp_port=4242, rate_query=False, generate_df=False):
  start_timestamp = ts.Timestamp(start_time)
  end_timestamp = ts.Timestamp(end_time)

  # Observe that tseries_id is supplied as a list because can query multiple
  # timeseries at the same time (for the same time window).
  value_query = query_api.QueryApi(
          host, tcp_port,
          start_timestamp, end_timestamp,
          [tseries_id],
          bt.Aggregator.NONE,
          rate_query,   # Controls whether this a rate vs regular query.
          flag_ms_response=True
        )
  rv = value_query.populate_ts_data()
  assert rv == 0

  value_result_list = value_query.get_result_set()
  assert len(value_result_list) == 1

  if generate_df:
      tsdd_to_df_xform_dict = {'timestamp': [], result_col_name: []}
      for kk,vv in value_result_list[0]:
          tsdd_to_df_xform_dict['timestamp'].append(kk)
          tsdd_to_df_xform_dict[result_col_name].append(vv)
      result_as_df = pd.DataFrame.from_dict(tsdd_to_df_xform_dict)
  else:
      result_as_df = None

  # Return the result as a TSDD object and also a dataframe.
  return value_result_list[0], result_as_df


'''
   Check if the supplied coil_num is consistent in the timestamp range supplied.

   Return True if coil_num is consistent, False otherwise.
'''
def __is_coil_number_consistent(values_tsdd, coil_num, start_ts, end_ts):
  incr_ms = 100
  for cur_ts in range(int(start_ts), int(end_ts), incr_ms):
      _, vv_s = values_tsdd.get_datapoint(cur_ts,
                                           tsd.LookupQualifier.NEAREST_SMALLER)
      _, vv_l = values_tsdd.get_datapoint(cur_ts,
                                           tsd.LookupQualifier.NEAREST_LARGER)
      if vv_s != coil_num and vv_l != coil_num:
          print("[Err at %s]: Expected coil %s" % (str(cur_ts), str(coil_num)))
          return False
  return True


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
def process_time_window(coil_number_dict, coil_num_tracker, tseries_id,
                        start_time, end_time, skip_coil_num_audit):
    '''
    Step 1: Get value and rate query results for Coil number in supplied time window.
    '''
    values_tsdd, values_df = get_query_result_as_df(tseries_id, start_time, end_time, generate_df=True)
    rate_tsdd, rate_df = get_query_result_as_df(tseries_id, start_time, end_time,
                                                rate_query=True, generate_df=True)
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

        # When the tracker is unitialized, there's nothing after this to do.
        if coil_num_tracker == -1.0:
            coil_num_tracker = edges_df.iloc[ii]['timestamp']
            continue

        
        coil_num_start_ts, coil_num_end_ts = (coil_num_tracker,
                                              edges_df.iloc[ii]['timestamp'])
        coil_num_tracker = edges_df.iloc[ii]['timestamp']
        '''
          Step 4: Audit that the the coil number is same over the following time
                  range - [coil_num_start_ts, coil_num_end_ts)
        '''
        if skip_coil_num_audit:
            coil_number_dict[coil_num] = (coil_num_start_ts, coil_num_end_ts)
        elif __is_coil_number_consistent(values_tsdd, coil_num,
                                       coil_num_start_ts, coil_num_end_ts):
            # Step 5: Audit passed ! We can store results.
            coil_number_dict[coil_num] = (coil_num_start_ts, coil_num_end_ts)
        else:
            print("Ooops. Coil number %d failed time range audit %s %s" %
                  (coil_num, coil_num_start_ts, coil_num_end_ts))

    # Returns:
    #        the last time stamp for which edge was detected.
    #        the coil_num tracker
    if edges_df.iloc[-1]['timestamp'] == coil_num_start_ts:
        print("Warning last time %d stamp same as first." % coil_num_start_ts)
        return coil_num_end_ts, coil_num_tracker
    else:
        return edges_df.iloc[-1]['timestamp'], coil_num_tracker

# start & end time are in seconds since epoch
def generate_coil_number_idx(coil_number_dict, start_time, end_time, skip_coil_num_audit):
  tseries_id = ts_id.TimeseriesID("poc.v3.coil.number", {"machine_id":"900-18"})
  delta = 86400
  q_start = start_time
  # We want a do..while loop here. In absence of that we achieve that result
  # with this while True and using a 'break' inside on a condition.
  coil_num_tracker = -1.0
  while True:
      q_end = q_start + delta
      print("Processing time range: %d %d" % (q_start, q_end))
      tmp, coil_num_tracker = process_time_window(coil_number_dict,
                                                  coil_num_tracker, tseries_id,
                                                  q_start, q_end,
                                                  skip_coil_num_audit)
      next_start = tmp / 1000
      if q_end > end_time:
          break
      q_start = next_start

  return

def main():
  parser = argparse.ArgumentParser(description='Generate the coil number index')
  parser.add_argument('--skip_coil_number_audit', type=bool, help='Audit the coil numbers found in each time window', default=True)
  args = parser.parse_args()

  # Stores the result
  coil_number_dict = OrderedDict()

  time_ranges = [
              ("02-01-2021 00:00:00", "02-23-2021 06:00:00"),
           #   ("02-24-2021 10:00:00", "04-14-2021 07:00:00"),
           #   ("04-14-2021 13:00:00", "05-19-2021 03:00:00"),
           #   ("05-19-2021 13:00:00", "05-31-2021 16:50:00"),
          ]
  print("Skipping coil number audit : %s" % args.skip_coil_number_audit)
  format_str = "%m-%d-%Y %H:%M:%S"
  for (start_time_str, end_time_str) in time_ranges:
      print("Generating coil number index from %s to %s" % (start_time_str,
                                                            end_time_str))
      generate_coil_number_idx(coil_number_dict,
          datetime.datetime.strptime(start_time_str, format_str).timestamp(),
          datetime.datetime.strptime(end_time_str, format_str).timestamp(),
          args.skip_coil_number_audit)

  pickle_file = "CoilNumberIndex.pickle"
  print("Picking coil number index into %s" % pickle_file)

  with open(pickle_file, 'wb') as handle:
    pickle.dump(coil_number_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

  # Audit the picked file by doing a readback and verify
  with open(pickle_file, 'rb') as handle:
    tmp_cn_dict = pickle.load(handle)

  assert tmp_cn_dict == coil_number_dict

if __name__ == "__main__":
  # execute only if run as a script
  main()
