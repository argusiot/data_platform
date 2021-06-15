'''
   The applique main file used for the Quilt trial run for Wilson Cables
   Pvt Ltd (Singapore).
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
        builder = StateSetProcessorBuilder(schema_file, "192.168.1.146", 4242)
        __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                        os.path.dirname(__file__)))
        with open(os.path.join(__location__, \
                  "quilt_test_state_v1_definition_ulfs.json")) as file:
            state_set_json_schema = json.load(file)
        processor = builder.build(state_set_json_schema)

        # Start: Apr 16 00:00:00 SGT -> Apr 15 16:00:00 GMT -> 1618502400
        # End:   Apr 18 00:00:00 SGT -> Apr 17 16:00:00 GMT -> 1618675200
        # start = 1618502400
        # end = 1618675200
        # Trouble at:
        #  - 1618559280  ....skipped by resuming at 1618559310
        #  - 1618645410
        #  - 1618645440  ....skipped by resuming at 1618645470
        start = 1613199661
        end = 1613201460
        computation_window_in_sec = 300
        processor.one_shot(start, end, computation_window_in_sec)


if __name__ == '__main__':
    main()

