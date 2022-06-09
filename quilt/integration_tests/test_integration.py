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
import re
import os
import sys
import unittest
from collections import OrderedDict
from json import loads
from unittest.mock import Mock, patch
import responses
from responses import matchers
import json
import importlib.resources as pkg_resources
sys.path.append("..")
sys.path.append("../..")
from tsdb_abstraction_layer.argus_tal.timeseries_id import TimeseriesID
from urllib import parse


from .context import argus_quilt
from argus_quilt.filter_primitive import FilteredTimeseries, FilterQualifier
from argus_quilt.stepify import Stepify
from argus_quilt.state_set_processor import StateSetProcessor
from argus_quilt.state_set_processor_builder import StateSetProcessorBuilder
from argus_tal import timeseries_id as ts_id
from argus_tal import query_api
from argus_tal import basic_types as bt
from argus_tal import timestamp as ts
from argus_tal import query_urlgen as qurlgen

import pandas as pd


class Integration_Tests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(Integration_Tests, self).__init__(*args, **kwargs)
        self.__test_timeseries_ts_id1 = ts_id.TimeseriesID("machine.sensor.dummy_melt_temperature",
                                                          {"machine_name": "90mm_extruder"})
        self.__test_timeseries_ts_id2 = ts_id.TimeseriesID("machine.sensor.dummy_barrel_temperature",
                                                          {"machine_name": "90mm_extruder"})
        self.__test_timeseries_ts_id3 = ts_id.TimeseriesID("machine.sensor.dummy_melt_temperature",
                                                          {"machine_name": "60mm_extruder"})
        self.__test_timeseries_ts_id4 = ts_id.TimeseriesID("machine.sensor.dummy_barrel_temperature",
                                                          {"machine_name": "60mm_extruder"})
        self.__tsdb_ip = "172.0.0.1"
        self.__tsdb_port = 4242
        self.__replace_new_vals = True #setting to remove duplicate entries from mock TSDB. True simulates real behavior
        self.__test_output_df = pd.DataFrame(columns=['metric', 'timestamp', 'value'])
        '''
        The following __test_result_dict is organized in this manner:
        "Query URL" -> "Timeseries result"
        The query URL is constructed based on (timeseries_id, start_time & end_time) being used for a test case.
        '''
        self.__test_result_dict = {}

    # def __getTimeSeriesData(self, tsids, start_timestamp, end_timestamp):
    #     foo = query_api.QueryApi(
    #         self.__tsdb_ip, self.__tsdb_port,
    #         start_timestamp, end_timestamp,
    #         tsids,
    #         bt.Aggregator.NONE,
    #         False,
    #     )

    #     rv = foo.populate_ts_data()
    #     assert rv == 0

    #     result_list = foo.get_result_set()

    #     return result_list

    #change
    def __setup_testcase_data(self, start,
                              end,
                              server_ip,
                              server_port,
                              tsids):

        # Step 1:
        this_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(this_dir, 'test_data/mock_data.json')
        with open(file_path, 'r') as dataFile:
            data = dataFile.read()
        raw_dict = loads(data, object_pairs_hook=OrderedDict)

        metric_tags = [(tsid.metric_id, tsid.filters) for tsid in tsids]
        output = []
        for tseries in raw_dict:
            if((tseries['metric'], tseries['tags']) in metric_tags):
                new_dps = OrderedDict()
                for k, v in tseries['dps'].items():
                    if start <= int(k) <= end:
                        new_dps.update({k: v})
                    elif int(k) > end:
                        break
                tseries['dps'] = new_dps
                output.append(tseries)

        # Step 2:
        start_ts, end_ts = ts.Timestamp(start), ts.Timestamp(end)
        url_to_expect = qurlgen.url(
            bt.Tsdb.OPENTSDB, server_ip, server_port,
            start_ts, end_ts,
            bt.Aggregator.NONE, tsids)

        self.__store_expected_result(url_to_expect, 200, output)

    # def __build_opentsdb_json_response(self, tsids, timeseries_dict):
    #     json_response = []
    #     for tsid in tsids:
    #         ts_response = {
    #             "aggregateTags": [],
    #             "dps": {
    #                 # Fill in data from timeseries_dict.
    #                 k: v for k, v in timeseries_dict.items()
    #             },
    #             # Fill in metric name from ts_id.
    #             "metric": ts_id.metric_id,

    #             # Fill in tag value pairs from the filters in ts_id.
    #             "tags": {
    #                 k: v for k, v in ts_id.filters.items()
    #             }
    #         }
    #         json_response.append(ts_response)
    #     return json_response

    def __store_expected_result(self, url, resp_code, timeseries_dict):
        if resp_code == 200:
            json_resp = timeseries_dict
        else:
            json_resp = None
        self.__test_result_dict[url] = (resp_code, json_resp)

    def fulfill_query(self, url):
        query = parse.parse_qs(parse.urlparse(url).query)
        start = int(query['start'][0])
        end = int(query['end'][0])
        ms = query['m']
        tsids = []
        for m in ms:
            m_split = re.split(":|{|}", m)
            metric = m_split[1]
            tag_string = m_split[2]
            tag_dict = {re.split("=", pair)[0]:re.split("=", pair)[1] for pair in re.split(",", tag_string)}
            tsid = TimeseriesID(metric, tag_dict)
            tsids.append(tsid)
        self.__setup_testcase_data(start, end, self.__tsdb_ip, self.__tsdb_port, tsids)
    def mocked_requests_get(self, url):
        resp_mock = Mock()
        self.fulfill_query(url)
        resp_mock.status_code, resp_mock.json.return_value = self.__test_result_dict[url]
        return resp_mock
    
    def mocked_requests_post(self, url, data, headers):
        _data = json.loads(data)
        newdata = {**_data, **_data['tags']}
        del newdata['tags']
        newdata['value'] = float(newdata['value'])
        newrow = pd.DataFrame.from_dict([newdata])
        self.__test_output_df = pd.concat([self.__test_output_df, newrow], ignore_index=True)
        assert url == 'http://%s:%d/api/put' % (self.__tsdb_ip,
                                    self.__tsdb_port)
        if(self.__replace_new_vals):
            self.__test_output_df = self.__test_output_df.drop_duplicates()

    def mock_integration_helper(self, t1, t2, tsids, applique_file, output_granularity=30):
        with patch('argus_quilt.state_set_processor.requests') as mock_tsdb, patch('argus_tal.query_api.requests') as mock_tsdb2:
            mock_tsdb.post.side_effect = self.mocked_requests_post
            mock_tsdb2.get.side_effect = self.mocked_requests_get

            self.__setup_testcase_data(t1, t2, self.__tsdb_ip, self.__tsdb_port, tsids)

            # start_timestamp = ts.Timestamp(t1)
            # end_timestamp = ts.Timestamp(t2)
            # self.__getTimeSeriesData(tsids, start_timestamp, end_timestamp)

            with pkg_resources.path( \
                "argus_quilt", "SCHEMA_DEFN_state_set.json") as schema_file:
                    builder = StateSetProcessorBuilder(schema_file, self.__tsdb_ip, self.__tsdb_port)
                    __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                                    os.path.dirname(__file__)))
                    with open(os.path.join(__location__, applique_file)) as file:
                        state_set_json_schema = json.load(file)
                    processor = builder.build(state_set_json_schema)
                    processor.one_shot(t1, t2, output_granularity)


    # def mock_stepify_helper(self, t1, t2):
    #     with patch('argus_tal.query_api.requests') as mock_tsdb:
    #         mock_tsdb.get.side_effect = self.mocked_requests_get

    #         self.__setup_testcase_data(
    #             t1, t2,
    #             self.__tsdb_ip,
    #             self.__tsdb_port,
    #             self.__test_timeseries_ts_id)

    #         start_timestamp = ts.Timestamp(t1)
    #         end_timestamp = ts.Timestamp(t2)
    #         test_timeseries = getTimeSeriesData(self.__test_timeseries_ts_id, start_timestamp, end_timestamp)
    #         filtered_result = FilteredTimeseries(test_timeseries, FilterQualifier.GREATERTHAN, 100)
    #         return Stepify(filtered_result)

    def testIntegrationInit(self):
        tsid1 = TimeseriesID("mock_data", {"input":"Melt-Temp"})
        tsid2 = TimeseriesID("mock_data", {"input":"Barrel-Temp"})
        self.mock_integration_helper(1616083200, 1616083360, [tsid1, tsid2], "sample_input.json")
        this_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(this_dir, 'test_data/expected_output_case1.csv')
        print(pd.read_csv(file_path))
        pd.testing.assert_frame_equal(self.__test_output_df, pd.read_csv(file_path), check_dtype=False, check_exact=False)
        self.assertAlmostEqual(self.__test_output_df[self.__test_output_df['state_label'] == "Melt"]['value'].sum(), 46.56565618515015)
        
    # def testStepifyInit(self):
    #     stepified_result = self.mock_stepify_helper(1587949200, 1587949214)
    #     self.assertEqual(len(stepified_result.get_stepified_time_windows().get_time_windows()), 3)
    #     self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
    #                      (1587949200.1666667, 1587949201.8333333))
    #     self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[1],
    #                      (1587949202.1666667, 1587949207.8333333))
    #     self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[2],
    #                      (1587949210.1666667, 1587949214))

    # def testStepifyCase1(self):
    #     stepified_result = self.mock_stepify_helper(1587947408, 1587948205)

    #     self.assertEqual(stepified_result.get_stepified_time_windows().get_time_windows()[0],
    #                      (1587947408, 1587948205))
