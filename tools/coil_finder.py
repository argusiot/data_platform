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
  
    # Observe that timeseries_id is supplied as a list because can query 
    # multiple timeseries at the same time (for the same time window).
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
        print(f"      t:{start_timestamp} - {end_timestamp}")
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

def compare_coil_num(first_dp, last_dp):
    # This function is a special compare functon for coil numbers.
    # It makes the following assumptions:
    #  1. coil numbers are strictly increasing by time, i.e. a later coil number
    #     sample is either same value or larger.
    #  2. coil numbers wrap around (reset) to 200000 after 499999.
    # The comparison returns the diff between first_dp and last_dp,
    # i.e. 0 for equal.
    # If first is larger than last dp, wrap-around is assumed to have
    # happened once between the 2, so 300000 is subtracted from first_dp before
    # before calculating the diff.

    if first_dp > last_dp:
        return last_dp - (first_dp - 300000) 
    else:
        return last_dp - first_dp
    
def get_edge_dps (start_time, end_time=None, qw=10000, vb=0):
    # Return first and last dp in range, and the distance between them.
    # Also returns the query results to avoid having to re-query same windows
    # qw = query window size
    # vb = debug verbosity
    
    if end_time == None:
        end_time = start_time + qw
        dist = qw
    else:
        dist = end_time - start_time

    if vb >=2:
        print(f"   ged: Start: {start_time}, End: {end_time}, "
              f"Gap: {dist}, QW: {qw}")

    timeseries_id = ts_id.TimeseriesID("poc.v3.coil.number",
                                       {"machine_id":"900-18"})

    if dist <= qw:
        start_list = get_query_result_list(timeseries_id,
                                           start_time, end_time,
                                           flag_compute_rate=False)
        end_list = start_list
    else:  
        start_list = get_query_result_list(timeseries_id,
                                           start_time, start_time + qw,
                                           flag_compute_rate=False)
        end_list = get_query_result_list(timeseries_id,
                                         end_time - qw, end_time,
                                         flag_compute_rate=False)

    if vb >= 4:
        print_query_result(start_list, flag_compute_rate=False)
        print_query_result(end_list, flag_compute_rate=False)

    first_coil_dp = start_list[0].get_datapoint(start_time,
                                                LQ.NEAREST_SMALLER_WEAK)
    last_coil_dp = end_list[-1].get_datapoint(end_time,
                                              LQ.NEAREST_LARGER_WEAK)

    if vb > 2:
        print (f"    ged: Coil: {first_coil_dp[1]} - {last_coil_dp[1]}")
        print (f"    ged: Time: {start_time} - {end_time}")
        print (f"    ged: Actual: {first_coil_dp[0]} - {last_coil_dp[0]}")

    return {"first":first_coil_dp,
            "last":last_coil_dp,
            "dist":dist,
            "startlst": start_list,
            "endlst": end_list}
  
def get_center_dp (start_time, end_time=None, rel=0.5, qw=10000, vb=0):
    # Return dp at relative location of the range, as well as the query result
    # qw = query window size
    # vb = debug verbosity
    
    if end_time == None:
        end_time = start_time + qw
        dist = qw
    else:
        dist = end_time - start_time

    center_time = int(start_time + dist * rel)
    q_start = int(center_time - qw/2)
    q_end   = int(center_time + qw/2)

    if vb >= 2:
        print(f"   gcd: Start: {start_time}, End: {end_time}, "
              f"Center: {center_time}")

    timeseries_id = ts_id.TimeseriesID("poc.v3.coil.number",
                                       {"machine_id":"900-18"})

    center_list = get_query_result_list(timeseries_id,
                                        q_start, q_end,
                                        flag_compute_rate=False)

    center_coil_dp = center_list[0].get_datapoint(center_time,
                                                  LQ.NEAREST_SMALLER_WEAK)
    
    if vb >= 2:
        print (f"    gcd: Coil: {center_coil_dp[1]}")
        print (f"    gcd: Time: {q_start} / {center_time} / {q_end}")
        print (f"    gcd: Actual: {center_coil_dp[0]}")

    return {"center":center_coil_dp,
            "centerlst": center_list}  


