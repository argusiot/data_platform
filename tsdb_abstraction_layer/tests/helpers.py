'''
  Helper module for unit tests.
'''

from .context import argus_tal
from argus_tal import query_api as qq
from argus_tal import timestamp as ts

def get_dummy_query_params():
  return "172.1.1.1", "4242", "some_metric", {"filer1":"value1"}, \
          qq.QueryQualifier.DATA_VALUE, ts.Timestamp('10'), ts.Timestamp('20')

# From Python 3.6 onwards, a dictionary maintains order of insertion i.e.
# if keys are inserted in sorted order then sorted order is maintained.
# This is not true prior to Python 3.6. So take these method names with a grain
# of salt.
def get_sorted_datapoints():
  return {1234560: "10", \
          1234561: "20", \
          1234562: "30", \
          1234563: "40", \
          1234564: "50", \
          1234565: "60"  \
         }

def get_UNsorted_datapoints():
  return {1234560: "10", \
          1234565: "60",  \
          1234562: "30", \
          1234561: "20", \
          1234564: "50", \
          1234563: "40"  \
         }

def get_string_datapoints():
  return {"1234560": "10", \
          "1234565": "60",  \
          "1234562": "30", \
          "1234561": "20", \
          "1234564": "50", \
          "1234563": "40"  \
         }
