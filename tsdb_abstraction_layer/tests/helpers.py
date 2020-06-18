'''
  Helper module for unit tests.
'''

from .context import argus_tal
from argus_tal import query_api as qq
from argus_tal import timestamp as ts
import random

def get_dummy_query_params():
  return "172.1.1.1", "4242", "some_metric", {"filer1":"value1"}, \
          qq.QueryQualifier.DATA_VALUE, ts.Timestamp('10'), ts.Timestamp('20')

def __generate_test_dict(key_as_string):
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
  # Generate a random number from the keys such that we exclude both the
  # boundary elements.
  arbit_key_idx = 2 # int(random.uniform(1, len(key_list) - 1))
  key_list = list(sorted_test_data.keys())
  return key_list[arbit_key_idx], \
         sorted_test_data[key_list[arbit_key_idx]]
