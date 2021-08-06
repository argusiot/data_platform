'''
   The applique main file used for the Quilt trial run for Cliffs steel data.
'''
import json
import os
import sys

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
                "steel_poc_plate_thickness_states.json")) as file:
            state_set_json_schema = json.load(file)
        processor = builder.build(state_set_json_schema)

        # Start: Saturday, February 13, 2021 7:01:01 AM GMT
        # End:   Saturday, February 13, 2021 8:01:00 AM GMT
        # start = 1613199661
        # end = 1613203260
        start = 1613199661
        end = 1613203260
        computation_window_in_sec = 30
        processor.one_shot(start, end, computation_window_in_sec)


if __name__ == '__main__':
    main()
