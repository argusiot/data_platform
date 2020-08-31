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
   [1.0 = ON, 0.0 = OFF]         [start, end]
   ============================================================================
   Fixed period tests:
   -------------------
   Following tests have datapoints at a fixed period of 1 dp every 10sec.


   Continuous power ON        W1: 1234510 - 1234570       1.0       60

   Continuous power OFF       W2: 1234610 - 1234670       0.0       60

   OFF->ON transition         W3: 1234800 - 1234850       0.0       50
                                  1234850 - 1234900       1.0       40

   ON->OFF transition         W4: 1234900 - 1234950       1.0       50
                                  1234950 - 1234990       0.0       40

   OFF->ON->OFF               W5: 1235000 - 1235030       0.0       30
                                  1235030 - 1235060       1.0       30
                                  1235060 - 1235090       0.0       30
                                  Total - OFF/ON: 60/30

   ON->OFF->ON                W5: 1235100 - 1235130       1.0       30
                                  1235130 - 1235160       0.0       30
                                  1235160 - 1235190       1.0       30
                                  Total - OFF/ON: 30/60

   Long time windows and
   multi-transitions.
   OFF->ON->OFF->ON->OFF      W6: 1236000 - 1236200       0.0      200
                                  1236200 - 1236400       1.0      200
                                  1236400 - 1236600       0.0      200
                                  1236600 - 1236800       1.0      200
                                  1236800 - 1237000       0.0      200
                                  Total - OFF/ON: 600/400

   ON->OFF->ON->OFF->ON       W7: 1238000 - 1238200       1.0      200
                                  1238200 - 1238400       0.0      200
                                  1238400 - 1238600       1.0      200
                                  1238600 - 1238800       0.0      200
                                  1238800 - 1239000       1.0      200
                                  Total - ON/OFF: 400/600


   Variable period tests:
   ----------------------
   Now we're going to relax the exact 1 dp every 10sec constraint that way the
   the timestamps are not so well aligned.

   Repeat all the above tests for same start time but with data points generated
   using normal distribution with mean = 10 & stddev = 3. The expected values
   now to need to be computed as a well.
