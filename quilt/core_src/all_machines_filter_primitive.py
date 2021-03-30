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
    LESSERTHAN = "<"
    LESSERTHAN_EQUAL = "<="
    EQUALS = "=="


filtering_criterion_ops = {
    FilterQualifier.LESSERTHAN: operator.lt,
    FilterQualifier.LESSERTHAN_EQUAL: operator.le,
    FilterQualifier.GREATERTHAN: operator.gt,
    FilterQualifier.GREATERTHAN_EQUAL: operator.ge,
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
            self.__next_key = None
            self.__next_element = None
            self.__prev_key = None
            self.__prev_element = None

        def get_marker_type(self):
            return self.__type

        def get_marker_key(self):
            return self.__marker_key

        def get_marker_value(self):
            return self.__marker_value

        def set_next_key(self, key):
            self.__next_key = key

        def get_next_key(self):
            return self.__next_key

        def get_next_element(self):
            return self.__next_element

        def set_next_element(self, value):
            self.__next_element = value

        def set_prev_key(self, key):
            self.__prev_key = key

        def get_prev_key(self):
            return self.__prev_key

        # This is needed only if linear interpolation is used
        def get_prev_element(self):
            return self.__prev_element

        # This is needed only if linear interpolation is used
        def set_prev_element(self, value):
            self.__prev_element = value

    # constructor for FilteredTimeseries
    def __init__(self, ts_datadict, filter_qualifier, filter_constant):
        self.__timeseries_data_dict = ts_datadict
        self.__tsid = ts_datadict.get_timeseries_id()
        self.__filter_qualifier = filter_qualifier
        self.__filter_constant = filter_constant
        self.__filtered_dict = None
        self.__first_marker = None
        self.__filter_by()

    def get_timeseries_data_dict(self):
        return self.__timeseries_data_dict

    def get_tsid(self):
        return self.__tsid

    def get_filter_qualifier(self):
        return self.__filter_qualifier

    def get_filter_constant(self):
        return self.__filter_constant

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
        filter_criterion_func = filtering_criterion_ops[self.__filter_qualifier]

        '''
        Spread Sheet containing the cases the following logic is designed for.
        https://docs.google.com/spreadsheets/d/1qenFE7QDa_4zUordDWembJJ6BMWZWDXJv_fveTm5y2s/edit#gid=0
        '''
        # Pass 1 : Identify all the markers.
        # We define any element that doesn't meet filtering criterion as marker.
        for cur_index, (key, value) in enumerate(self.__timeseries_data_dict):
            if cur_index == 0: # First element requires special handling
                if filter_criterion_func(value, self.__filter_constant):
                    marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, key - 1, value)
                    result_dict.update({key - 1: marker})
                    result_dict.update({key: value})
                    self.__first_marker = marker
                else:
                    marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.INIT, key, value)
                    result_dict.update({key: marker})
                    self.__first_marker = marker
            elif cur_index == len(self.__timeseries_data_dict) - 1: # Last element requires special handling
                if filter_criterion_func(value, self.__filter_constant):
                    marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, key + 1, value)
                    result_dict.update({key: value})
                    result_dict.update({key + 1: marker})
                else:
                    marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.EXIT, key, value)
                    result_dict.update({key: marker})
            else:  # All other elements
                if not filter_criterion_func(value, self.__filter_constant):
                    # Any value filtered out is a marker.
                    marker = FilteredTimeseries.Marker(FilteredTimeseries.MarkerTypes.NORMAL, key, value)
                    result_dict.update({key: marker})
                else:
                    # Value meets criterion to not get filtered out, hence include as is in result set.
                    result_dict.update({key: value})

        # Pass 2 - Compress non-boundary markers
        items = list(result_dict.items())
        prev_key, prev_value = items[0]
        cur_index = 1
        end = len(items)
        while cur_index < end - 1:
            if isinstance(prev_value, FilteredTimeseries.Marker) \
                    and isinstance(items[cur_index][1], FilteredTimeseries.Marker) \
                    and isinstance(items[cur_index + 1][1], FilteredTimeseries.Marker):
                result_dict.pop(items[cur_index][0])
            prev_key, prev_value = items[cur_index]
            cur_index += 1

        # PASS 3 - Marker Fixup
        items = list(result_dict.items())
        for cur_index, (key, value) in enumerate(result_dict.items()):
            if isinstance(value, FilteredTimeseries.Marker):
                if value.get_marker_type() is FilteredTimeseries.MarkerTypes.INIT:
                    value.set_next_key(items[cur_index + 1][0])
                    value.set_next_element(items[cur_index + 1][1])
                if value.get_marker_type() is FilteredTimeseries.MarkerTypes.NORMAL:
                    value.set_next_key(items[cur_index + 1][0])
                    value.set_next_element(items[cur_index + 1][1])
                    value.set_prev_key(items[cur_index - 1][0])
                    value.set_prev_element(items[cur_index - 1][1])
                if value.get_marker_type() is FilteredTimeseries.MarkerTypes.EXIT:
                    value.set_prev_key(items[cur_index - 1][0])
                    value.set_prev_element(items[cur_index - 1][1])

        self.__filtered_dict = result_dict

    def is_value_filtered_out(self, value):
        filter_criterion_func = filtering_criterion_ops[self.__filter_qualifier]
        if filter_criterion_func(value, self.__filter_constant):
            return True
        else:
            return False
