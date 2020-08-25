'''
   Power state test cases.

   NOTE: There's an intentional gap between all the time windows below i.e.
         between W1 & W2, between W2 & W3 etc. This gap is essential to ensure
         that test data is isolated from each other. Talk to Parag if you have
         any doubts about this.

   Tests are divided into fixed period and variable period tests. Continue
   reading to understand the difference.

   ============================================================================
   Test                              Time                Power   Expected
   scenario                          window              state   duration (sec)
   [1.0 = ON, 0.0 = OFF]
   ============================================================================
   Fixed period tests:
   -------------------
   Following tests have datapoints at a fixed period of 1 dp every 10sec.


   Continuous power ON        W1: 1234510 - 1234570       1.0       60

   Continuous power OFF       W2: 1234610 - 1234670       0.0       60

   OFF->ON transition         W3: 1234800 - 1234845       0.0       45
                                  1234846 - 1234890       1.0       45

   ON->OFF transition         W4: 1234900 - 1234945       1.0       45
                                  1234946 - 1234990       0.0       45

   OFF->ON->OFF               W5: 1235000 - 1235030       0.0       30
                                  1235031 - 1235060       1.0       30
                                  1235061 - 1235090       0.0       30
                                  Total - OFF/ON: 60/30

   ON->OFF->ON                W5: 1235100 - 1235130       1.0       30
                                  1235131 - 1235160       0.0       30
                                  1235161 - 1235190       1.0       30
                                  Total - OFF/ON: 30/60

   Long time windows and
   multi-transitions.
   OFF->ON->OFF->ON->OFF      W6: 1236000 - 1236199       0.0      200
                                  1236200 - 1236399       1.0      200
                                  1236400 - 1236599       0.0      200
                                  1236600 - 1236799       1.0      200
                                  1236800 - 1236999       0.0      200
                                  Total - OFF/ON: 600/400

   ON->OFF->ON->OFF->ON       W7: 1238000 - 1238199       1.0      200
                                  1238200 - 1238399       0.0      200
                                  1238400 - 1238599       1.0      200
                                  1238600 - 1238799       0.0      200
                                  1238800 - 1238999       1.0      200
                                  Total - ON/OFF: 400/600


   Variable period tests:
   ----------------------
   Now we're going to relax the exact 1 dp every 10sec constraint that way the
   the timestamps are not so well aligned.

   Repeat all the above tests for same start time but with data points generated
   using normal distribution with mean = 10 & stddev = 3. The expected values
   now to need to be computed as a well.
'''

import sys
import os

# FIXME: We're cheating a little here until we've sorted out how to
# package machine_analytics (i.e. inside argus_tal or separately outside).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from common_power_state_calculator import PowerStateCalculator
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

class PSC_Tests(unittest.TestCase):
  '''Unit tests for PowerStateCalculator.'''

  @mock.patch('requests.get', side_effect=mocked_requests_get)
  def testUsingMock(self, mock_get):
    pass

  # NOTE: This does not use mock and make the actual HTTP request.
  def testUsingRealTSDBData_REMOVE_THIS(self):
    power_state_ts_id = ts_id.TimeseriesID(
        "machine.sensor.dummy_machine_powerOn_stat",
        {"machine_name": "90mm_extruder"}
      )
    power_state_calc_obj = PowerStateCalculator(
        "34.221.154.248", 4242, ComputationMode.ON_DEMAND, power_state_ts_id)

    result = power_state_calc_obj.compute_result(
        ts.Timestamp(1587947403), ts.Timestamp(1587949197))
    start_time_ts, end_time_ts = result['time_window']
    window_duration = end_time_ts.value - start_time_ts.value
    # All numbers below are in seconds.
    self.assertEqual(1794, window_duration)
    self.assertEqual(874, result['off_state'])
    self.assertEqual(903, result['on_state'])
