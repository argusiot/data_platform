#!/usr/bin/python3
'''
  sample_argus_tal_usage.py.

  This file contains a handful of argus_tal API usage examples. Its organized
  as just a sequence of methods that demonstrate API usage with increasing
  levels of complexity/sophistication.

  To get a quick idea of what each example does, just jump to main() and
  look at the function names, they are fairly self descriptive !
'''

from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
from argus_tal import query_urlgen as qurlgen
from argus_tal import timeseries_datadict as tsd
from argus_tal.timeseries_datadict import LookupQualifier as LQ

def log_in_out(func):
  def decorated_func(*args, **kwargs):
    print("Starting %s -----------------" % func.__name__)
    result = func(*args, **kwargs)
    print("Done %s -----------------\n\n" % func.__name__)
    return result
  return decorated_func

@log_in_out
def example_query_for_1_timeseries(get_result_silently=True):
  # We specify the metric name (machine.sensor.raw_melt_temperature) and
  # 1 filter to be able to disambiguate this timeseries from other timeseries
  # (with the same metric).
  #
  # With this we expect to get 1 result back.
  timeseries_id = ts_id.TimeseriesID("machine.sensor.raw_melt_temperature", \
                                     {"machine_name":"90mm_extruder"})

  start_timestamp = ts.Timestamp(1593043062)
  end_timestamp = ts.Timestamp(1593043117)

  # Observe that timeseries_id is supplied as a list because can query multiple
  # timeseries at the same time (for the same time window).
  foo = query_api.QueryApi(
          "34.221.154.248", 4242, \
          start_timestamp, end_timestamp, \
          [timeseries_id], \
          bt.Aggregator.NONE \
        )

  rv = foo.populate_ts_data()
  assert rv == 0

  # The outcome of populate_ts_data() is available as a list of
  # Timeseries_DataDict objects. Lets get these out.
  result_list = foo.get_result_set()
  assert len(result_list) == 1  # We expect to get exactly 1 timeseries back !

  # Returns results before we start printing anyting to the console.
  if get_result_silently:
    return result_list, start_timestamp, end_timestamp

  print("Number of timeseries retrieved -- %d" % len(result_list))
  for result in result_list:
    print("Retrieved timeseries id : %s" % str(result.get_timeseries_id()))
    print("Datapoints:")
    for kk, vv in result:
      print("\t%s->%d" % (kk, vv))

  return result_list, start_timestamp, end_timestamp


@log_in_out
def example_query_for_all_timeseries():
  # We specify the metric name and an empty filer map. This tells the API to
  # retrieve *all* the timeseries associated with this metric and return them
  # in the result list.
  timeseries_id = ts_id.TimeseriesID("machine.sensor.raw_melt_temperature", {})

  start_timestamp = ts.Timestamp(1593043062)
  end_timestamp = ts.Timestamp(1593043117)

  foo = query_api.QueryApi(
          "34.221.154.248", 4242, \
          start_timestamp, end_timestamp, \
          [timeseries_id], \
          bt.Aggregator.NONE \
        )

  rv = foo.populate_ts_data()
  assert rv == 0

  # The outcome of populate_ts_data() is available as a list of
  # Timeseries_DataDict objects. Lets get these out.
  result_list = foo.get_result_set()
  assert len(result_list) == 2  # We expect to 2 timeseries back !

  print("Number of timeseries retrieved -- %d" % len(result_list))
  for result in result_list:
    print("Retrieved timeseries id : %s" % \
           str(result.get_timeseries_id()))
    print("Datapoints:")
    for kk, vv in result:
      print("\t%s->%d" % (kk, vv))


