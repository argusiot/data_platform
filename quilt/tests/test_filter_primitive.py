'''
    Test cases for filter primitive
    Spread Sheet containing the design cases.
    https://docs.google.com/spreadsheets/d/1qenFE7QDa_4zUordDWembJJ6BMWZWDXJv_fveTm5y2s/edit#gid=0

    The following test data patterns corresponds to the "Case X" from the design spreadsheet.

    <Case 1>
    "1587947408": 149.4,
    "1587947414": 147.2,
    "1587948199": 148.6,
    "1587948205": 106.8,

    <Case 2>
    "1587948690": 96.4,
    "1587948696": 114.3,
    "1587948702": 147.8,
    "1587948708": 159.7,
    "1587948714": 157.9,
    "1587949173": 158.7,
    "1587949179": 158.2,
    "1587949185": 158.2,
    "1587949191": 157.8,
    "1587949197": 159.5

    <Case 3>
    "1587947408": 149.4,
    "1587947414": 147.2,
    "1587947420": 149.5,
    "1587948193": 147.2,
    "1587948199": 148.6,
    "1587948205": 106.8,
    "1587948211": 17.8

    <Case 4>
    "1587948690": 96.4,
    "1587948696": 114.3,
    "1587948702": 147.8,
    "1587949185": 158.2,
    "1587949191": 157.8,
    "1587949197": 159.5,
    "1587949200": 90

    <Case 5>
    "1587949214": 150,
    "1587949215": 90,
    "1587949216": 90,
    "1587949217": 150

    <Case 6>
    "1587949200": 90,
    "1587949201": 150,
    "1587949202": 90,
    "1587949203": 150

    <Case 7>
    "1587947408": 149.4,
    "1587947414": 147.2,
    "1587948199": 148.6,
    "1587948205": 106.8,
    "1587948211": 17.8,
    "1587948217": 17.9,
    "1587948678": 56.5,
    "1587948684": 76.0,
    "1587948690": 96.4,
    "1587948696": 114.3,
    "1587948702": 147.8,
    "1587949179": 158.2,
    "1587949185": 158.2,
    "1587949191": 157.8,
    "1587949197": 159.5

    <Case 8> Corner case of Case <Case 11>
    "1587949205": 150,
    "1587949206": 150,
    "1587949207": 150,
    "1587949208": 90,
    "1587949209": 90,
    "1587949210": 90

    <Case 9>
    "1587949208": 90,
    "1587949209": 90,
    "1587949210": 90,
    "1587949211": 150,
    "1587949212": 150,
    "1587949213": 150,
    "1587949214": 150

    <Case 10>
    "1587948211": 17.8,
    "1587948217": 17.9,
    "1587948223": 16.9,
    "1587948667": 16.8,
    "1587948673": 23.7,
    "1587948678": 56.5,
    "1587948684": 76.0,

    <Case 11> similar to <Case 8>
    "1587947408": 149.4,
    "1587947414": 147.2,
    "1587947420": 149.5,
    "1587948193": 147.2,
    "1587948199": 148.6,
    "1587948205": 106.8,
    "1587948211": 17.8,
    "1587948217": 17.9,
    "1587948223": 16.9,
    "1587948667": 16.8,
    "1587948673": 23.7,
    "1587948678": 56.5,
    "1587948684": 76.0,
    "1587948690": 96.4

'''

import os
import sys
from collections import OrderedDict
from json import loads

from .context import argus_quilt
from argus_quilt.filter_primitive import FilteredTimeseries, FilterQualifier, filtering_criterion_ops
from argus_tal import timeseries_id as ts_id
from argus_tal import query_api
from argus_tal import basic_types as bt
from argus_tal import timestamp as ts
from argus_tal import query_urlgen as qurlgen

import unittest
from unittest.mock import Mock, patch


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


