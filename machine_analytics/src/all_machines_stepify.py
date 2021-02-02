'''
Stepify TBD
'''

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from all_machines_filter_primitive import FilteredTimeseries


class TimeWindows(object):
    def __init__(self, tw):
        self.__time_windows = tw

    def get_time_windows(self):
        return self.__time_windows

    def set_time_windows(self, time_windows):
        self.__time_windows = time_windows


class Stepify(object):
    def __init__(self, filtered_ts):
        self.__filtered_timeseries = filtered_ts
        self.__transition_points = None
        self.__stepified_time_windows = None
        self.__stepify()

    def get_stepified_time_windows(self):
        return self.__stepified_time_windows

    def get_transition_points(self):
        return self.__transition_points

    def __calculate_x_intercept(self, p1_coordinates, p2_coordinates, y_intercept):
        x1, y1 = p1_coordinates
        x2, y2 = p2_coordinates

        m = (y2 - y1) / (x2 - x1)
        c = y1 - (m * x1)
        x_intercept = ((y_intercept - c) / m)
        return x_intercept

    def __get_interpolation_point(self, current_marker, threshold, direction):
        interpolation_point = 0
        if direction == "PREV":
            interpolation_point = self.__calculate_x_intercept(
                (current_marker.get_prev_key(), current_marker.get_prev_element()),
                (current_marker.get_marker_key(), current_marker.get_marker_value()), threshold)
        elif direction == "NEXT":
            interpolation_point = self.__calculate_x_intercept(
                (current_marker.get_marker_key(), current_marker.get_marker_value()),
                (current_marker.get_next_key(), current_marker.get_next_element()), threshold)
        return interpolation_point

    def __prepare_time_windows(self):
        time_windows = []
        for idx, val in enumerate(self.__transition_points):
            if idx < len(self.__transition_points) - 1:
                time_windows.append((val, self.__transition_points[idx+1]))
        self.__stepified_time_windows = TimeWindows(time_windows)

    def __stepify(self):
        current_marker = self.__filtered_timeseries.get_first_marker()
        threshold = self.__filtered_timeseries.get_filter_constant()
        element_list = []

        while self.__filtered_timeseries.get_next_marker(current_marker) is not None:
            if current_marker.get_marker_type() == FilteredTimeseries.MarkerTypes.INIT:
                if not isinstance(current_marker.get_next_element(), FilteredTimeseries.Marker):
                    element_list.append(self.__get_interpolation_point(current_marker, threshold, "NEXT"))
            elif current_marker.get_marker_type() == FilteredTimeseries.MarkerTypes.NORMAL:
                if not isinstance(current_marker.get_prev_element(), FilteredTimeseries.Marker):
                    element_list.append(self.__get_interpolation_point(current_marker, threshold, "PREV"))
                if not isinstance(current_marker.get_next_element(), FilteredTimeseries.Marker):
                    element_list.append(self.__get_interpolation_point(current_marker, threshold, "NEXT"))
            elif current_marker.get_marker_type() == FilteredTimeseries.MarkerTypes.EXIT:
                if not isinstance(current_marker.get_prev_element(), FilteredTimeseries.Marker):
                    element_list.append(self.__get_interpolation_point(current_marker, threshold, "PREV"))
            current_marker = self.__filtered_timeseries.get_next_marker(current_marker)

        self.__transition_points = element_list
        self.__prepare_time_windows()
