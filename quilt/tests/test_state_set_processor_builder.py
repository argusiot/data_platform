'''
    test_set_processor_builder.py

    Test cases for SetProcessorBuilder class
'''
import sys
import os
import json

# FIXME: We're cheating a little here until we've sorted out how to 
# package applique_infra (i.e. inside argus_tal or separately outside).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../applique_infra')))
from state_set_processor_builder import StateSetProcessorBuilder

import unittest
from unittest import mock

class SetProcessorBuilder_Tests(unittest.TestCase):
  '''Unit tests for SetProcessorBuilder.'''
  def __init__(self, *args, **kwargs):
      super(SetProcessorBuilder_Tests, self).__init__(*args, **kwargs)

      # o_u_t = Object_Under_Test
      self.__o_u_t = StateSetProcessorBuilder("/home/vagrant/data_platform/quilt/applique_infra/SCHEMA_DEFN_state_set.json", "http://ignore")

      self.__test_json_data = None
      with open("/home/vagrant/data_platform/quilt/tests/test_data/applique_infra_state_set_testdata.json", 'r') as test_data_f:
          self.__test_data = json.load(test_data_f)

  def testSimpleTest(self):
      self.__o_u_t.validate_request(self.__test_data["minimum_state_set_defn"])
