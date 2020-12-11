#!/usr/bin/python3
from builtins import print

from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
from argus_tal import timeseries_datadict as tsdd
from argus_tal.timeseries_datadict import LookupQualifier as LQ
import operator


ops = {
    "<":  operator.lt,
    "<=": operator.le,
    ">":  operator.gt,
    ">=": operator.gt,
    "==": operator.eq
}

def getTimeSeriesData(timeseries_id, start_timestamp, end_timestamp, flag_compute_rate=False):
    foo = query_api.QueryApi(
        "34.221.154.248", 4242,
        start_timestamp, end_timestamp,
        [timeseries_id],
        bt.Aggregator.NONE,
        flag_compute_rate,
    )

    rv = foo.populate_ts_data()
    assert rv == 0

    result_list = foo.get_result_set()
    assert len(result_list) == 1

    # for result in result_list:
    #     for kk, vv in result:
    #         print("\t%s->%d" % (kk, vv))
    return result_list[0]

def filterTS(input_ts, operator, constant):
    datapoints_dict = {}
    timeseries_id = ts_id.TimeseriesID("filtered.dummy_melt_temperature",
                                       {"machine_name": "90mm_extruder"})
    op_func = ops[operator]
    for k, v in input_ts:
        if op_func(v,constant):
            datapoints_dict.update({k: v})
        elif op_func
    result = tsdd.TimeseriesDataDict(timeseries_id, datapoints_dict)
    return result






def main():
    timeseries_id = ts_id.TimeseriesID("machine.sensor.dummy_melt_temperature",
                                       {"machine_name": "90mm_extruder"})
    # Primary start and end time stamps, should be provided by the caller.
    start_timestamp = ts.Timestamp(1587947403)
    end_timestamp = ts.Timestamp(1587949197)

    result = getTimeSeriesData(timeseries_id, start_timestamp, end_timestamp)

    filtered_ts = filterTS(result, ">", 100)



# if __name__ == "__main__":
#   # execute only if run as a script
main()

# import operator
# ops = {
#     "+": operator.add,
#     "-": operator.sub,
#     "*": operator.mul,
#     "/": operator.div
# }
# op_char = input('enter a operand')
# op_func = ops[op_char]
# result = op_func(a, b)