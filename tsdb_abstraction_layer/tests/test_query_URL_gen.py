# -*- coding: utf-8 -*-

from .context import argus_tal
from argus_tal import basic_types as bt
from argus_tal import exceptions as tal_err
from argus_tal import query_urlgen as qurlg
from argus_tal import timestamp as tstamp
from argus_tal import timeseries_id as ts_id
import unittest

class QueryURLGenerator_Tests(unittest.TestCase):
  def __init__(self, *args, **kwargs):
    super(QueryURLGenerator_Tests, self).__init__(*args, **kwargs)
    self.__tsdb_type = bt.Tsdb.OPENTSDB
    self.__host = "34.221.154.248"
    self.__port = 4242
    self.__start_time = tstamp.Timestamp("1592530632")
    self.__end_time = tstamp.Timestamp("1592530682")
    self.__query_agg = bt.Aggregator.NONE
    metric1 = "machine.sensor.raw_melt_temperature"
    filters = {"port_num": "1"}
    multiple_filters = {"tag1": "val1", "tag2": "val2", "tag3":"val3"}
    self.__tsid1 = ts_id.TimeseriesID(metric1, filters)
    self.__tsid_multi_filter = ts_id.TimeseriesID(metric1, multiple_filters)

    # Build a list of timeseries IDs.
    self.__tsid_list = []
    self.__tsid_list.append(self.__tsid1)
    self.__tsid_list.append(ts_id.TimeseriesID( \
        "machine.sensor.raw_melt_pressure", filters))
    self.__tsid_list.append(ts_id.TimeseriesID( \
        "machine.sensor.raw_screw_speed", filters))

    # A handy timeseries ID with an empty filter.
    self.__tsid_no_filters = ts_id.TimeseriesID(metric1, {})

  def test_single_metric_url(self):
    url = qurlg.url(self.__tsdb_type, self.__host, self.__port, \
                    self.__start_time, self.__end_time, \
                    self.__query_agg, [self.__tsid1])
    self.assertEqual( \
      url, \
      "http://34.221.154.248:4242/api/query?start=1592530632&end=1592530682" \
      "&m=none:machine.sensor.raw_melt_temperature{port_num=1}" \
    )

  def test_single_metric_no_filter(self):
    url = qurlg.url(self.__tsdb_type, self.__host, self.__port, \
                    self.__start_time, self.__end_time, \
                    self.__query_agg, [self.__tsid_no_filters])
    self.assertEqual( \
      url, \
      "http://34.221.154.248:4242/api/query?start=1592530632&end=1592530682" \
      "&m=none:machine.sensor.raw_melt_temperature{}" \
    )

  def test_multi_metric_url(self):
    url = qurlg.url(self.__tsdb_type, self.__host, self.__port, \
                    self.__start_time, self.__end_time, \
                    self.__query_agg, self.__tsid_list)
    self.assertEqual( \
      url, \
      "http://34.221.154.248:4242/api/query?start=1592530632&end=1592530682" \
      "&m=none:machine.sensor.raw_melt_temperature{port_num=1}" \
      "&m=none:machine.sensor.raw_melt_pressure{port_num=1}" \
      "&m=none:machine.sensor.raw_screw_speed{port_num=1}" \
    )

  def test_single_metric_url_with_rate(self):
    url = qurlg.url(self.__tsdb_type, self.__host, self.__port, \
                    self.__start_time, self.__end_time, \
                    self.__query_agg, [self.__tsid1], flag_compute_rate=True)
    self.assertEqual( \
      url, \
      "http://34.221.154.248:4242/api/query?start=1592530632&end=1592530682" \
      "&m=none:rate:machine.sensor.raw_melt_temperature{port_num=1}" \
    )

  def test_single_metric_no_filter_with_rate(self):
    url = qurlg.url(self.__tsdb_type, self.__host, self.__port, \
                    self.__start_time, self.__end_time, \
                    self.__query_agg, [self.__tsid_no_filters], \
                    flag_compute_rate=True)
    self.assertEqual( \
      url, \
      "http://34.221.154.248:4242/api/query?start=1592530632&end=1592530682" \
      "&m=none:rate:machine.sensor.raw_melt_temperature{}" \
    )

  def test_single_metric_multiple_filters(self):
    url = qurlg.url(self.__tsdb_type, self.__host, self.__port, \
                    self.__start_time, self.__end_time, \
                    self.__query_agg, [self.__tsid_multi_filter])
    self.assertEqual( \
      url, \
      "http://34.221.154.248:4242/api/query?start=1592530632&end=1592530682" \
      "&m=none:machine.sensor.raw_melt_temperature{tag1=val1,tag2=val2,tag3=val3}" \
    )

  def test_single_metric_url_with_millisecond_response(self):
    url = qurlg.url(self.__tsdb_type, self.__host, self.__port, \
                    self.__start_time, self.__end_time, \
                    self.__query_agg, [self.__tsid1], flag_ms_response=True)
    self.assertEqual( \
      url, \
      "http://34.221.154.248:4242/api/query?start=1592530632&end=1592530682" \
      "&ms=true&m=none:machine.sensor.raw_melt_temperature{port_num=1}" \
    )

  def test_single_metric_url_with_millisecond_response_and_rate(self):
    url = qurlg.url(self.__tsdb_type, self.__host, self.__port,
                    self.__start_time, self.__end_time,
                    self.__query_agg, [self.__tsid1],
                    flag_ms_response=True, flag_compute_rate=True)
    self.assertEqual( \
      url, \
      "http://34.221.154.248:4242/api/query?start=1592530632&end=1592530682" \
      "&ms=true&m=none:rate:machine.sensor.raw_melt_temperature{port_num=1}" \
    )

  def test_multi_metric_url_with_millisecond_response(self):
    url = qurlg.url(self.__tsdb_type, self.__host, self.__port, \
                    self.__start_time, self.__end_time, \
                    self.__query_agg, self.__tsid_list, flag_ms_response=True)
    self.assertEqual( \
      url, \
      "http://34.221.154.248:4242/api/query?start=1592530632&end=1592530682" \
      "&ms=true"
      "&m=none:machine.sensor.raw_melt_temperature{port_num=1}" \
      "&m=none:machine.sensor.raw_melt_pressure{port_num=1}" \
      "&m=none:machine.sensor.raw_screw_speed{port_num=1}" \
    )

  def test_multi_metric_url_with_rate_and_millisecond_response(self):
    url = qurlg.url(self.__tsdb_type, self.__host, self.__port,
                    self.__start_time, self.__end_time,
                    self.__query_agg, self.__tsid_list,
                    flag_ms_response=True, flag_compute_rate=True)
    self.assertEqual( \
      url, \
      "http://34.221.154.248:4242/api/query?start=1592530632&end=1592530682"
      "&ms=true"
      "&m=none:rate:machine.sensor.raw_melt_temperature{port_num=1}"
      "&m=none:rate:machine.sensor.raw_melt_pressure{port_num=1}"
      "&m=none:rate:machine.sensor.raw_screw_speed{port_num=1}"
    )

if __name__ == '__main__':
  unittest.main()
