'''
    Test cases for filter primitive
'''

import os
import sys

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
        "34.221.154.248", 4242,
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
        self.__tsdb_ip = "34.221.154.248"
        self.__tsdb_port = 4242

        self.__test_result_dict = {}

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
        start_timestamp = ts.Timestamp(1587947403)
        end_timestamp = ts.Timestamp(1587949197)
        test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
        filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)
        self.assertEqual(filtered_result.get_data_dict(), test_timeseries)
        self.assertEqual(filtered_result.get_tsid(), self.__test_timeseries_ts_id)


    def testFilteredDataDictInit_Case1(self):
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

    def testFilteredDataDictInit_Case2(self):
        start_timestamp = ts.Timestamp(1587948690)
        end_timestamp = ts.Timestamp(1587949197)
        test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
        filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587948690, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949198, 159.5)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(first_marker)

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testFilteredDataDictInit_Case3(self):
        start_timestamp = ts.Timestamp(1587947403)
        end_timestamp = ts.Timestamp(1587948211)
        test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
        filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587947407, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587948211, 159.5)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(first_marker)

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testFilteredDataDictInit_Case4(self):
        start_timestamp = ts.Timestamp(1587947403)
        end_timestamp = ts.Timestamp(1587948690)
        test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
        filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587947407, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587948690, 159.5)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testFilteredDataDictInit_Case5(self):
        start_timestamp = ts.Timestamp(1587948211)
        end_timestamp = ts.Timestamp(1587948690)
        test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
        filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587948211, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587948690, 159.5)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(first_marker)

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testFilteredDataDictInit_Case6(self):
        start_timestamp = ts.Timestamp(1587949200)
        end_timestamp = ts.Timestamp(1587949203)
        test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
        filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587949200, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949204, 159.5)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())


    def testFilteredDataDictInit_Case7(self):
        start_timestamp = ts.Timestamp(1587948690)
        end_timestamp = ts.Timestamp(1587949200)
        test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
        filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587948690, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949200, 159.5)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(first_marker)

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testFilteredDataDictInit_Case8(self):
        start_timestamp = ts.Timestamp(1587949205)
        end_timestamp = ts.Timestamp(1587949210)
        test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
        filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587949204, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949210, 159.5)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())

    def testFilteredDataDictInit_Case9(self):
        start_timestamp = ts.Timestamp(1587949208)
        end_timestamp = ts.Timestamp(1587949214)
        test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
        filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)

        mock_first_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, 1587949208, 149.4)
        mock_end_marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, 1587949215, 159.5)

        first_marker = filtered_result.get_first_marker()
        end_marker = filtered_result.get_next_marker(filtered_result.get_next_marker(first_marker))

        self.assertEqual(first_marker.get_marker_key(), mock_first_marker.get_marker_key())
        self.assertEqual(end_marker.get_marker_key(), mock_end_marker.get_marker_key())
        self.assertEqual(None, filtered_result.get_next_marker(end_marker))