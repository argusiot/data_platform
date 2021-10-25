#!/usr/bin/python3
'''
  coil_number_query.py

  Skeletal tool should how to query by coil number, analyse the results and
  then do more fun stuff...
'''

from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
from argus_tal import query_urlgen as qurlgen
from argus_tal import timeseries_datadict as tsd
from argus_tal.timeseries_datadict import LookupQualifier as LQ

def print_query_result(timeseries_id, start_time, end_time, flag_compute_rate=False):
  start_timestamp = ts.Timestamp(start_time)
  end_timestamp = ts.Timestamp(end_time)

  # Observe that timeseries_id is supplied as a list because can query multiple
  # timeseries at the same time (for the same time window).
  foo = query_api.QueryApi(
          "34.221.154.248", 4242,  # CHANGE HERE: Use your IP addr
          start_timestamp, end_timestamp,
          [timeseries_id],
          bt.Aggregator.NONE,
          flag_compute_rate,   # Controls whether this a rate vs regular query.
          flag_ms_response=True
        )

  rv = foo.populate_ts_data()
  assert rv == 0

  # The outcome of populate_ts_data() is available as a list of
  # Timeseries_DataDict objects. Lets get these out.
  result_list = foo.get_result_set()
  # assert len(result_list) == 1  # We expect to get exactly 1 timeseries back !

  print("Rate query: %s" % str(flag_compute_rate))
  print("Number of timeseries retrieved -- %d" % len(result_list))
  for result in result_list:
    print("Retrieved timeseries id : %s" % str(result.get_timeseries_id()))
    print("Datapoints:")
    for kk, vv in result:
      print("\t%s->%d" % (kk, vv))

def generate_coil_number_time_windows(start_time, end_time):
  # CHANGE HERE: Use coil_number metric & tags
  timeseries_id = ts_id.TimeseriesID("machine.sensor.raw_melt_temperature",
                                     {"machine_name":"90mm_extruder"})

  print_query_result(timeseries_id, start_time, end_time, flag_compute_rate=False)
  print_query_result(timeseries_id, start_time, end_time, flag_compute_rate=True)

  return


def main():
  # CHANGE HERE: supply start time, end time e.g.
  # generate_coil_number_time_windows(1593043069,1593043200)
  generate_coil_number_time_windows(1593043069,1593043200)

  '''
  Will be needed when you have to query interesting signals for the start and end
  timestamp associated with a coil number.

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
