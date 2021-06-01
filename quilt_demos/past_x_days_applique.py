from datetime import datetime
import calendar
import json
import os
import sys
import time

import argus_quilt
import importlib.resources as pkg_resources

from argus_quilt.state_set_processor_builder import StateSetProcessorBuilder


def main():

    with pkg_resources.path( \
            "argus_quilt", "SCHEMA_DEFN_state_set.json") as schema_file:
        builder = StateSetProcessorBuilder(schema_file, "localhost", 4242)
        __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                        os.path.dirname(__file__)))
        with open(os.path.join(__location__, \
                  "quilt_test_state_v1_definition.json")) as file:
            state_set_json_schema = json.load(file)
        processor = builder.build(state_set_json_schema)

        '''
            SGT:
            ("2021-05-31 00:00:00", "2021-05-31 23:59:59"),
            ("2021-05-30 00:00:00", "2021-05-30 23:59:59"),
            ("2021-05-29 00:00:00", "2021-05-29 23:59:59"),
            ("2021-05-28 00:00:00", "2021-05-28 23:59:59"),
            ("2021-05-27 00:00:00", "2021-05-27 23:59:59"),
            ("2021-05-26 00:00:00", "2021-05-26 23:59:59"),

            UTC:
            ("2021-05-30 16:00:00", "2021-05-31 15:59:59"),
            ("2021-05-29 16:00:00", "2021-05-30 15:59:59"),
            ("2021-05-28 16:00:00", "2021-05-29 15:59:59"),
            ("2021-05-27 16:00:00", "2021-05-28 15:59:59"),
            ("2021-05-26 16:00:00", "2021-05-27 15:59:59"),
            ("2021-05-25 16:00:00", "2021-05-26 15:59:59"),
        '''
        format = "%Y-%m-%d %H:%M:%S"
        time_windows = [
            ("2021-05-31 16:00:00", "2021-06-01 15:59:59"),
            ("2021-05-30 16:00:00", "2021-05-31 15:59:59"),
            ("2021-05-29 16:00:00", "2021-05-30 15:59:59"),
            ("2021-05-28 16:00:00", "2021-05-29 15:59:59"),
            ("2021-05-27 16:00:00", "2021-05-28 15:59:59"),
            ("2021-05-26 16:00:00", "2021-05-27 15:59:59"),
            ("2021-05-25 16:00:00", "2021-05-26 15:59:59"),
        ]
        computation_granularity_in_sec = 86399
        for t_win in time_windows:
            start_utc, end_utc = t_win
            print("Starting processing for %s to %s" % (start_utc, end_utc))
            start = calendar.timegm(
                        datetime.strptime(start_utc, format).timetuple())
            end = calendar.timegm(
                      datetime.strptime(end_utc, format).timetuple())
            print("Window: %s %s" % (str(start), str(end)))
            foo = processor.one_shot(start, end, computation_granularity_in_sec)



if __name__ == '__main__':
    main()