class FilterPrimitive_Tests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FilterPrimitive_Tests, self).__init__(*args, **kwargs)
        self.__test_timeseries_ts_id = ts_id.TimeseriesID("machine.sensor.dummy_melt_temperature",
                                                          {"machine_name": "90mm_extruder"})
        self.__tsdb_ip = "172.0.0.1"
        self.__tsdb_port = 4242

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

    def mock_filter_series_helper(self, t1, t2):
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
            return filtered_result

    def mock_filter_series_helper_temp(self, t1, t2):
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
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.EQUALS, 17.9)
            return filtered_result

    def testFilterCriterion(self):
        filter_criterion_func = filtering_criterion_ops[FilterQualifier.LESSERTHAN]
        self.assertTrue(filter_criterion_func(99, 100))
        self.assertFalse(filter_criterion_func(101, 100))
        self.assertFalse(filter_criterion_func(100, 100))

        filter_criterion_func = filtering_criterion_ops[FilterQualifier.LESSERTHAN_EQUAL]
        self.assertTrue(filter_criterion_func(99, 100))
        self.assertFalse(filter_criterion_func(101, 100))
        self.assertTrue(filter_criterion_func(100, 100))

        filter_criterion_func = filtering_criterion_ops[FilterQualifier.GREATERTHAN]
        self.assertTrue(filter_criterion_func(101, 100))
        self.assertFalse(filter_criterion_func(99, 100))
        self.assertFalse(filter_criterion_func(100, 100))

        filter_criterion_func = filtering_criterion_ops[FilterQualifier.GREATERTHAN_EQUAL]
        self.assertTrue(filter_criterion_func(101, 100))
        self.assertFalse(filter_criterion_func(99, 100))
        self.assertTrue(filter_criterion_func(100, 100))

        filter_criterion_func = filtering_criterion_ops[FilterQualifier.EQUALS]
        self.assertFalse(filter_criterion_func(101, 100))
        self.assertFalse(filter_criterion_func(99, 100))
        self.assertTrue(filter_criterion_func(100, 100))

    def testMarkerInit(self):
        marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 8090, 100)
        self.assertEqual(marker.get_marker_key(), 8090)
        self.assertEqual(marker.get_marker_value(), 100)
        self.assertEqual(marker.get_marker_type(), FilteredTimeseries.MarkerTypes.INIT)
        self.assertEqual(marker.get_next_element(), None)
        self.assertEqual(marker.get_prev_element(), None)
        marker.set_next_element(150)
        self.assertEqual(marker.get_next_element(), 150)
        marker.set_prev_element(200)
        self.assertEqual(marker.get_prev_element(), 200)

    def testFilteredDataDictInit(self):
        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                1587947403, 1587949197,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(1587947403)
            end_timestamp = ts.Timestamp(1587949197)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)
            self.assertEqual(filtered_result.get_timeseries_data_dict(), test_timeseries)
            self.assertEqual(filtered_result.get_tsid(), self.__test_timeseries_ts_id)

            for key, value in filtered_result.get_filtered_dict().items():
                if not isinstance(value, FilteredTimeseries.Marker):
                    self.assertGreater(value, 100)

    def testAllElementsQualifying_ExpectSuccess(self):
        # Uses Case 1 dataset
        filtered_result = self.mock_filter_series_helper(1587947408, 1587948205)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587947407, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587948206, 106.8)

        mock_first_marker.set_next_element(149.4)
        mock_end_marker.set_prev_element(106.8)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(first_marker)

        self.assertEqual(first_marker.get_marker_type(), mock_first_marker.get_marker_type())
        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(first_marker.get_next_element(), mock_first_marker.get_next_element())
        self.assertEqual(end_marker.get_prev_element(), mock_end_marker.get_prev_element())
        self.assertEqual(end_marker.get_marker_type(), mock_end_marker.get_marker_type())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testInitDisqualifyAndExitQualifyingMarker(self):
        # Uses Case 2 dataset
        filtered_result = self.mock_filter_series_helper(1587948690, 1587949197)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587948690, 96.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949198, 159.5)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(first_marker)

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testInitQualifyAndExitDisqualifyingMarker(self):
        # Uses Case 3 dataset
        filtered_result = self.mock_filter_series_helper(1587947403, 1587948211)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587947407, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587948211, 17.8)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(first_marker)

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testInitAndExitDisqualifyingMarker(self):
        # Uses Case 4 dataset
        filtered_result = self.mock_filter_series_helper(1587948690, 1587949200)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587948690, 96.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949200, 90)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(first_marker)

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testAdjacentNormalMarker(self):
        # Uses Case 5 dataset
        filtered_result = self.mock_filter_series_helper(1587949214, 1587949217)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587949213, 150)
        mock_adjacent_marker1 = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.NORMAL, 1587949215, 90)
        mock_adjacent_marker2 = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.NORMAL, 1587949216, 90)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949218, 150)

        first_marker = filtered_result.get_first_marker()
        adjacent_marker1 = filtered_result.get_next_marker(first_marker)
        adjacent_marker2 = filtered_result.get_next_marker(adjacent_marker1)
        end_marker = filtered_result.get_next_marker(adjacent_marker2)

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())
        self.assertEqual(adjacent_marker1.get_marker_key(), mock_adjacent_marker1.get_marker_key())
        self.assertEqual(adjacent_marker2.get_marker_key(), mock_adjacent_marker2.get_marker_key())

        self.assertEqual(first_marker.get_marker_value(), mock_first_marker.get_marker_value())
        self.assertEqual(adjacent_marker1.get_marker_value(), mock_adjacent_marker1.get_marker_value())
        self.assertEqual(adjacent_marker2.get_marker_value(), mock_adjacent_marker2.get_marker_value())

    def testSawToothPattern(self):
        # Uses Case 6 dataset
        filtered_result = self.mock_filter_series_helper(1587949200, 1587949203)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587949200, 90)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949204, 150)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testInitExitQualifyingAndNormalMarker_ExpectSuccess(self):
        # Uses Case 7 dataset
        filtered_result = self.mock_filter_series_helper(1587947403, 1587949197)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587947407, 149.4)
        mock_next_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.NORMAL, 1587948211, 17.8)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949198, 159.5)

        mock_first_marker.set_next_element(149.4)
        mock_end_marker.set_prev_element(159.5)

        first_marker = filtered_result.get_first_marker()
        next_marker = filtered_result.get_next_marker(first_marker)
        end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(next_marker))

        self.assertEqual(first_marker.get_marker_type(), mock_first_marker.get_marker_type())
        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(next_marker.get_marker_type(), mock_next_marker.get_marker_type())
        self.assertEqual(next_marker.get_marker_key(), mock_next_marker.get_marker_key())
        self.assertEqual(first_marker.get_next_element(), mock_first_marker.get_next_element())
        self.assertEqual(end_marker.get_prev_element(), mock_end_marker.get_prev_element())

    def testExitContinuousMarker(self):
        # Uses Case 8 dataset
        filtered_result = self.mock_filter_series_helper(1587949205, 1587949210)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587949204, 150)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949210, 90)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testInitContinuousMarker(self):
        # Uses Case 9 dataset
        filtered_result = self.mock_filter_series_helper(1587949208, 1587949214)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587949208, 90)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949215, 150)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())
        self.assertEqual(None, filtered_result.get_next_marker(end_marker))

    def testNoQualifyingEntriesInDataSet(self):
        # Uses Case 10 dataset
        filtered_result = self.mock_filter_series_helper(1587948211, 1587948690)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587948211, 17.8)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587948690, 96.4)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(first_marker)

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testExitContinuousCompressionMarker(self):
        # Uses Case 11 dataset
        filtered_result = self.mock_filter_series_helper(1587947403, 1587948690)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587947407, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587948690, 96.4)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def test_is_value_filtered_out(self):
        filtered_result = self.mock_filter_series_helper(1587947403, 1587948690)
        self.assertTrue(filtered_result.is_value_filtered_out(110))
        self.assertFalse(filtered_result.is_value_filtered_out(90))

    def testSingleElement(self):
        with self.assertRaises(ValueError) as context:
            self.mock_filter_series_helper(1587948206, 1587948213)

            self.assertTrue('Single datapoint present system error' in str(context.exception))

    def testDoubleElement(self):
        # Uses Case 1 dataset
        filtered_result = self.mock_filter_series_helper_temp(1587948206, 1587948218)
