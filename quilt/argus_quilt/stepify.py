'''
    This class accepts as input a FilteredTimeseries object, which contains data points as
    (time, value) pairs and also markers* which are special type of data points identifying a
    boundary condition.

    To plot data points on a graph, we'd put time as X-axis and value as Y-axis.

    Purpose of Stepify is take the FilteredTimeseries as input and generate a
    step function such that all Y-axis values in the step function are either 0 or
    the threshold value. The threshold value is defined by
    FilteredTimeseries::get_filter_constant().

    *Marker type and the immediately preceding/following value are used to decide whether
     to "step up" from 0 to 'threshold' or to "step down" from 'threshold' to 0. See __stepify()
     below for details.

     The resulting step function can be obtained by calling Stepify::get_stepified_time_windows().
     It returns an object of the type TimeWindowSequence.

     To visually understand how it works, consult the quilt algorithm:
     https://docs.google.com/presentation/d/15EnUsMb4w9Xwg26iMBw8uNcUB_Sd5uAqXQWmie3X60s
'''

from .filter_primitive import FilteredTimeseries
from .time_windows import TimeWindowSequence


class Stepify(object):
    def __init__(self, filtered_ts):
        assert(isinstance(filtered_ts, FilteredTimeseries))
        self.__transition_points = None
        # self.__transition_points is used to store the 'transition points' computed during the stepify process.
        # These transition_points are actually an intermediate result that are used to compute the time windows.

        self.__stepified_time_windows = None
        # self.__stepified_time_windows is used to store the final result (as a list of TimeWindows objects)

        self.__stepified_time_windows, self.__transition_points = self.__stepify(filtered_ts)

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

    def __prepare_time_windows(self, transition_points):
        '''
        The basic algorithm here is similar to wellformedness property.
        e.g. wellformedness of parentheses - "(", ")", "(", ")"

        We iterate over the list of transition points and construct tuples by picking 2 consecutive,
        items and then move to the next couple in an exclusive manner.
        e.g Input: transition_points = [w,x,y,z]
            Output: time_windows = [(w,x), (y,z)]
        '''
        time_windows = []
        idx = 0
        while idx < len(transition_points) - 1:
            time_windows.append((transition_points[idx], transition_points[idx + 1]))
            idx += 2
        return TimeWindowSequence(time_windows)

    def __stepify(self, filtered_timeseries):
        current_marker = filtered_timeseries.get_first_marker()
        threshold = filtered_timeseries.get_filter_constant()
        transition_points = []

        '''
        The basic algorithm here is as follows:
        1) Walk through all the markers to generate transition points.
            At each marker, make a decision on:
                (a) whether a step should be generated
                (b) If yes, generate the step by computing the point using __get_interpolation_point()
            Decision (a) is made based on the type of marker and what precedes/follows it.
        2) Walk through the transition points to generate the stepi-fied time windows.
        '''

        while current_marker is not None:
            if current_marker.get_marker_type() == FilteredTimeseries.MarkerTypes.INIT:
                if not isinstance(current_marker.get_next_element(), FilteredTimeseries.Marker):
                    if filtered_timeseries.is_value_filtered_out(current_marker.get_marker_value()):
                        transition_points.append(current_marker.get_next_key())
                    else:
                        transition_points.append(self.__get_interpolation_point(current_marker, threshold, "NEXT"))
            elif current_marker.get_marker_type() == FilteredTimeseries.MarkerTypes.NORMAL:
                if not isinstance(current_marker.get_prev_element(), FilteredTimeseries.Marker):
                    transition_points.append(self.__get_interpolation_point(current_marker, threshold, "PREV"))
                if not isinstance(current_marker.get_next_element(), FilteredTimeseries.Marker):
                    transition_points.append(self.__get_interpolation_point(current_marker, threshold, "NEXT"))
            elif current_marker.get_marker_type() == FilteredTimeseries.MarkerTypes.EXIT:
                if not isinstance(current_marker.get_prev_element(), FilteredTimeseries.Marker):
                    if filtered_timeseries.is_value_filtered_out(current_marker.get_marker_value()):
                        transition_points.append(current_marker.get_prev_key())
                    else:
                        transition_points.append(self.__get_interpolation_point(current_marker, threshold, "PREV"))
            else:
                # Should never get here
                assert False
            current_marker = filtered_timeseries.get_next_marker(current_marker)

        return self.__prepare_time_windows(transition_points), transition_points
