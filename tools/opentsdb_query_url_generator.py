#!/usr/bin/python3
'''
  Simple tool to generate query URLs that can be used on the command line.

  Example:
      To generate query URL:
        ./opentsdb_query_url_generator.py 65mm_extruder 5m-ago 1m-ago

        ./opentsdb_query_url_generator.py 90mm_extruder 5m-ago 1m-ago

        ./opentsdb_query_url_generator.py \"*\" 5m-ago 1m-ago

      To directly embed URL into curl based query:
      curl "`./opentsdb_query_url_generator.py 65mm_extruder 5m-ago 1m-ago`"
      (note: The URL needs to be embedded to inside double quotes (") for
             the command to work).
       

'''

import argparse
import sys


parser = argparse.ArgumentParser(description="OpenTSDB query URL generator")
parser.add_argument("machine_name", \
                    help="Machine name.")
parser.add_argument("start_time", \
                    help="Start time for query.")
parser.add_argument("end_time", \
                    help="End time for query.")
parser.add_argument("--h", \
                    help="Simple too to generate the OpenTSBD query URL.")
args = parser.parse_args()

metric_prefix="machine.sensor"

metric_list = ["raw_melt_temperature", "raw_melt_pressure", \
               "raw_screw_speed", "raw_line_speed", \
               "raw_barrel_temperature_1", "raw_barrel_temperature_2", \
               "raw_machine_powerOn_state", "raw_wire_output_diameter"]

query_str="http://34.221.154.248:4242/api/query?start=%s&end=%s" % \
         (args.start_time, args.end_time)

for metric in metric_list:
  query_str="%s&m=sum:%s.%s\{machine_name=%s\}" % (query_str, metric_prefix, \
                                                   metric, args.machine_name)

print(query_str)
