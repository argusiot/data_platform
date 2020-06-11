'''
  Helper module for unit tests.
'''

from .context import argus_tal
from argus_tal import query_api as qq
from argus_tal import timestamp as ts

def get_dummy_query_params():
  return "172.1.1.1", "4242", "some_metric", {"filer1":"value1"}, \
          qq.QueryQualifier.DATA_VALUE, ts.Timestamp('10'), ts.Timestamp('20')

