#!/usr/bin/python3

'''
   all_machines_filter_primitive.py
   Use case(s): COMMON_INFRA
   This is a common filter class for all machine analysis.
'''

from builtins import print
from enum import Enum
from itertools import islice, dropwhile

from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
from collections import OrderedDict
import operator

class FilterQualifier(Enum):
    GREATERTHAN = ">"
    GREATERTHAN_EQUAL = ">="
    LESSERTHAN = "<>"
    LESSERTHAN_EQUAL = "<="
    EQUALS = "=="

ops = {
    FilterQualifier.LESSERTHAN:  operator.lt,
    FilterQualifier.LESSERTHAN_EQUAL: operator.le,
    FilterQualifier.GREATERTHAN:  operator.gt,
    FilterQualifier.GREATERTHAN_EQUAL: operator.gt,
    FilterQualifier.EQUALS: operator.eq
}

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


class FilteredDataDict(object):
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

    def get_next_marker(self,marker):
        if marker.get_marker_type() is MarkerTypes.EXIT:
            return None

        i = 0
        for k in dropwhile(lambda x: x != marker.get_marker_key(), self.__filtered_dict):
            if i > 0 and isinstance(self.__filtered_dict[k], Marker):
                return self.__filtered_dict[k]
            i += 1

        # found = False
        # for k, v in self.__filtered_dict.items():
        #     if found is False:
        #         if isinstance(v, Marker) and v is marker:
        #             found = True
        #     elif found is True and isinstance(v, Marker):
        #         return v

    def __filter_by(self):
        result_dict = OrderedDict()
        op_func = ops[self.__filter_qualifier]

        # PASS 1
        for i, (k, v) in enumerate(self.__data_dict):
            if i == 0:
                if op_func(v, self.__filter_constant):
                    marker = Marker(MarkerTypes.INIT, k - 1, v)
                    result_dict.update({k - 1: marker})
                    result_dict.update({k: v})
                    self.__first_marker = marker
                else:
                    marker = Marker(MarkerTypes.INIT, k, v)
                    result_dict.update({k: marker})
                    self.__first_marker = marker
            elif i == len(self.__data_dict) - 1 :
                if op_func(v, self.__filter_constant):
                    marker = Marker(MarkerTypes.EXIT, k + 1, v)
                    result_dict.update({k: v})
                    result_dict.update({k + 1: marker})
                else:
                    marker = Marker(MarkerTypes.EXIT, k, v)
                    result_dict.update({k: marker})
            elif op_func(v, self.__filter_constant):
                result_dict.update({k: v})
            elif not op_func(v, self.__filter_constant):
                marker = Marker(MarkerTypes.NORMAL, k, v)
                result_dict.update({k: marker})


        # PASS 2
        items = list(result_dict.items())
        prev_v = items[0]
        index = 1
        end = len(items)
        while index < end-1:
            if isinstance(prev_v[1], Marker) and isinstance(items[index][1], Marker) and isinstance(items[index+1][1], Marker):
                result_dict.pop(items[index][0])
            prev_v = items[index]
            index += 1

        # PASS 3 - Marker Fixup
        items = list(result_dict.items())
        for i, (k, v) in enumerate(result_dict.items()):
            if isinstance(v, Marker):
                if v.get_marker_type() is MarkerTypes.INIT:
                    v.set_next_element(items[i+1][1])
                if v.get_marker_type() is MarkerTypes.NORMAL:
                    v.set_next_element(items[i + 1][1])
                    v.set_prev_element(items[i - 1][1])
                if v.get_marker_type() is MarkerTypes.EXIT:
                    v.set_prev_element(items[i - 1][1])

        self.__filtered_dict = result_dict






























