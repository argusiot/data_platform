import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from state_set_processor_builder import StateSetProcessorBuilder

def main():

    builder = StateSetProcessorBuilder("SCHEMA_DEFN_state_set.json", "http://34.221.154.248:4242/api/put")
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(__location__, "sample_input.json")) as file:
        state_set_json_schema = json.load(file)
    processor = builder.build(state_set_json_schema)
    processor.one_shot(1616083200, 1616083360, 30)


main()
