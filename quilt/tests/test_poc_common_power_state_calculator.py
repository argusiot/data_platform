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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../poc')))
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
    self.__tsdb_ip = "172.1.1.1"
    self.__tsdb_port = 4242
    # Initialize the timeseries id of interest
    self.__power_state_ts_id = ts_id.TimeseriesID(
      "machine.sensor.dummy_machine_powerOn_stat",
      {"machine_name": "90mm_extruder"}
    )

    self.__fixed_period_test_data = [
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


  def __update_time_spent_in_state(self, value_dict, key, value):
    # Update cummulative value.
    updated_value = value_dict.get(key, 0) + value
    value_dict[key] = int(updated_value)

  def __generate_timeseries(self, time_window_and_value_list,
                                  period_mean,
                                  period_stddev):
    '''Generates a timeseries for the supplied time window list.

       time_window_and_value_list is of the form:
          [(start_w1, end_w1, value), (start_w2, end_w2, value), ...]

       Each datapoint has the same 'value'.

       The period dictates distance between data points. Its normally distributed
       with the period_mean and period_stddev. By supplying a value of 0 for
       the stddev caller can generate *exactly* equidistant datapoints.

       The timestamps for the data points are generated using the start window
       time and period mean/std_dev values and are guaranteed to not exceed the
       end time window.

       Caller can get fixed period by supplying 0 for std-dev.

       Return:
         timeseries:
           A map containing time->value.

         cumm_duration_in_this_state:
           Stores the cummulative durations associated with each of the
           values that were supplied in the timeseries generation parameters.
           e.g. Over the entire time duration value 0.0 was seen for 60sec
           and 1.0 was seen for 90sec. This is used for verification of results
           returned by machine analytics.

        first_timestamp:
            This is the timestamp of the first datapoint in the generated
            timeseries.

        last_timestamp:
            This is the timestamp of the last datapoint in the generated
            timeseries.
     '''
    timeseries = {}  # Stores the generated timeseries data.
    cumm_duration_in_this_state = {}  # to store cummulative values written

    # Initialize variables that allow us to chain successive time windows.
    # FIXME: Explain how these are getting used.
    last_ts_in_prev_timeseries = None
    for vv in time_window_and_value_list:
      start_time, end_time, dp_value = vv  # Unpack the test data params.

      # From the 2nd time window onwards, the start_time gets overridden
      # with the last_ts_in_prev_timeseries (time window chaining).
      if last_ts_in_prev_timeseries != None:
        start_time = last_ts_in_prev_timeseries

      # Initialize housekeep variables
      timestamp = start_time
      next_ts_distance = 0

      '''Its crucial to understand how next_ts_distance is used here.

         FIXME: Add how next_ts_distance computed in one iteration affects
                computation in the next iteration.
      '''
      while timestamp + next_ts_distance <= end_time:
        timestamp += next_ts_distance  # Update timestamp and...
        timeseries[timestamp] = dp_value # ... add datapoint into timeseries.

        # Generate (temporal) distance for next datapoint.
        next_ts_distance = int(random.gauss(period_mean, period_stddev))

      last_ts_in_prev_timeseries = timestamp

      # Update cummulative duration spent in 'dp_value' state.
      duration = last_ts_in_prev_timeseries - start_time
      updated_value = cumm_duration_in_this_state.get(dp_value, 0) + duration
      cumm_duration_in_this_state[dp_value] = int(updated_value)


    # Lets pull out the first timestamp in the timeseries. This will be the
    # start time of the first window in the window and value list.
    first_window = time_window_and_value_list[0]
    start_time, end_time, state = first_window

    return timeseries, cumm_duration_in_this_state, start_time, last_ts_in_prev_timeseries

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
                                  server_ip,
                                  server_port,
                                  ts_id_obj):
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
    cummulative_time_in_each_state, \
    first_timestamp, \
    last_timestamp = self.__generate_timeseries(
                 time_window_params,
                 period_mean,
                 period_std_dev)

    # Step 2:
    start_ts, end_ts = ts.Timestamp(first_timestamp), ts.Timestamp(last_timestamp)
    url_to_expect = qurlgen.url(
       bt.Tsdb.OPENTSDB, server_ip, server_port,
       start_ts, end_ts,
       bt.Aggregator.NONE, [ts_id_obj])

    self.__store_expected_result(url_to_expect, 200, ts_id_obj,  timeseries)
    return start_ts, end_ts, cummulative_time_in_each_state

  def __verify_power_state_obj_results(self, power_state_calc_obj,
                                             time_window_params,
                                             total_expected_duration,
                                             test_case_label,
                                             computed_result,
                                             cumm_state_from_generated_ts_data,
                                             strict_verification=True):
    '''Verify the PowerStateCalculator object results with expected data.

       If strict_verification is True, then both generated state transition
       time windows and the computed cummulative time spent in each state are
       verified.

       If strict_verification is False, then only the computed cummulative time
       spent in each state are verified. Verification of transition windows is
       skipped.
    '''
    # 1) Verify computed state tranistion time windows
    # Verify that the state transition list computed exactly matches our
    # time windows from the test data.
    if strict_verification:
      self.assertEqual(power_state_calc_obj.state_transition_list,
                       time_window_params,
                       msg=test_case_label)

    # 2) Audit computed result for time spent in each state.
    # Verify that in the computed result, the time spent in ON and OFF
    # states equals total time window.
    self.assertEqual(computed_result['off_state'] + computed_result['on_state'],
                     total_expected_duration)

    # 3) Verify that cummulative duration spent each state.
    # More precisely, verify that expected values for time spent in
    # ON/OFF states matches that with our generated data.
    self.assertEqual(cumm_state_from_generated_ts_data.get(1.0, 0),
                     computed_result['on_state'])
    self.assertEqual(cumm_state_from_generated_ts_data.get(0.0, 0),
                     computed_result['off_state'])

  def mocked_requests_get(self, url):
    print("GENERATED URL: %s" % url)
    resp_mock = Mock()
    resp_mock.status_code, resp_mock.json.return_value = self.__test_result_dict[url]
    return resp_mock

  def testAllSubtestCasesForFixedPeriod(self):
    '''Test Power state calcuation for fixed period test data.

       In the test method we generate timeseries with a fixed period between
       the data points.
    '''

    # tc = test_case
    for tc_idx, tc_data in enumerate(self.__fixed_period_test_data):
      test_case_label, time_window_params = tc_data # Unpack test case data
      print("\nTesting: %s" % test_case_label)
      with self.subTest():
        with patch('argus_tal.query_api.requests') as mock_tsdb:

          # Setup mock handler
          mock_tsdb.get.side_effect = self.mocked_requests_get

          # Setup test case data that PowerStateCalculator consumes.
          start_ts, end_ts, \
          cumm_state_from_generated_ts_data = self.__setup_testcase_data(
              time_window_params,
              self.__period_mean,
              0, # Std dev = 0 i.e. fixed distance between data points.
              self.__tsdb_ip,
              self.__tsdb_port,
              self.__power_state_ts_id)

          # Instantiate Object Under Test and invoke the functionality being
          # tested.
          power_state_calc_obj = PowerStateCalculator(
              self.__tsdb_ip,
              self.__tsdb_port,
              ComputationMode.ON_DEMAND,
              self.__power_state_ts_id)
          computed_result = power_state_calc_obj.compute_result(start_ts,
                                                                end_ts)

          mock_tsdb.get.assert_called_once()

          # Verify that PowerStateCalculator object matches expected results
          # by comparing against generated timeseries data.
          self.__verify_power_state_obj_results(
              power_state_calc_obj,
              time_window_params,
              end_ts.value - start_ts.value,  # total duration
              test_case_label,
              computed_result,
              cumm_state_from_generated_ts_data)


  def testAllSubtestCasesForVariablePeriod(self):
    '''Test Power state calcuation for fixed period test data.

       In the test method we generate timeseries with a fixed period between
       the data points.
    '''

    start = 1239000
    window = 50
    time_windows = [
        (start, start+window, 0.0),
        (-1, start+2*window, 1.0),
        (-1, start+3*window, 0.0),
        (-1, start+10*window, 1.0),
        (-1, start+11*window, 0.0),
    ]
    variable_period_test_data = [
        ("Variable period window *** FIX TIME WINDOW AUDITING",
          time_windows)
    ]

    # tc = test_case
    for tc_idx, tc_data in enumerate(variable_period_test_data):
      test_case_label, time_window_params = tc_data # Unpack test case data
      print("\nTesting: %s" % test_case_label)
      with self.subTest():
        with patch('argus_tal.query_api.requests') as mock_tsdb:

          # Setup mock handler
          mock_tsdb.get.side_effect = self.mocked_requests_get

          # Setup test case data that PowerStateCalculator consumes.
          start_ts, end_ts, \
          cumm_state_from_generated_ts_data = self.__setup_testcase_data(
              time_window_params,
              self.__period_mean,
              self.__period_std_dev,
              self.__tsdb_ip,
              self.__tsdb_port,
              self.__power_state_ts_id)

          # Instantiate Object Under Test and invoke the functionality being
          # tested.
          power_state_calc_obj = PowerStateCalculator(
              self.__tsdb_ip,
              self.__tsdb_port,
              ComputationMode.ON_DEMAND,
              self.__power_state_ts_id)
          computed_result = power_state_calc_obj.compute_result(start_ts,
                                                                end_ts)

          mock_tsdb.get.assert_called_once()

          # Verify that PowerStateCalculator object matches expected results
          # by comparing against generated timeseries data.
          self.__verify_power_state_obj_results(
              power_state_calc_obj,
              time_window_params,
              end_ts.value - start_ts.value,  # total duration
              test_case_label,
              computed_result,
              cumm_state_from_generated_ts_data,
              strict_verification=False)

  def testVariableTimePeriod2(self):
    start = 1239000
    window = 50
    time_windows = [
        (start, start+window, 1.0),
        (-1, start+2*window, 0.0),
        (-1, start+3*window, 1.0),
    ]

    timeseries_dps, \
    time_in_each_state, \
    _, \
    _ = self.__generate_timeseries(time_windows,
                                   self.__period_mean,
                                   self.__period_std_dev)
    print(timeseries_dps)
    print(time_in_each_state)
