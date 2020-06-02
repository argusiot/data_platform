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


contents = urllib2.urlopen(sys.argv[1:][0]).read()
data = json.loads(contents)
dpsData= data[0]['dps']
for key, value in dpsData.iteritems():
    print key, value

