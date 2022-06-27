from cgi import test
import json
import os
import sys
<<<<<<< HEAD
sys.path.append("..")
=======
sys.path.append("../../..")
>>>>>>> 03c59c5 (made it_main.py into a full demo script)
import argus_quilt
import importlib.resources as pkg_resources
import test_data_generator
from grafana_dashboard_generator import AppliqueDashboard
from argus_quilt.state_set_processor_builder import StateSetProcessorBuilder


def main():
    test_data_generator.main()

    with pkg_resources.path( \
            "argus_quilt", "SCHEMA_DEFN_state_set.json") as schema_file:
        builder = StateSetProcessorBuilder(schema_file, "localhost", 4242)
        __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                        os.path.dirname(__file__)))
        with open(os.path.join(__location__, "sample_input.json")) as file:
            state_set_json_schema = json.load(file)
        processor = builder.build(state_set_json_schema)
        processor.one_shot(1616083200, 1616083360, 30)
    
    adash = AppliqueDashboard("sample_input.json")
    adash.upload_to_grafana("2021-03-18T15:59:45.000Z", "2021-03-18T16:03:00.000Z", "localhost:3000")



main()
