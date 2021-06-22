import json
import os
import sys
import time
import datetime

import argus_quilt
import importlib.resources as pkg_resources

from argus_quilt.state_set_processor_builder import StateSetProcessorBuilder


def main():

    now = datetime.datetime.now()
    start_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    print ("%s: quilt run started" % start_time_str)

    with pkg_resources.path( \
            "argus_quilt", "SCHEMA_DEFN_state_set.json") as schema_file:
        builder = StateSetProcessorBuilder(schema_file, "localhost", 4242)
        with open("/home/ubuntu/quilt/extruder_states.json") as file:
            state_set_json_schema = json.load(file)
        processor = builder.build(state_set_json_schema)

        computation_window_in_sec = 86399
        # end = int(time.time())
        timewindows = [ (1623909600,1623995999), # Tuesday, June 17, 2021 6:00:00 GMT
                        (1623996000,1624082399), # Tuesday, June 18, 2021 6:00:00 GMT
                        (1624082400,1624168799), # Tuesday, June 19, 2021 6:00:00 GMT
                        (1624168800,1624255199), # Tuesday, June 20, 2021 6:00:00 GMT
                        (1624255200,1624341599)] # Tuesday, June 21, 2021 6:00:00 GMT
        for twins in timewindows:
            start, end = twins
            processor.one_shot(start, end, computation_window_in_sec)


if __name__ == '__main__':
    main()