def find_coil_num_time (coil_num, start_time, end_time, vb=0):
  
    # get first & last dp
    edge_dps = get_edge_dps(start_time, end_time=end_time, vb=vb)

    first_time, first_coil = edge_dps["first"]
    last_time, last_coil = edge_dps["last"]

    if vb >= 2:
        print (f"  fcnt: Coil: {coil_num}: {first_coil}-{last_coil}")
        print (f"  fcnt: Time: {start_time}-{end_time} "
               f"Actual: {first_time}-{last_time}")

    # check against edge dps
    if coil_num == first_coil:
        return True, first_time
    elif coil_num == last_coil:
        return True, last_time

    # Check if coil is in this time range, considering wrap-around, etc:
    # Equivalent to if (coil_num < first_coil) or (coil_num > last_coil):
    first2coil = compare_coil_num(first_coil, coil_num)
    coil2last  = compare_coil_num(coil_num, last_coil)
    first2last = compare_coil_num(first_coil, last_coil)
    if (first2coil + coil2last) > first2last:
        return False, 0

    # The coil num is somewhere in the range. Let's find it!

    relative_loc = first2coil/first2last

    # guess_time = int(first_time + (edge_dps["dist"] * relative_loc))

    guess_dps = get_center_dp(first_time, last_time, rel=relative_loc, vb=vb)

    guess_dp_time, guess_coil = guess_dps["center"]
    hops=0
    if vb >= 1:
        print (f"  fcnt: Guess coil: {guess_coil}, "
               f"guess time: {guess_dp_time}, "
               f"hops: {hops}")
    while guess_coil != coil_num:
        # break if the coil is missing in the range, e.g. looking for coil 2
        # when only 1 and 3 is there.
        # FIXME: Right now stopping after theoretical max hops in 3 months.
        hops += 1
        if hops > 28:
            print (f"Hops: {hops}, Guess coil: {guess_coil}")
            break
        
        if coil_num < guess_coil:
            # Searched coil num is the "left" portion
            last_time = guess_dp_time
            guess_dps = get_center_dp(first_time, last_time, vb=vb)
            guess_dp_time, guess_coil = guess_dps["center"]
        else:
            # Searched coil num is the "right" portion
            first_time = guess_dp_time
            guess_dps = get_center_dp(first_time, last_time, vb=vb)
            guess_dp_time, guess_coil = guess_dps["center"]

        if vb >=1:
            print (f"  fcnt: Guess coil: {guess_coil}, "
                   f"guess time: {guess_dp_time},"
                   f" hops: {hops}")

    if guess_coil == coil_num:
        return True, guess_dp_time
    else:
        return False, guess_dp_time


def find_coil_num_range (coil_num, coil_time, qw=10000, vb=0):

    # known center point
    # find edge from centerpoint - half average coil number time to centerpoint
    # If there's an edge in interval:
    #    linear search the edge.
    #
    
    start_time = coil_time - qw
    end_time = coil_time

    found = False
    hops = 0
    while not found:
        hops += 1
        edge_dps = get_edge_dps(start_time, end_time, qw=qw, vb=vb)            
        first_time, first_coil = edge_dps['first']
        if first_coil == coil_num:
            # No edge, move out
            end_time = start_time
            start_time -= qw
        else:
            found = True

    start_edge = 0
    edge_window = edge_dps['startlst']
    if vb >= 3:
        print_query_result(edge_window, flag_compute_rate=False)
    lookups = 0
    for tstamp, cnum in edge_window[0]:
        lookups += 1
        if cnum == coil_num:
            start_edge = tstamp
            break

    if vb >= 2:
        print(f"Starting edge is at: {start_edge}, "
              f"hops: {hops}, lookups: {lookups}")
          
    # Trailing edge
    start_time = coil_time
    end_time = coil_time + qw

    found = False
    hops = 0
    while not found:
        hops += 1
        edge_dps = get_edge_dps(start_time, end_time, qw=qw, vb=vb)            
        last_time, last_coil = edge_dps['last']
        if last_coil == coil_num:
            # No edge, move out
            start_time = end_time
            end_time += qw
        else:
            found = True

    trail_edge = 0
    edge_window = edge_dps['startlst']
    if vb >= 3:
        print_query_result(edge_window, flag_compute_rate=False)
    lookups = 0
    for tstamp, cnum in edge_window[0]:
        lookups += 1
        if cnum != coil_num:
            break
        else:
            trail_edge = tstamp

    if vb >= 2:
        print(f"Trailing edge is at: {trail_edge}, "
              f"hops: {hops}, lookups: {lookups}")

    return start_edge, trail_edge

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
    psr.add_argument("--start_time", type=int, default=1617235320000,
                     help="First time stamp to search")
    psr.add_argument("--end_time", type=int, default=0,
                     help="First time stamp to search")
    psr.add_argument("--coilcnt", type=int, default=1,
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

    if args.coilnum:
        if args.end_time:
            t1 = args.end_time
        else:
            t1 = 1622505599000

        for coilnum in range(args.coilnum, args.coilnum + args.coilcnt):
            found, attime = find_coil_num_time(coilnum, t0, t1, vb=vb)

            if found:
                if vb >= 1:
                    print (f"Found {coilnum} at {attime}.")
                if vb >= 3:
                    print_coil_number_window(attime, attime+1000)
                coil_start, coil_end = find_coil_num_range(coilnum, attime,
                                                           qw=100000, vb=vb)
                print (f"Found {coilnum}: {coil_start} - {coil_end}.")
            else:
                print (f"Did not find {coilnum}.")

        print_epilogue(startTime, verbose = vb)

    else:
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
