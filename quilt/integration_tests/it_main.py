import json
import os
import sys

import argus_quilt
import importlib.resources as pkg_resources

from argus_quilt.state_set_processor_builder import StateSetProcessorBuilder


def main():

    with pkg_resources.path( \
            "argus_quilt", "SCHEMA_DEFN_state_set.json") as schema_file:
        builder = StateSetProcessorBuilder( \
            schema_file, "http://34.221.154.248:4242/api/put")
        __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                        os.path.dirname(__file__)))
        with open(os.path.join(__location__, "sample_input.json")) as file:
            state_set_json_schema = json.load(file)
        processor = builder.build(state_set_json_schema)
        processor.one_shot(1616083200, 1616083360, 30)


main()
