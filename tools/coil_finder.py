#!/usr/bin/python3
'''
    coil_finder.py

    Utility for random access find of a coil by coil number.
'''

import resource
import argparse
from pprint import pprint
import time

from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
from argus_tal import query_urlgen as qurlgen
from argus_tal import timeseries_datadict as tsd
from argus_tal.timeseries_datadict import LookupQualifier as LQ

def timelog(t0, msg, show=True):
    # Prints the msg with time stamp relative to t0.
    # The msg is only printed if show is True; used to control verbosity
    if show:
        print(f"{time.time() - t0:.2f}: {msg}")

def print_epilogue(startTime, verbose=0):
    if verbose >= 1:
        print('Peak Memory Usage =',
              resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        print('User Mode Time =',
              resource.getrusage(resource.RUSAGE_SELF).ru_utime)
        print('System Mode Time =',
              resource.getrusage(resource.RUSAGE_SELF).ru_stime)
        print('Execution time in seconds: ' + str(time.time() - startTime))


def get_query_result_list(timeseries_id, start_time, end_time,
                          flag_compute_rate=False):
    start_timestamp = ts.Timestamp(start_time)
    end_timestamp = ts.Timestamp(end_time)
    serverip = "192.168.1.154"
    serverport = 4242
  
    # Observe that timeseries_id is supplied as a list because can query multiple
    # timeseries at the same time (for the same time window).
    foo = query_api.QueryApi(
      serverip, serverport, 
      start_timestamp, end_timestamp,
      [timeseries_id],
      bt.Aggregator.NONE,
      flag_compute_rate,   # Controls whether this a rate vs regular query.
      flag_ms_response=True
    )

    rv = foo.populate_ts_data()
    if rv != 0:
        timelog(show=(vb >= 2), t0=startTime,
                msg=f"      t:{start_timestamp} - {end_timestamp}")
        assert rv == 0

    # The outcome of populate_ts_data() is available as a list of
    # Timeseries_DataDict objects. Lets get these out.
    result_list = foo.get_result_set()
    # assert len(result_list) == 1  # We expect to get exactly 1 timeseries back

    return result_list

def print_query_result(result_list, flag_compute_rate=False, vb=0):
    print(f"Rate query: {str(flag_compute_rate)}")
    print(f"Number of timeseries retrieved -- {len(result_list)}")
    for result in result_list:
        print("Retrieved timeseries id : %s" % str(result.get_timeseries_id()))
        print("Datapoints:")
        for kk, vv in result:
            print("\t%s->%d" % (kk, vv))

def get_edge_dps (start_time, end_time=None, qw=10000, vb=0):
    # Return first and last dp in range, and the distance between them.

    # query window is 10000ms.
    qw = 10000

    if end_time == None:
        end_time = start_time + qw
        dist = qw
    else:
        dist = end_time - start_time

    if vb >=2:
        print(f"   Start: {start_time}, End: {end_time}, Gap: {dist}, QW: {qw}")

    timeseries_id = ts_id.TimeseriesID("poc.v3.coil.number",
                                       {"machine_id":"900-18"})

    if dist <= qw:
        start_list = get_query_result_list(timeseries_id,
                                           start_time, end_time,
                                           flag_compute_rate=False)
        last_coil_dp = start_list[-1].get_datapoint(end_time,
                                                    LQ.NEAREST_LARGER_WEAK)
    else:  
        start_list = get_query_result_list(timeseries_id,
                                           start_time, start_time + qw,
                                           flag_compute_rate=False)
        end_list = get_query_result_list(timeseries_id,
                                         end_time - qw, end_time,
                                         flag_compute_rate=False)
        if vb >=3:
            print_query_result(end_list, flag_compute_rate=False)
        if vb >=2:
            print(f"end list = {len(end_list)}")
        last_coil_dp = end_list[-1].get_datapoint(end_time,
                                                  LQ.NEAREST_LARGER_WEAK)

    if vb >=3:
        print_query_result(start_list, flag_compute_rate=False)

    first_coil_dp = start_list[0].get_datapoint(start_time,
                                                LQ.NEAREST_SMALLER_WEAK)

    if vb >2:
        print (f"    Coil: {first_coil_dp[1]} - {last_coil_dp[1]}")
        print (f"    Time: {start_time} - {end_time}")
        print (f"    Actual: {first_coil_dp[0]} - {last_coil_dp[0]}")

    return { "first":first_coil_dp, "last":last_coil_dp, "dist":dist}
  
  
def find_coil_num_time (coil_num, start_time, end_time, vb=0):
  
    # get first & last dp
    edge_dps = get_edge_dps(start_time, end_time=end_time)

    first_time, first_coil = edge_dps["first"]
    last_time, last_coil = edge_dps["last"]

    if vb >= 2:
        print (f"  Coil: {coil_num}: {first_coil}-{last_coil}")
        print (f"  Time: {start_time}-{end_time} "
               f"Actual: {first_time}-{last_time}")

    # check against edge dps
    if coil_num == first_coil:
        return True, first_time
    elif coil_num == last_coil:
        return True, last_time

    if (coil_num < first_coil) or (coil_num > last_coil):
        return False, 0

    # The coil num is somewhere in the range. Let's guess!

    coil_num_range = last_coil - first_coil
    range_ratio = (coil_num - first_coil)/coil_num_range

    guess_time = first_time + (edge_dps["dist"] * range_ratio)

    guess_dps = get_edge_dps(guess_time, qw=1000)

    # Check last one first
    guess_dp_time, guess_coil = guess_dps["last"]
    if guess_coil == coil_num:
        return True, guess_dp_time

    guess_dp_time, guess_coil = guess_dps["first"]
    if guess_coil == coil_num:
        return True, guess_dp_time
    elif coil_num < guess_coil:
        # Searched coil num is the "left" portion
        return find_coil_num_time(coil_num, start_time, guess_dp_time)
    else:
        # Searched coil num is the "right" portion
        return find_coil_num_time(coil_num, guess_dp_time, end_time)
  
def find_coil_num_step (start_time, end_time):

    # If there's an edge in interval:
    #    split interval in 2.
    #    if there's an edge in left interval split left interval
    #    else if there's an edge in right interval split right interval
    #    else return false

    # dist = end_time - start_time  
    # if dist < query_interval
    #   get 1 query
    #   get first dp @ start time
    #   get last dp @ end time
    # else 
    #   get first query
    #   get last query
    #   get first dp @ start time in first range
    #   get last dp @ end time in last range

    # if first_dp.value==last_dp_value,
    #   there is no edge in this interval
    #   return false, 0
    # else 

    # get mid dp (first+dist DP)

    # if first..mid dp has an edge
    #   return true, edge time

    # else if mid dp .. last has an edge
    #   return true, edge time
  
    # if first_dp.value!=last_dp_value,
    #    # There is an edge in the interval
    #    if (return find_coil_num_edge(start_time, end_time-dist/2))
    # else
    #    # There is no edge in the interval
    #    if start_time == end_time
    #       return true
    #    else
    #       return false
    #    return find_coil_num_edge(start_time

    return

def print_coil_number_window(start_time, end_time):
    # CHANGE HERE: Use coil_number metric & tags
    timeseries_id = ts_id.TimeseriesID("poc.v3.coil.number",
                                       {"machine_id":"900-18"})

    coilnum_list = get_query_result_list(timeseries_id, start_time, end_time,
                                         flag_compute_rate=False)
    coilnumrate_list = get_query_result_list(timeseries_id,
                                             start_time, end_time,
                                             flag_compute_rate=True)
    print_query_result(coilnum_list, flag_compute_rate=False)
    print_query_result(coilnumrate_list, flag_compute_rate=True)

def generate_coil_number_time_windows(start_time, end_time):
    # CHANGE HERE: Use coil_number metric & tags
    timeseries_id = ts_id.TimeseriesID("poc.v3.coil.number",
                                       {"machine_id":"900-18"})

    coilnum_list = get_query_result_list(timeseries_id, start_time, end_time,
                                         flag_compute_rate=False)
    coilnumrate_list = get_query_result_list(timeseries_id,
                                             start_time, end_time,
                                             flag_compute_rate=True)
    print_query_result(coilnum_list, flag_compute_rate=False)
    print_query_result(coilnumrate_list, flag_compute_rate=True)

    first_coil_dp = coilnum_list[0].get_datapoint(start_time, LQ.EXACT_MATCH)

    first_coil_time, first_coil_num = first_coil_dp
    print (f"First coil: {first_coil_num} @ {first_coil_time}\n") 

    this_coil_num = first_coil_num
    next_coil_num = this_coil_num
    next_coil_start = str(int(first_coil_time) + 120000)
    print (f"First: {first_coil_num} Next: {next_coil_num}\n")
    while (next_coil_num < first_coil_num + 10):
        start_time = next_coil_start
        end_time = str(int(next_coil_start) + 1000)
        coilnum_list = get_query_result_list(timeseries_id,
                                             start_time, end_time,
                                             flag_compute_rate=False)
        coilnumrate_list = get_query_result_list(timeseries_id,
                                                 start_time, end_time,
                                                 flag_compute_rate=True)
        #print_query_result(coilnum_list, flag_compute_rate=False)
        #print_query_result(coilnumrate_list, flag_compute_rate=True)

        next_coil_dp = coilnum_list[0].get_datapoint(int(start_time),
                                                     LQ.NEAREST_LARGER_WEAK)

        this_coil_time, this_coil_num = next_coil_dp
        if this_coil_num != next_coil_num:
            print (f"Sample coil: {this_coil_num} @ {this_coil_time}\n")
            print (f"First: {first_coil_num} Next: {next_coil_num}\n")

            next_coil_num = this_coil_num
            next_coil_start = str(int(this_coil_time) + 30000)

    return

def main():

    psr = argparse.ArgumentParser(description="Argus coil finder")
    psr.add_argument("start_time", type=int,
                     help="First time stamp to search")
    psr.add_argument("--end_time", type=int, default=0,
                     help="First time stamp to search")
    psr.add_argument("--coilcnt", type=int, default=10,
                     help="How many coil numbers to")
    psr.add_argument("--coilnum", type=int, default=0,
                     help="Which coil number to find")
    psr.add_argument("-v", "--verbose", action='count', default=0,
                     help=("Verbose progress logs and debugs. "
                           "Repeat (eg. -vvv) for more verbose"))

    args = psr.parse_args()

    vb = args.verbose

    startTime = time.time()
    t0 = args.start_time
    if args.end_time:
        t1 = args.end_time
    else:
        t1 = t0 + 3600000

    if args.coilnum:
        found, attime = find_coil_num_time(args.coilnum, t0, t1)

        if found:
            print (f"Found {args.coilnum} at {attime}.")
            if vb >=2:
                print_coil_number_window(attime, attime+1000)
        else:
            print (f"Did not find {args.coilnum}.")
        print_epilogue(startTime, verbose = vb)

    else:
        # CHANGE HERE: supply start time, end time e.g.
        # generate_coil_number_time_windows(1618307351000,1618307371000)
        generate_coil_number_time_windows(t0,str(int(t0)+100))

    '''
    Will be needed when you have to query interesting signals for the start 
    and end timestamp associated with a coil number.

    q_obj = QueryApi(....,[foo_ts1, bar_ts, wr_position_ts],....)
    q_obj.populate_...()

    This would be useful to organize code:
        TimeseriesID::fqid
        res_map = q_obj.get_result_map()
        result_for_foo_ts1 = res_map[foo_ts1.fqid]
    '''

if __name__ == "__main__":
    # execute only if run as a script
    main()
