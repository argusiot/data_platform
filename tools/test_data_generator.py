import requests
import json
import time
from random import randint
from time import sleep

class TestDataGenerator(object):
    def __init__(self, url, metric, tag_name, tag_value):
        self.__url = url
        self.__metric = metric
        self.__tag_name = tag_name
        self.__tag_value = tag_value

    def push_data(self, start_timestamp, value):
        url = self.__url
        headers = {'content-type': 'application/json'}
        datapoint = {}
        datapoint['metric'] = self.__metric
        datapoint['timestamp'] = start_timestamp
        datapoint['value'] = value
        datapoint['tags'] = {}
        datapoint['tags'][self.__tag_name] = self.__tag_value
        response = requests.post(url, data=json.dumps(datapoint), headers=headers)

    def generate_slope(self, start_timestamp, frequency, total_data_points, init_value, final_value):
        print(start_timestamp, init_value)
        self.push_data(start_timestamp, init_value)
        total_data_points -= 1

        total_period = frequency * total_data_points
        end_timestamp = start_timestamp + total_period
        m = (final_value - init_value) / (end_timestamp - start_timestamp)
        c = init_value - (m * start_timestamp)

        current_timestamp = start_timestamp + frequency
        while total_data_points > 0:
            current_value = (m * current_timestamp) + c
            print(current_timestamp, current_value)
            self.push_data(current_timestamp, current_value)
            current_timestamp += frequency
            total_data_points -= 1

    def generate_straight_line(self, start_timestamp, frequency, total_data_points, value):
        current_timestamp = start_timestamp
        while total_data_points > 0:
            print(current_timestamp, value)
            # self.push_data(current_timestamp, value)
            current_timestamp += frequency
            total_data_points -= 1

    def generate_tilda_straight_line(self, start_timestamp, frequency, total_data_points, lower_range, upper_range):
        current_timestamp = start_timestamp
        while total_data_points > 0:
            print(current_timestamp, randint(lower_range, upper_range))
            self.push_data(current_timestamp, randint(lower_range, upper_range))
            current_timestamp += frequency
            total_data_points -= 1


def main():
    data_generator = TestDataGenerator('http://localhost:4242/api/put', 'mock_data', 'input', 'Melt-Temp')
    data_generator.generate_slope(1616083200, 10, 3, 0, 110)
    data_generator.push_data(1616083230, 55)
    data_generator.push_data(1616083240, 110)
    data_generator.generate_tilda_straight_line(1616083250, 10, 4, 108, 115)
    data_generator.generate_tilda_straight_line(1616083290, 10, 4, 75, 85)
    data_generator.generate_tilda_straight_line(1616083330, 10, 4, 108, 115)

    data_generator = TestDataGenerator('http://localhost:4242/api/put', 'mock_data', 'input', 'Barrel-Temp')
    data_generator.generate_slope(1616083200, 10, 3, 0, 110)
    data_generator.push_data(1616083230, 55)
    data_generator.generate_slope(1616083240, 10, 3, 65, 110)
    data_generator.generate_tilda_straight_line(1616083270, 10, 4, 80, 90)
    data_generator.generate_slope(1616083310, 10, 3, 95, 110)
    data_generator.generate_tilda_straight_line(1616083330, 10, 4, 108, 115)

    data_generator = TestDataGenerator('http://localhost:4242/api/put', 'mock_data_output', 'state', 'TestState')
    data_generator.push_data(1616073230, 55)

main()
