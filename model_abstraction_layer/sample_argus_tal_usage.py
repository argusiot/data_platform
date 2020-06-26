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

def log_in_out(func):
  def decorated_func(*args, **kwargs):
    print("Starting %s -----------------" % func.__name__)
    result = func(*args, **kwargs)
    print("Done %s -----------------\n\n" % func.__name__)
    return result
  return decorated_func

@log_in_out
def example_query_for_1_timeseries():
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

  print("Number of timeseries retrieved -- %d" % len(result_list))
  for result in result_list:
    print("Retrieved timeseries id : %s" % \
           str(result.get_timeseries_id()))
    print("Datapoints:")
    for kk, vv in result:
      print("\t%s->%d" % (kk, vv))


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
def example_peek_poke_single_timeseries_result():
  print("Coming soon ...")
  pass

@log_in_out
def example_iterating_over_a_slice_using_result_from_other_ts():
  print("Coming soon ...")
  pass

def main():
  example_query_for_1_timeseries()
  example_query_for_all_timeseries()
  example_peek_poke_single_timeseries_result()
  example_iterating_over_a_slice_using_result_from_other_ts()

if __name__ == "__main__":
  # execute only if run as a script
  main()
