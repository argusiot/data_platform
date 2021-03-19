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
from argus_tal.timeseries_id import TimeseriesID

import unittest
from unittest import mock

class SetProcessorBuilder_Tests(unittest.TestCase):
  '''Unit tests for SetProcessorBuilder.'''
  def __init__(self, *args, **kwargs):
      super(SetProcessorBuilder_Tests, self).__init__(*args, **kwargs)

      this_dir = os.path.dirname(os.path.realpath(__file__))
      schema_file_path = os.path.join( \
          this_dir, '../applique_infra/SCHEMA_DEFN_state_set.json')

      # o_u_t = Object_Under_Test
      self.__o_u_t = StateSetProcessorBuilder(schema_file_path, "http://ignore")

      test_data_file = os.path.join(
          this_dir, "test_data/applique_infra_state_set_testdata.json")

      with open(test_data_file, 'r') as dataFile:
          self.__test_data = json.load(dataFile)

  def testValidateOnly(self):
      self.__o_u_t.validate_request(self.__test_data["minimum_state_set_defn"])

  def testValidateSSP_Construction_IsCorrectForTrivialStateDefn(self):
      # ssp -> StateSetProcessor
      ssp = self.__o_u_t.build(self.__test_data["1_series_2_state_set_defn"])

      ss_req_json = self.__test_data["1_series_2_state_set_defn"]

      # Build a TSID object from the JSON request data
      expected_tsid_obj = TimeseriesID( \
          ss_req_json["input_timeseries"][0]["ts_defn"]["metric"],
          ss_req_json["input_timeseries"][0]["ts_defn"]["tags"])

      '''
      We're now going to walk though StateSetProcessor and verify that each
      element contained in it is correct.
      StateSetProcessor
           |
           |=> TemporaState obj list
                    |
                    | (each TemporalState object)
                    |
                    |=> output TSID (i.e. TSID to write to)
                    |=> Expression list
                           |
                           |  (each Expression)
                           |
                           |=> List of statements
                                   |
                                   |  (each statement)
                                   |=> TimeseriesID, operator, filter_const
      '''

      self.assertEqual(ssp.name, ss_req_json["name"])
      state_defns = ssp._get_temporal_obj_list()
      self.assertEqual(2, len(state_defns))

      # Lets cache the output/write timeseries template constituents for
      # ease of use below.
      output_ts_template = ss_req_json["output_timeseries_template"]
      output_metric_id, output_tags = (output_ts_template["metric"], \
                                       output_ts_template["tags"])

      # Verify "state1" by unpacking the expression for the 1st state in the
      # input JSON and verifying its constituents.
      self.assertEqual(state_defns[0].state_label, \
                       ss_req_json["state_definitions"][0]["label"])
      expr_list = state_defns[0]._get_expression_list() # Retrieve expr list
      self.assertEqual(1, len(expr_list))  # Verify count of stmts in expr
      ts_id_obj, operator, filter_val = expr_list[0]  # Unpack 1st stmt
      self.assertEqual(ts_id_obj, expected_tsid_obj)
      self.assertEqual(operator, ">")
      self.assertEqual(filter_val, 100)
      write_tsid = state_defns[0].write_tsid  # Now verify output ts_id parts.
      self.assertEqual(write_tsid.metric_id, output_metric_id)
      self.assertEqual(write_tsid.filters["machine"], output_tags["machine"])
      self.assertEqual(write_tsid.filters["state_label"],
                       state_defns[0].state_label) # Verify PLACEHOLDER fix-up

      # Verify "opposite_of_state1" by unpacking the expression for the 2nd
      # in the input JSON and verifying its constituents.
      self.assertEqual(state_defns[1].state_label,
                       ss_req_json["state_definitions"][1]["label"])
      expr_list = state_defns[1]._get_expression_list() # Retrieve expr list
      self.assertEqual(1, len(expr_list))  # Verify count of stmts in expr
      ts_id_obj, operator, filter_val = expr_list[0]  # Unpack 1st stmt
      self.assertEqual(ts_id_obj, expected_tsid_obj)
      self.assertEqual(operator, "<=")
      self.assertEqual(filter_val, 100)
      write_tsid = state_defns[1].write_tsid  # Now verify output ts_id parts.
      self.assertEqual(write_tsid.metric_id, output_metric_id)
      self.assertEqual(write_tsid.filters["machine"], output_tags["machine"])
      self.assertEqual(write_tsid.filters["state_label"],
                       state_defns[1].state_label) # Verify PLACEHOLDER fix-up

