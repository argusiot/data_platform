ubuntu@ip-172-31-45-219:~/quilt/appliques$ cat last_24hrs_quilt_msec.py 
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

def main():
    generate_quilt("Coarse state quilt", "/home/ubuntu/quilt/appliques/extruder_states_coarse_msec.json")

if __name__ == '__main__':
    main()
