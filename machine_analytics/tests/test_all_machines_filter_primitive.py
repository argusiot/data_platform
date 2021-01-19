'''
    Test cases for filter primitive
    Spread Sheet containing the design cases.
    https://docs.google.com/spreadsheets/d/1qenFE7QDa_4zUordDWembJJ6BMWZWDXJv_fveTm5y2s/edit#gid=0
'''

import os
import sys
from collections import OrderedDict
from json import loads

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from all_machines_filter_primitive import FilteredTimeseries, FilterQualifier
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
        with open('test_data.json', 'r') as dataFile:
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

    def testInitExitQualifyingAndNormalMarker_ExpectSuccess(self):
        '''
            Case 1 and Case 7
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
        '''
        
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

    def testInitDisqualifyAndExitQualifyingMarker(self):
        '''
            Case 2
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
        '''

        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                1587948690, 1587949197,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(1587948690)
            end_timestamp = ts.Timestamp(1587949197)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

            mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587948690, 96.4)
            mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949198, 159.5)

            first_marker = filtered_result.get_first_marker()
            end_marker = filtered_result.get_next_marker(first_marker)

            self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
            self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testInitQualifyAndExitDisqualifyingMarker(self):
        '''
            Case 3
            "1587947408": 149.4,
            "1587947414": 147.2,
            "1587947420": 149.5,
            "1587948193": 147.2,
            "1587948199": 148.6,
            "1587948205": 106.8,
            "1587948211": 17.8
        '''

        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                1587947403, 1587948211,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(1587947403)
            end_timestamp = ts.Timestamp(1587948211)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

            mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587947407, 149.4)
            mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587948211, 17.8)

            first_marker = filtered_result.get_first_marker()
            end_marker = filtered_result.get_next_marker(first_marker)

            self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
            self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testExitContinuousCompressionMarker(self):
        '''
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

        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                1587947403, 1587948690,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(1587947403)
            end_timestamp = ts.Timestamp(1587948690)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

            mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587947407, 149.4)
            mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587948690, 96.4)

            first_marker = filtered_result.get_first_marker()
            end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

            self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
            self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testNoQualifyingEntriesInDataSet(self):
        '''
            "1587948211": 17.8,
            "1587948217": 17.9,
            "1587948223": 16.9,
            "1587948667": 16.8,
            "1587948673": 23.7,
            "1587948678": 56.5,
            "1587948684": 76.0,
            "1587948690": 96.4
        '''

        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                1587948211, 1587948690,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(1587948211)
            end_timestamp = ts.Timestamp(1587948690)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

            mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587948211, 17.8)
            mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587948690, 96.4)

            first_marker = filtered_result.get_first_marker()
            end_marker = filtered_result.get_next_marker(first_marker)

            self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
            self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testSawToothPattern(self):
        '''
            Case 6
            "1587949200": 90,
            "1587949201": 150,
            "1587949202": 90,
            "1587949203": 150
        '''

        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                1587949200, 1587949203,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(1587949200)
            end_timestamp = ts.Timestamp(1587949203)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

            mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587949200, 90)
            mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949204, 150)

            first_marker = filtered_result.get_first_marker()
            end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

            self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
            self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testInitAndExitDisqualifyingMarker(self):
        '''
            Case 4
            "1587948690": 96.4,
            "1587948696": 114.3,
            "1587948702": 147.8,
            "1587949185": 158.2,
            "1587949191": 157.8,
            "1587949197": 159.5,
            "1587949200": 90
        '''
        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                1587948690, 1587949200,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(1587948690)
            end_timestamp = ts.Timestamp(1587949200)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

            mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587948690, 96.4)
            mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949200, 90)

            first_marker = filtered_result.get_first_marker()
            end_marker = filtered_result.get_next_marker(first_marker)

            self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
            self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testExitContinuousMarker(self):
        '''
            Case 8
            "1587949205": 150,
            "1587949206": 150,
            "1587949207": 150,
            "1587949208": 90,
            "1587949209": 90,
            "1587949210": 90
        '''

        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                1587949205, 1587949210,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(1587949205)
            end_timestamp = ts.Timestamp(1587949210)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

            mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587949204, 150)
            mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949210, 90)

            first_marker = filtered_result.get_first_marker()
            end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

            self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
            self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testInitContinuousMarker(self):
        '''
            Case 9
            "1587949208": 90,
            "1587949209": 90,
            "1587949210": 90,
            "1587949211": 150,
            "1587949212": 150,
            "1587949213": 150,
            "1587949214": 150
        '''

        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                1587949208, 1587949214,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(1587949208)
            end_timestamp = ts.Timestamp(1587949214)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

            mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587949208, 90)
            mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949215, 150)

            first_marker = filtered_result.get_first_marker()
            end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

            self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
            self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())
            self.assertEqual(None, filtered_result.get_next_marker(end_marker))

    def testAdjacentNormalMarker(self):
        '''
            Case 5
            "1587949214": 150,
            "1587949215": 90,
            "1587949216": 90,
            "1587949217": 150
        '''

        with patch('argus_tal.query_api.requests') as mock_tsdb:
            mock_tsdb.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(
                1587949214, 1587949217,
                self.__tsdb_ip,
                self.__tsdb_port,
                self.__test_timeseries_ts_id)

            start_timestamp = ts.Timestamp(1587949214)
            end_timestamp = ts.Timestamp(1587949217)
            test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
            filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

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
