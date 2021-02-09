'''
    This class is used to maintain the stepified time windows.
'''


class TimeWindowSequence(object):
    def __init__(self, tw):
        self.__time_windows = tw

    def get_time_windows(self):
        return self.__time_windows

    def set_time_windows(self, time_windows):
        self.__time_windows = time_windows