'''
  Helper module for unit tests.
'''

from .context import argus_tal
from argus_tal import query_api as qq
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
import random

def get_dummy_query_params():
  return "172.1.1.1", 4242, "some_metric", {"filter1":"value1"}, \
          bt.Aggregator.NONE, ts.Timestamp('1234510'), ts.Timestamp('1234570')

def get_dummy_query_params_for_ms_response():
  return "172.1.1.1", 4242, "some_metric", {"filter1":"value1"}, \
         bt.Aggregator.NONE, \
         ts.Timestamp('1628043432000'), ts.Timestamp('1628043482000')

def get_query_params_for_maxsize_64bits():
  return "172.1.1.1", 4242, "some_metric", {"filter1":"value1"}, \
         bt.Aggregator.NONE, \
         ts.Timestamp('9223372036854775800'), \
         ts.Timestamp('9223372036854775807')

def get_url_for_dummy_query_params():
  return "http://172.1.1.1:4242/api/query?start=1234510&end=1234570" \
      "&m=none:some_metric{filter1=value1}" \

def get_url_for_dummy_query_params_with_rate():
  return "http://172.1.1.1:4242/api/query?start=1234510&end=1234570" \
      "&m=none:rate:some_metric{filter1=value1}" \

def get_url_for_truncated_json_response():
  return "http://172.1.1.1:4242/api/query?start=1234510&end=1234570" \
      "&m=none:truncated_json_metric{filter1=value1}" \

def get_url_for_dummy_query_params_with_ms_response():
  return "http://172.1.1.1:4242/api/query?" \
         "start=1628043432000&end=1628043482000&ms=true" \
         "&m=none:some_metric{filter1=value1}" \

def get_url_for_query_params_with_maxsize_64bits():
  return "http://172.1.1.1:4242/api/query?" \
         "start=9223372036854775800&end=9223372036854775807&ms=true" \
         "&m=none:some_metric{filter1=value1}" \

def get_truncated_json_response():
  # Problems:
  #  1) Typo with aggregateTags
  #  2) missing metric field
  return [{ \
            "aggreTags": [], \
            "dps": { \
              "1234510": 10, \
              "1234560": 60, \
              "1234570": 70, \
              "1234530": 30, \
              "1234520": 20, \
              "1234550": 50, \
              "1234540": 40, \
            }, \
            "tags": { \
                "filter1": "value1" \
            } \
        }]

def get_good_json_response():
  return [{ \
            "aggregateTags": [], \
            "dps": { \
              "1234510": 10, \
              "1234560": 60, \
              "1234570": 70, \
              "1234530": 30, \
              "1234520": 20, \
              "1234550": 50, \
              "1234540": 40, \
            }, \
            "metric": "some_metric", \
            "tags": { \
                "filter1": "value1" \
            } \
        }]

def get_good_json_response_for_rate():
  # The rate math below is just slope of 2 points (ts1, val1) and (ts2, val2).
  # Rate = (val2 - val1) / (ts2 - ts1)
  # Since all points are 10s apart and values are 10sec apart, the slope is 1
  # for all cases except for the first point.
  return [{ \
            "aggregateTags": [], \
            "dps": { \
              "1234510": 0, \
              "1234560": 1, \
              "1234570": 1, \
              "1234530": 1, \
              "1234520": 1, \
              "1234550": 1, \
              "1234540": 1, \
            }, \
            "metric": "some_metric", \
            "tags": { \
                "filter1": "value1" \
            } \
        }]

def __generate_test_dict(key_as_string, use_rate_dps=False):
  tmp_dict = None
  if use_rate_dps:
    tmp_dict = get_UNsorted_RATE_datapoints()
  else:
    tmp_dict = get_UNsorted_datapoints()
  keys = sorted(tmp_dict.keys())
  new_dict = {}
  for kk in keys:
    new_key = kk
    if key_as_string:
      new_key = str(kk)
    new_dict[new_key] = tmp_dict[kk]
  return new_dict

# From Python 3.6 onwards, a dictionary maintains order of insertion i.e.
# if keys are inserted in sorted order then sorted order is maintained.
# This is not true prior to Python 3.6. So take these method names with a grain
# of salt.
def get_sorted_datapoints():
  return __generate_test_dict(key_as_string=False)

def get_distance():
  return 10  # the distance between the keys and values in the test datapoints.

def get_sorted_datapoints_for_rate():
  return __generate_test_dict(key_as_string=False, use_rate_dps=True)

def get_datapoint_slice(start_idx, end_idx):
  test_dps = get_UNsorted_datapoints()
  key_list = list(sorted(test_dps.keys()))
  requested_slice = key_list[start_idx:end_idx]
  slice_of_dps = {}
  for key in requested_slice:
    slice_of_dps[key] = test_dps[key]
  return slice_of_dps

def get_UNsorted_datapoints():
  return {1234510: 10, \
          1234560: 60, \
          1234570: 70, \
          1234530: 30, \
          1234520: 20, \
          1234550: 50, \
          1234540: 40, \
         }

def get_UNsorted_RATE_datapoints():
  return {1234510: 0, \
          1234560: 1, \
          1234570: 1, \
          1234530: 1, \
          1234520: 1, \
          1234550: 1, \
          1234540: 1, \
         }

def get_good_msec_json_response():
  return [{ \
            "aggregateTags": [], \
            "dps": { \
              "1628043432000": 10, \
              "1628043440000": 60, \
              "1628043448000": 70, \
              "1628043457000": 30, \
              "1628043465000": 20, \
              "1628043473000": 50, \
              "1628043482000": 40, \
            }, \
            "metric": "some_metric", \
            "tags": { \
                "filter1": "value1" \
            } \
        }]

def get_sorted_datapoints_for_ms_response():
    return {
              1628043432000: 10, \
              1628043440000: 60, \
              1628043448000: 70, \
              1628043457000: 30, \
              1628043465000: 20, \
              1628043473000: 50, \
              1628043482000: 40, \
           }

'''
Insipration for this test case & test data:
Python 3.7.5 (default, Feb 23 2021, 13:22:40)
[GCC 8.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import sys
>>> sys.max
sys.maxsize     sys.maxunicode
>>> sys.maxsize
9223372036854775807

'''
def get_json_response_for_maxsize_on_64bit():
  return [{ \
            "aggregateTags": [], \
            "dps": { \
              "9223372036854775800": 10, \
              "9223372036854775801": 60, \
              "9223372036854775807": 70, \
            }, \
            "metric": "some_metric", \
            "tags": { \
                "filter1": "value1" \
            } \
        }]

def get_datapoints_for_maxsize_on_64bit():
    return {
              9223372036854775800: 10, \
              9223372036854775801: 60, \
              9223372036854775807: 70, \
           }


def get_string_datapoints():
  return __generate_test_dict(key_as_string=False)

def get_smallest_key_and_its_value():
  sorted_test_data = get_sorted_datapoints()
  first_key = min(sorted_test_data.keys())
  return first_key, sorted_test_data[first_key]

def get_largest_key_and_its_value():
  sorted_test_data = get_sorted_datapoints()
  last_key = max(sorted_test_data.keys())
  return last_key, sorted_test_data[last_key]

def get_arbit_key_and_value():
  sorted_test_data = get_sorted_datapoints()
  arb_k_idx = 3
  key_list = list(sorted_test_data.keys())
  return (key_list[arb_k_idx-1], sorted_test_data[key_list[arb_k_idx-1]]), \
         (key_list[arb_k_idx], sorted_test_data[key_list[arb_k_idx]]), \
         (key_list[arb_k_idx+1], sorted_test_data[key_list[arb_k_idx+1]])
