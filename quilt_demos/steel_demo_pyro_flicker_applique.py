'''
   The applique main file used for the Quilt demo run for Cliffs steel data.
'''
import json
import os
import sys
import argparse
import argus_quilt
import importlib.resources as pkg_resources

from argus_quilt.state_set_processor_builder import StateSetProcessorBuilder


def main():

    # Default start value is first sample of our first test dat file.
    # Start: Saturday, February 13, 2021 7:01:01 AM GMT
    dflt_start = 1613199661
    dlft_win = 10

    psr = argparse.ArgumentParser(description="ArgusIoT Applique Tool")
    psr.add_argument("--start", type=int, default=dflt_start,
                     help="Epoch time stamp for first point in time series")
    psr.add_argument("--end", type=int, default=(dflt_start + 3600),
                     help="Epoch time stamp for first point in time series")
    psr.add_argument("--win", type=int, default=dflt_win,
                     help=f"Number of samples in quit window {dflt_win}")
    args = psr.parse_args()

    with pkg_resources.path( \
            "argus_quilt", "SCHEMA_DEFN_state_set.json") as schema_file:
        builder = StateSetProcessorBuilder(schema_file, "localhost", 4242)
        __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                        os.path.dirname(__file__)))
        with open(os.path.join(__location__, \
                "steel_demo_pyro_flicker_states.json")) as file:
            state_set_json_schema = json.load(file)
        processor = builder.build(state_set_json_schema)

        start = args.start
        end = args.end
        computation_window_in_sec = args.win
        processor.one_shot(start, end, computation_window_in_sec)


if __name__ == '__main__':
    main()
