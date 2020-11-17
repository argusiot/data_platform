
import sys
import os

# FIXME: We're cheating a little here until we've sorted out how to 
# package machine_analytics (i.e. inside argus_tal or separately outside).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from extruder_machine_states_calculator import ExtruderMachineStateCalculator
from all_machines_common_base import ComputationMode
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts

import unittest
from unittest import mock

# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    # FIXME: Fill in different responses for different test URLs.

    return MockResponse([{}], 404)

class ESMC_Tests(unittest.TestCase):
  '''Unit tests for ExtruderMachineStateCalculator.'''

  #############################################################################
  # Next steps
  # 1. Change testUsingRealQueryData_RemoveThisTestSoon to use mock and the
  #    test data in json files from under ADP_DASH_SW5/
  # 2. Add small unit tests for each computation separately (e.g. power state
  #    melt temp stability, etc). That way we can flush out bugs that are
  #    leading to the audit error at the bottom of
  #    testUsingRealTSDBData_REMOVE_THIS
  #############################################################################
  @mock.patch('requests.get', side_effect=mocked_requests_get)
  def testUsingMock(self, mock_get):
    pass

  # NOTE: This does not use mock and make the actual HTTP request.
  def testUsingRealTSDBData_REMOVE_THIS(self):
    power_state_ts_id = ts_id.TimeseriesID(
        "machine.sensor.dummy_machine_powerOn_stat",
        {"machine_name": "90mm_extruder"}
      )
    melt_temp_ts_id = ts_id.TimeseriesID(
        "machine.sensor.dummy_melt_temperature",
        {"machine_name": "90mm_extruder"}
      )
    line_speed_ts_id = ts_id.TimeseriesID(
        "machine.sensor.dummy_line_speed",
        {"machine_name": "90mm_extruder"}
      )
    screw_speed_ts_id = ts_id.TimeseriesID(
        "machine.sensor.dummy_screw_speed",
        {"machine_name": "90mm_extruder"}
      )
    machine_usage = ExtruderMachineStateCalculator(
        "34.221.154.248", 4242, ComputationMode.ON_DEMAND,
        power_state_ts_id, melt_temp_ts_id, line_speed_ts_id, screw_speed_ts_id)

    result = machine_usage.compute_result(ts.Timestamp(1587947403),
                                          ts.Timestamp(1587949197))
    start_time_ts, end_time_ts = result['time_window']
    window_duration = end_time_ts.value - start_time_ts.value
    '''
      FIXME: These numbers are using the original (Vishwas) data as is. It is
      understood that these values fail the following audit:
      2) on_state = ready_state + purge_state
      We'll fix the code later and add suitable MOCK based unit tests in follow
      up commits.
    '''
    # All numbers below are in seconds.
    self.assertEqual(1794, window_duration)
    self.assertEqual(result['off_state'] + result['on_state'], window_duration)
    self.assertEqual(850, result['ready_state'])
    self.assertEqual(18, result['purge_state'])
