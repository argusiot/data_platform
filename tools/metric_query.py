'''
  Simple tool to print results of a query URL.
  Example:
      To run:
        ./print-tool.py "http://34.221.154.248:4242/api/query?start=1587947400&end=1587949200&m=none:machine.sensor.melt_temperature:machine.sensor.screw_speed"
      (note: The URL needs to be embedded to inside double quotes (") for
             the command to work).
       
'''

import urllib2
import json
from collections import OrderedDict
import sys

def get_data_set(url):
  contents = urllib2.urlopen(url).read()
  data = json.loads(contents)
  dpsData= data[0]['dps']
  data_set = {}
  for timestamp, value in dpsData.items():
    data_set[int(timestamp)] = value
  return data_set

def main():
  data_set = get_data_set(sys.argv[1:][0])
  for tt, vv in data_set.iteritems():
    print(tt,vv)
  

if __name__ == "__main__":
  main()