@log_in_out
def example_explore_result_object_api_aka_TimeseriesDataDict_api():
  '''
    Prior examples iterated over all the data points from the returned
    result. This example now focuses on exploring the TimeseriesDataDict API
    by doing some more peeking/poking at the result set.
  '''

  # To avoid duplicating boilerplate code (for query construction etc.), we
  # re-run example1 and just get the result_list containing exactly 1
  # timeseries DataDict. In addition we also get the start and end timestamps
  # that were supplied for the query.
  result_list, q_start_ts, q_end_ts = example_query_for_1_timeseries(True)
  assert len(result_list) == 1  # We expect to 2 timeseries back !

  ts_dd = result_list[0]


  # Using -- get_min_key() & get_max_key()
  #
  # Now lets learn how to get the start and end timestamps from the result set.
  r_start_ts = ts_dd.get_min_key()
  r_end_ts = ts_dd.get_max_key()

  print("Visual timestamp comparison -- query:(%d,%d)\tresult:(%d,%d)" %
        (q_start_ts.value, q_end_ts.value, r_start_ts, r_end_ts))

  # Obviously the r_*_ts values should be within the [q_start_ts, q_end_ts]
  # range. Agreed ? Lets verify that !
  assert q_start_ts.value <= r_start_ts
  assert q_end_ts.value >= r_end_ts

  # From the visual inspection of timestamps you will notice that in this case,
  # the result time window falls strictly inside the query time window:
  #     query:(1593043062,1593043117)
  #     result:(1593043069,1593043110)
  # This may not always be the case, but here its true. So we can make the
  # following assertions.
  assert q_start_ts.value < r_start_ts
  assert q_end_ts.value > r_end_ts


  # Using -- get_datapoint()
  #
  # Now lets learn to get a specific data point back using get_datapoint() API.
  # This is also time to understand how the lookup qualifier is to be used.

  # We expect to get a legit value when r_start_ts is supplied with EXACT_MATCH
  # because we know the timestamp exists in the result set, however if we supply
  # q_start_t (i.e. the original timestamp) with EXACT_MATCH we get a value of
  # None !
  ts1, val1 = ts_dd.get_datapoint(r_start_ts, LQ.EXACT_MATCH)
  ts2, val2 = ts_dd.get_datapoint(q_start_ts.value, LQ.EXACT_MATCH)
  assert ts1 == r_start_ts and val1 != None
  assert ts2 == q_start_ts.value and val2 == None

  # Using -- LookupQualifier.NEAREST_LARGER
  #
  # Since we know that the query timestamp is smaller than the result timestamp,
  # lets change the lookup qualifier to get a legit result back.
  ts3, val3 = ts_dd.get_datapoint(q_start_ts.value, LQ.NEAREST_LARGER)
  assert (ts3, val3) == (ts1, val1) # The above result matches result for
                                    # r_start_ts. Makes sense, right ?

  # Using -- LookupQualifier.NEAREST_SMALLER
  #
  # To start with lets compare query results with r_end_ts and q_end_ts.
  ts4, val4 = ts_dd.get_datapoint(r_end_ts, LQ.EXACT_MATCH)
  ts5, val5 = ts_dd.get_datapoint(q_end_ts.value, LQ.EXACT_MATCH)
  assert ts4 == r_end_ts and val4 != None   # Expect legit value.
  assert ts5 == q_end_ts.value and val5 == None  # value is None. Makes sense ?

  ts6, val6 = ts_dd.get_datapoint(q_end_ts.value, LQ.NEAREST_SMALLER)
  assert (ts4, val4) == (ts6, val6) # The above result matches result for


  # Using -- LookupQualifier.NEAREST_SMALER_WEAK
  #
  # Lets first understand the need for the above 2 and then see how they work.
  #
  # Q: What happens if you query with a timestamp that is outside the bounds of
  #    the result set?
  # A: It will fail and you will get value back as None.
  #
  # Sometimes its useful to never get that failure i.e. always get a legit
  # result back. The lookup below is going to fail because 1000 is smaller than
  # the smallest timestamp in the result datadict.
  ts7, val7 = ts_dd.get_datapoint(1000,    # Lookup with non-existent timestamp.
                                  LQ.NEAREST_SMALLER)
  assert ts7 == 1000 and val7 == None

  # ...lets change NEAREST_SMALLER to make that requirement weaker as shown
  # below. What we're telling get_datapoint() is that if the supplied key is
  # smaller than mininum key in the datadict, then return the minimum key even
  # if the key is larger than the supplied key (thus a "weak"er requirement
  # to look for NEAREST_SMALLER).
  ts8, val8 = ts_dd.get_datapoint(1000, LQ.NEAREST_SMALLER_WEAK)
  assert (ts8, val8) == (r_start_ts, val1)

  # Using -- LookupQualifier.NEAREST_LARGER_WEAK
  #
  # This is the complement of NEAREST_SMALLER_WEAK. We'll just show the code
  # below without explanation !
  ts9, val9 = ts_dd.get_datapoint(q_end_ts.value*2,   # Timestamp out of bound.
                                  LQ.NEAREST_LARGER)
  assert ts9 == q_end_ts.value*2 and val9 == None

  ts10, val10 = ts_dd.get_datapoint(q_end_ts.value*2, LQ.NEAREST_LARGER_WEAK)
  assert (ts10, val10) == (ts4, val4)


@log_in_out
def example_iterating_over_a_slice_using_result_from_other_ts():
  print("Coming soon ...")
  pass


def main():
  example_query_for_1_timeseries()
  example_query_for_all_timeseries()
  example_explore_result_object_api_aka_TimeseriesDataDict_api()
  example_iterating_over_a_slice_using_result_from_other_ts()

if __name__ == "__main__":
  # execute only if run as a script
  main()