'''

import os
import random
import sys

# FIXME: We're cheating a little here until we've sorted out how to
# package machine_analytics (i.e. inside argus_tal or separately outside).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from common_power_state_calculator import PowerStateCalculator
from all_machines_common_base import ComputationMode
from argus_tal import basic_types as bt
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts
from argus_tal import query_urlgen as qurlgen

import unittest
from unittest.mock import Mock, patch

class PSC_Tests(unittest.TestCase):
  '''Unit tests for PowerStateCalculator.'''
  def __init__(self, *args, **kwargs):
    super(PSC_Tests, self).__init__(*args, **kwargs)
    random.seed(1000)  # We're intentionally fixing the seed.
    self.__period_mean = 10  # Why 10 ? So that it aligns timestamps on the
                             # datapoints, which is just convenient for
                             # visual verification of testdata.
    self.__period_std_dev = 3 # Choice of 3 is arbitrary.
    self.__test_data = [
         ("Continuous power ON", [(1234510, 1234570, 1.0)]),
         ("Continuous power OFF", [(1234610, 1234670, 0.0)]),
         ("OFF->ON transition", [(1234800, 1234850, 0.0),
                                 (1234850, 1234890, 1.0)]),
         ("ON->OFF transition", [(1234900, 1234950, 1.0),
                                 (1234950, 1234990, 0.0)]),
          ("OFF->ON->OFF", [(1235000, 1235030, 0.0),
                            (1235030, 1235060, 1.0),
                            (1235060, 1235090, 0.0)]),
         ("ON->OFF->ON", [(1235100, 1235130, 1.0),
                          (1235130, 1235160, 0.0),
                          (1235160, 1235190, 1.0)]),
         ("OFF->ON->OFF->ON->OFF", [(1236000, 1236200, 0.0),
                                    (1236200, 1236400, 1.0),
                                    (1236400, 1236600, 0.0),
                                    (1236600, 1236800, 1.0),
                                    (1236800, 1237000, 0.0)]),
          ("ON->OFF->ON->OFF->ON", [(1238000, 1238200, 1.0),
                                    (1238200, 1238400, 0.0),
                                    (1238400, 1238600, 1.0),
                                    (1238600, 1238800, 0.0),
                                    (1238800, 1239000, 1.0)]),
    ]

    # This stores the URL->result map and is consulted while constructing
    # a response for the test window.
    self.__test_result_dict = { }


  def __update_dict(self, value_dict, key, value):
    # Update cummulative value.
    updated_value = value_dict.get(key, 0) + value
    value_dict[key] = int(updated_value)

  def __generate_timeseries(self, time_window_and_value_list,
                                  period_mean,
                                  period_stddev,
                                  window_chaining = True):
    '''Generates a timeseries for the supplied time window list.

       Each datapoint has the same 'value'.

       The period is a tuple : (mean, std_dev).

       The timestamps for the data points are generated using the start window
       time and period mean/std_dev values and are guaranteed to not exceed the
       end time window.

       Caller can get fixed period by supplying 0 for std-dev.

       Return:
         timeseries:
           A map containing time->value.

         total_time_in_each_state:
           Stores the cummulative durations associated with each of the
           values that were supplied in the timeseries generation parameters.
           e.g. Over the entire time duration value 0.0 was seen for 60sec
           and 1.0 was seen for 90sec. This is used for verification of results
           returned by machine analytics.
     '''
    timeseries = {}  # Stores the generated timeseries data.
    total_time_in_each_state = {}  # to store cummulative values written

    # An house keeping variable to allow to chain time windows wherever needed.
    if window_chaining:
      last_ts_in_prev_timeseries = None

    for vv in time_window_and_value_list:
      start_time, end_time, value = vv  # Unpack the test data params.
      if window_chaining and last_ts_in_prev_timeseries != None:
        start_time = last_ts_in_prev_timeseries

      # Initialize housekeep variables
      timestamp = start_time
      next_ts_distance = 0

      while timestamp + next_ts_distance <= end_time:
        timestamp += next_ts_distance  # Update timestamp and...
        timeseries[timestamp] = value # ... add datapoint into timeseries.

        # Generate (temporal) distance for next datapoint.
        next_ts_distance = int(random.gauss(period_mean, period_stddev))

        # Update cummulative value for current timestamp
        self.__update_dict(total_time_in_each_state, value, next_ts_distance)

      last_ts_in_prev_timeseries = timestamp
      # last_ts_in_prev_timeseries = timestamp + next_ts_distance

    # Lets pull out the first timestamp in the timeseries. This will be the
    # start time of the first window in the window and value list.
    first_window = time_window_and_value_list[0]
    start_time, end_time, state = first_window

    return timeseries, total_time_in_each_state, start_time, last_ts_in_prev_timeseries

  #FIXME: Develop this for the variable period case.
  def __audit_fixed_period_timestamps(self, timeseries, period):
    old_ts = None
    for ts in timeseries:
      if old_ts != None:
        self.assertEqual(ts, old_ts + period)
      old_ts = ts # Update old_ts to current timestamp

  def __build_opentsdb_json_response(self, ts_id, timeseries_dict):
    json_response = [
      {
        "aggregateTags": [],
        "dps": {
          # Fill in data from timeseries_dict.
          k:v for k,v in timeseries_dict.items()
        },
        # Fill in metric name from ts_id.
        "metric": ts_id.metric_id,

        # Fill in tag value pairs from the filters in ts_id.
        "tags": {
          k:v for k,v in ts_id.filters.items()
        }
      }
    ]
    return json_response

  def __store_expected_result(self, url, resp_code, ts_id, timeseries_dict):
    if resp_code == 200:
      json_resp = self.__build_opentsdb_json_response(ts_id, timeseries_dict)
    else:
      json_resp = None
    self.__test_result_dict[url] = (resp_code, json_resp)

  def __setup_testcase_data(self, time_window_params,
                                  period_mean,
                                  period_std_dev,
                                  tsdb_ip,
                                  tsdb_port,
                                  power_state_ts_id):
    '''
      Setup the test case data.

      The PowerStateCalculator object expects to receive a timeseries of the
      machine power state from the TSDB. The timeseries data that comes in
      the response is embedded in a JSON object.

      Different test cases need different timeseries data.

      The URL constructed from the timseries windows+metric name precisely
      identify the JSON response that needs to be sent back.

      So we setup the testcase data in 2 steps.
      Step1: Generate the timeseries that the testcase expects to receive
         based on the time windows and state in time_window_params.
      Step2: Build a JSON object from that and save this generated
         timeseries in __test_result_dict which is consulted by the mock
         method to send a response back.
    '''
    # Step 1:
    timeseries, \
    total_time_in_each_state, \
    first_timestamp, \
    last_timestamp = self.__generate_timeseries(
                 time_window_params,
                 period_mean,
                 period_std_dev)
    self.__audit_fixed_period_timestamps(timeseries, self.__period_mean)

    # Step 2:
    start_ts, end_ts = ts.Timestamp(first_timestamp), ts.Timestamp(last_timestamp)
    url_to_expect = qurlgen.url(
       bt.Tsdb.OPENTSDB, tsdb_ip, tsdb_port,
       start_ts, end_ts,
       bt.Aggregator.NONE, [power_state_ts_id])

    self.__store_expected_result(url_to_expect, 200, power_state_ts_id,  timeseries)
    return start_ts, end_ts

  def mocked_requests_get(self, url):
    print("[TESTING FOR] URL: %s" % url)
    resp_mock = Mock()
    resp_mock.status_code, resp_mock.json.return_value = self.__test_result_dict[url]
    return resp_mock

  def testOffToOnTransition(self):
    '''Test Power state calcuation for test cases in self.__test_data.'''

    tsdb_ip = "172.1.1.1"
    tsdb_port = 4242
    # Initialize the timeseries id of interest
    power_state_ts_id = ts_id.TimeseriesID(
      "machine.sensor.dummy_machine_powerOn_stat",
      {"machine_name": "90mm_extruder"}
    )

    # tc = test_case
    for tc_idx, tc_data in enumerate(self.__test_data):
      test_case_label, time_window_params = tc_data # Unpack test case data
      with self.subTest():
        with patch('argus_tal.query_api.requests') as mock_tsdb:

          # Setup mock handler
          mock_tsdb.get.side_effect = self.mocked_requests_get

          # Setup test case data that PowerStateCalculator consumes.
          start_ts, end_ts = self.__setup_testcase_data(
              time_window_params,
              self.__period_mean,
              0, # Std dev = 0 i.e. fixed distance between data points.
              tsdb_ip,
              tsdb_port,
              power_state_ts_id)

          # Instantiate Object Under Test and invoke the functionality being
          # tested.
          power_state_calc_obj = PowerStateCalculator(
              tsdb_ip, tsdb_port, ComputationMode.ON_DEMAND, power_state_ts_id)
          result = power_state_calc_obj.compute_result(start_ts, end_ts)

          #
          # Verify expected outcomes and side effects.
          #

          mock_tsdb.get.assert_called_once()

          # Verify that the state transition list computed exactly matches our
          # time windows from the test data.
          self.assertEqual(power_state_calc_obj.state_transition_list,
                           time_window_params,
                           msg=test_case_label)

          # Verify that the time spent in ON and OFF states equals total time
          # window.
          self.assertEqual(result['off_state'] + result['on_state'],
                           end_ts.value - start_ts.value)


