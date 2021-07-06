'''
   The applique main file used for the Quilt trial run for Wilson Cables
   Pvt Ltd (Singapore).
'''
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
        builder = StateSetProcessorBuilder(schema_file, "34.221.154.248", 4242)
        __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                                     os.path.dirname(__file__)))
        with open(os.path.join(__location__, \
                               "quilt_test_state_v1_definition.json")) as file:
            state_set_json_schema = json.load(file)
        processor = builder.build(state_set_json_schema)

        computation_window_in_sec = 30
        end = int(time.time())
        start = end - 43200

        # start = 1618502400
        # end = 1618675200

        processor.one_shot(start, end, computation_window_in_sec)


if __name__ == '__main__':
    main()
