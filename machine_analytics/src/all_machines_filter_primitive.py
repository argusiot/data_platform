#!/usr/bin/python3

'''
    all_machines_filter_primitive.py
    Use case(s): COMMON_INFRA
    This is a common filter class for all machine analysis.

    Psuedo code on how to instantiate and use FilteredTimeseries

    #Use any timeseries of interest
    timeseries_id = ts_id.TimeseriesID("machine.sensor.dummy_melt_temperature",
                                       {"machine_name": "90mm_extruder"})

    # Primary start and end time stamps
    start_timestamp = ts.Timestamp(1587947403)
    end_timestamp = ts.Timestamp(1587949197)

    #Use the standard getTimeSeriesData function to obtain a TimeSeriesDataDict object
    result = getTimeSeriesData(timeseries_id, start_timestamp, end_timestamp)

    #Instantiate the FiteredTimeSeries object by passing the ts_dd object,
    filter_qualifier, and the constant to filterby in the respective order.
    filtered_result = FilteredTimeseries(result, FilterQualifier.GREATERTHAN, 100)

    #To iterate over the fileteredTimeseries, get the filtered dict from the Filtered Timeseries
    object. The returned object is a ordered dict from python. Sample below shows how to check
    for markers and get data from it.

    for i, (k,v) in enumerate(filtered_result.get_filtered_dict().items()):
        if isinstance(v, FilteredTimeseries.Marker):
            print(v.get_marker_type(), v.get_marker_value(), v.get_marker_key())
        if isinstance(v, FilteredTimeseries.Marker):
            if v.get_marker_type() == FilteredTimeseries.MarkerTypes.INIT:
                print(v.get_next_element())
        print(k,v)
'''

from enum import Enum
from itertools import dropwhile

from collections import OrderedDict
import operator


class FilterQualifier(Enum):
    GREATERTHAN = ">"
    GREATERTHAN_EQUAL = ">="
    LESSERTHAN = "<>"
    LESSERTHAN_EQUAL = "<="
    EQUALS = "=="


ops = {
    FilterQualifier.LESSERTHAN: operator.lt,
    FilterQualifier.LESSERTHAN_EQUAL: operator.le,
    FilterQualifier.GREATERTHAN: operator.gt,
    FilterQualifier.GREATERTHAN_EQUAL: operator.gt,
    FilterQualifier.EQUALS: operator.eq
}


class FilteredTimeseries(object):
    class MarkerTypes(Enum):
        INIT = "init"
        NORMAL = "normal"
        EXIT = "exit"

    class Marker(object):
        def __init__(self, marker_type, m_key, m_value):
            self.__type = marker_type
            self.__marker_key = m_key
            self.__marker_value = m_value
            self.__next_element = None
            self.__prev_element = None

        def get_marker_type(self):
            return self.__type

        def get_marker_key(self):
            return self.__marker_key

        def get_marker_value(self):
            return self.__marker_value

        def get_next_element(self):
            return self.__next_element

        def set_next_element(self, value):
            self.__next_element = value

        # This is needed only if linear interpolation is used
        def get_prev_element(self):
            return self.__prev_element

        # This is needed only if linear interpolation is used
        def set_prev_element(self, value):
            self.__prev_element = value

    # constructor for FilteredTimeseries
    def __init__(self, ts_datadict, filter_qualifier, filter_constant):
        self.__data_dict = ts_datadict
        self.__tsid = ts_datadict.get_timeseries_id()
        self.__filter_qualifier = filter_qualifier
        self.__filter_constant = filter_constant
        self.__filtered_dict = None
        self.__first_marker = None
        self.__filter_by()

    def get_data_dict(self):
        return self.__data_dict

    def get_tsid(self):
        return self.__tsid

    def get_filtered_dict(self):
        return self.__filtered_dict

    def get_first_marker(self):
        return self.__first_marker

    def get_next_marker(self, marker):
        if marker.get_marker_type() is FilteredTimeseries.MarkerTypes.EXIT:
            return None

        index = 0
        for key in dropwhile(lambda x: x != marker.get_marker_key(), self.__filtered_dict):
            if index > 0 and isinstance(self.__filtered_dict[key], FilteredTimeseries.Marker):
                return self.__filtered_dict[key]
            index += 1

    def __filter_by(self):
        result_dict = OrderedDict()
        op_func = ops[self.__filter_qualifier]

        # PASS 1
        for index, (key, value) in enumerate(self.__data_dict):
            if index == 0:
                if op_func(value, self.__filter_constant):
                    marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, key - 1, value)
                    result_dict.update({key - 1: marker})
                    result_dict.update({key: value})
                    self.__first_marker = marker
                else:
                    marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, key, value)
                    result_dict.update({key: marker})
                    self.__first_marker = marker
            elif index == len(self.__data_dict) - 1:
                if op_func(value, self.__filter_constant):
                    marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, key + 1, value)
                    result_dict.update({key: value})
                    result_dict.update({key + 1: marker})
                else:
                    marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, key, value)
                    result_dict.update({key: marker})
            elif op_func(value, self.__filter_constant):
                result_dict.update({key: value})
            elif not op_func(value, self.__filter_constant):
                marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.NORMAL, key, value)
                result_dict.update({key: marker})

        # PASS 2
        items = list(result_dict.items())
        prev_v = items[0]
        index = 1
        end = len(items)
        while index < end - 1:
            if isinstance(prev_v[1], FilteredTimeseries.Marker) \
                    and isinstance(items[index][1], FilteredTimeseries.Marker) \
                    and isinstance(items[index + 1][1], FilteredTimeseries.Marker):
                result_dict.pop(items[index][0])
            prev_v = items[index]
            index += 1

        # PASS 3 - Marker Fixup
        items = list(result_dict.items())
        for index, (key, value) in enumerate(result_dict.items()):
            if isinstance(value, FilteredTimeseries.Marker):
                if value.get_marker_type() is FilteredTimeseries.MarkerTypes.INIT:
                    value.set_next_element(items[index + 1][1])
                if value.get_marker_type() is FilteredTimeseries.MarkerTypes.NORMAL:
                    value.set_next_element(items[index + 1][1])
                    value.set_prev_element(items[index - 1][1])
                if value.get_marker_type() is FilteredTimeseries.MarkerTypes.EXIT:
                    value.set_prev_element(items[index - 1][1])

        self.__filtered_dict = result_dict