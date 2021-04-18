'''
    This Spread Sheet contains the design cases(1-11) for the Stepify unit tests
    https://docs.google.com/spreadsheets/d/1qenFE7QDa_4zUordDWembJJ6BMWZWDXJv_fveTm5y2s/edit#gid=0

    The test data is read from a resource file "test_data/quilt_core_testdata.json" which is shared with
    test_all_filter_primitive.py. All HTTP calls are hence mocked and data is in-turn retrieved
    from the json file.

    The unit testing of Stepify assumes the following:
        (a) Functionality of Filter Primitive in the expected way.
        (b) TimeSeries Object maintains the existing properties.
        (c) test_data/quilt_core_testdata.json file remains unmodified.

    For better understanding of the Cases 1-11, the below spreadsheet allows one to visualize the transition points:
    https://docs.google.com/spreadsheets/d/1x6eHR1LJ0XNgvyD3ytPKDwvZ9SkCTQMldJeSJHi52qo/edit#gid=2140809767
'''

import os
import sys
import unittest
from collections import OrderedDict
from json import loads
from unittest.mock import Mock, patch

from .context import argus_quilt
from argus_quilt.filter_primitive import FilteredTimeseries, FilterQualifier
from argus_quilt.stepify import Stepify
from argus_tal import timeseries_id as ts_id
from argus_tal import query_api
from argus_tal import basic_types as bt
from argus_tal import timestamp as ts
from argus_tal import query_urlgen as qurlgen


def getTimeSeriesData(timeseries_id, start_timestamp, end_timestamp):
    foo = query_api.QueryApi(
        "172.0.0.1", 4242,
        start_timestamp, end_timestamp,
        [timeseries_id],
        bt.Aggregator.NONE,
        False,
    )

    rv = foo.populate_ts_data()
    assert rv == 0

    result_list = foo.get_result_set()
    assert len(result_list) == 1

    return result_list[0]


class Stepify_Tests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(Stepify_Tests, self).__init__(*args, **kwargs)
        self.__test_timeseries_ts_id = ts_id.TimeseriesID("machine.sensor.dummy_melt_temperature",
                                                          {"machine_name": "90mm_extruder"})
        self.__tsdb_ip = "172.0.0.1"
        self.__tsdb_port = 4242

        '''
        The following __test_result_dict is organized in this manner:
        "Query URL" -> "Timeseries result"
        The query URL is constructed based on (timeseries_id, start_time & end_time) being used for a test case.
        '''
        self.__test_result_dict = {}

    def __setup_testcase_data(self, start,
                              end,
                              server_ip,
                              server_port,
                              ts_id_obj):

        # Step 1:
        this_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(this_dir, 'test_data/quilt_core_testdata.json')
        with open(file_path, 'r') as dataFile:
            data = dataFile.read()
        raw_dict = loads(data, object_pairs_hook=OrderedDict)

        timeseries_raw_dict = OrderedDict()
        for k, v in raw_dict.items():
            if start <= int(k) <= end:
                timeseries_raw_dict.update({k: v})
            elif int(k) > end:
                break

        # Step 2:
        start_ts, end_ts = ts.Timestamp(start), ts.Timestamp(end)
        url_to_expect = qurlgen.url(
            bt.Tsdb.OPENTSDB, server_ip, server_port,
            start_ts, end_ts,
            bt.Aggregator.NONE, [ts_id_obj])

        self.__store_expected_result(url_to_expect, 200, ts_id_obj, timeseries_raw_dict)

    def __build_opentsdb_json_response(self, ts_id, timeseries_dict):
        json_response = [
            {
                "aggregateTags": [],
                "dps": {
                    # Fill in data from timeseries_dict.
                    k: v for k, v in timeseries_dict.items()
                },
                # Fill in metric name from ts_id.
                "metric": ts_id.metric_id,

                # Fill in tag value pairs from the filters in ts_id.
                "tags": {
                    k: v for k, v in ts_id.filters.items()
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

    def mocked_requests_get(self, url):
        resp_mock = Mock()
        resp_mock.status_code, resp_mock.json.return_value = self.__test_result_dict[url]
        return resp_mock

    def mock_stepify_helper(self, t1, t2):
        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                t1, t2,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(t1)
            end_timestamp = ts.Timestamp(t2)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)
            return Stepify(filtered_result)

    def testStepifyInit(self):
        stepified_result = self.mock_stepify_helper(1587949200, 1587949214)
        self.assertEqual(len(stepified_result.get_stepified_time_windows().get_time_windows()), 3)
        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587949200.1666667, 1587949201.8333333))
        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[1],
                         (1587949202.1666667, 1587949207.8333333))
        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[2],
                         (1587949210.1666667, 1587949214))

    def testStepifyCase1(self):
        stepified_result = self.mock_stepify_helper(1587947408, 1587948205)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587947408, 1587948205))

    def testStepifyCase2(self):
        stepified_result = self.mock_stepify_helper(1587948690, 1587949197)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587948691.2067041, 1587949197))

    def testStepifyCase3(self):
        stepified_result = self.mock_stepify_helper(1587947403, 1587948211)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587947408, 1587948205.458427))

    def testStepifyCase4(self):
        stepified_result = self.mock_stepify_helper(1587948690, 1587949200)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587948691.2067041, 1587949199.5683453))

    def testStepifyCase5(self):
        stepified_result = self.mock_stepify_helper(1587949214, 1587949217)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587949214, 1587949214.8333333))
        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[1],
                         (1587949216.1666667, 1587949217))

    def testStepifyCase6(self):
        stepified_result = self.mock_stepify_helper(1587949200, 1587949203)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587949200.1666667, 1587949201.8333333))
        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[1],
                         (1587949202.1666667, 1587949203))

    def testStepifyCase7(self):
        stepified_result = self.mock_stepify_helper(1587947408, 1587949197)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587947408, 1587948205.458427))
        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[1],
                         (1587948691.2067041, 1587949197))

    def testStepifyCase8(self):
        stepified_result = self.mock_stepify_helper(1587949205, 1587949210)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587949205, 1587949207.8333333))

    def testStepifyCase9(self):
        stepified_result = self.mock_stepify_helper(1587949208, 1587949214)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587949210.1666667, 1587949214))

    def testStepifyCase10(self):
        stepified_result = self.mock_stepify_helper(1587948211, 1587948690)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows(), [])

    def testStepifyCase11(self):
        stepified_result = self.mock_stepify_helper(1587947403, 1587948690)

        self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
                         (1587947408, 1587948205.458427))
