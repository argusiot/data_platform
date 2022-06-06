#!/usr/bin/python3
'''
  Usage:
    python3 http_post_using_json_simple_script.py

  On Grafana:
    http://34.221.154.248:3000/d/l3XTzKZMk/test_metric-dashboard?orgId=1
'''

import requests
import json
import time
from random import randint
from time import sleep

def push_data():
  url = 'http://localhost:4242/api/put'
  headers = {'content-type': 'application/json'}
  datapoint = {}
  datapoint['metric'] = 'test_metric'
  datapoint['timestamp'] = round(time.time())  # timestamp
  datapoint['value'] = randint(3300, 3600)  # value
  datapoint['tags'] = {}
  datapoint['tags']['machine_id'] = 'cold_draw'
  response = requests.post(url, data=json.dumps(datapoint), headers=headers)
  return response, datapoint['timestamp']


data_point_count = 100

while(data_point_count > 0):
  response, data_time_stamp = push_data()
  print("%d Data point pushed. Result %s" % (data_time_stamp, str(response)))
  sleep(randint(1,5))
  data_point_count = data_point_count - 1

