#!/usr/bin/python3
'''
   FIXME: Add sections to this sample application to demonstrate various
          features of the argus_tal query API.
'''

from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
from argus_tal import query_urlgen as qurlgen
from argus_tal import timeseries_datadict as tsd

start_timestamp = ts.Timestamp(1593043062)
end_timestamp = ts.Timestamp(1593043117)

timeseries_id = ts_id.TimeseriesID("machine.sensor.raw_melt_temperature", {})

foo = query_api.QueryApi(
        "34.221.154.248", 4242, \
        start_timestamp, end_timestamp, \
        [timeseries_id], \
        bt.Aggregator.NONE \
      )

rv = foo.populate_ts_data()
assert rv == 0

result_list = foo.get_result_set()
print("Number of timeseries retrieved -- %d" % len(result_list))
for result in result_list:
  print("Retrieved timeseries id : %s" % \
         str(result.get_timeseries_id()))
  print("Datapoints:")
  for kk, vv in result:
    print("\t%s->%d" % (kk, vv))
