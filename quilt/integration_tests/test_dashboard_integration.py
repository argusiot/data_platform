from cgi import test
import json
import os
import sys
sys.path.append("..")
sys.path.append("../../..")
import importlib.resources as pkg_resources
from test_data import test_data_generator
from grafana_dashboard_generator import AppliqueDashboard
from argus_quilt.state_set_processor_builder import StateSetProcessorBuilder


def main():
    test_data_generator.main()

    with pkg_resources.path( \
            "argus_quilt", "SCHEMA_DEFN_state_set.json") as schema_file:
        builder = StateSetProcessorBuilder(schema_file, "localhost", 4242)
        __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                        os.path.dirname(__file__)))
        with open(os.path.join(__location__, "test_appliques/test_applique_1.json")) as file:
            state_set_json_schema = json.load(file)
        processor = builder.build(state_set_json_schema)
        processor.one_shot(1616083200, 1616083360, 30)
    
    adash = AppliqueDashboard("test_appliques/test_applique_1.json")
    adash.upload_to_grafana("2021-03-18T15:59:45.000Z", "2021-03-18T16:03:00.000Z", "localhost:3000")

main()