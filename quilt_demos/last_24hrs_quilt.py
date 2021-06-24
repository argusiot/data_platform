# This file runs every 2pm SGT by cronjob to generate a daily Quilt chart.

import json
import os
import sys
import time
import datetime

import argus_quilt
import importlib.resources as pkg_resources

from argus_quilt.state_set_processor_builder import StateSetProcessorBuilder


def generate_quilt(quilt_run_description, state_spec_filepath):
    now = datetime.datetime.now()
    start_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    log_str_prefix = "%s [%s]" % (start_time_str, quilt_run_description)
    print ("%s: run started for %s" % (log_str_prefix, state_spec_filepath))


    try:
        with pkg_resources.path( \
                "argus_quilt", "SCHEMA_DEFN_state_set.json") as schema_file:
            builder = StateSetProcessorBuilder(schema_file, "localhost", 4242)
            with open(state_spec_filepath) as file:
                state_set_json_schema = json.load(file)
            processor = builder.build(state_set_json_schema)

            computation_window_in_sec = 86399
            end = int(time.time())
            start = end - computation_window_in_sec
            processor.one_shot(start, end, computation_window_in_sec)
    except:
        print("%s: run failed" % log_str_prefix)
        print("%s: Unexpected error:\n%s" % (log_str_prefix, sys.exc_info()[0]))
    else:
        print("%s: run success" % log_str_prefix)

def main():
    generate_quilt("3 state quilt", "/home/ubuntu/quilt/quilt_test_state_v1_definition.json")
    generate_quilt("4 state quilt", "/home/ubuntu/quilt/extruder_states.json")

if __name__ == '__main__':
    main()
