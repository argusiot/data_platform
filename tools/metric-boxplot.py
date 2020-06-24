#!/usr/bin/python
'''
   Usage: ./metric-boxplot.py <out-put-dir>
   Example usage: ./metric-boxplot.py /vagrant/boxplots/

   FIXME: Add elaborate notes explainining what is happening here !!
'''

import argparse
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys
from metric_query import get_data_set
from collections import OrderedDict

parser = argparse.ArgumentParser(description="Tool to generate box plot for" \
   " all 8 channels of extruder machine")
parser.add_argument("input_file", help=".csv file containing the input data. Example data file: https://docs.google.com/spreadsheets/d/1a1GZeSylfCLVpj_lTlNcSvNi1Cz1qwTYQkfh2wGA5PQ/edit#gid=0")
parser.add_argument("output_dir", help="Location to save the generated boxplots")
args = parser.parse_args()

'''
 These values come from:
 https://docs.google.com/document/d/1gE8gTbTKHgaSs3BjsOmuH920oyZDiPX0nw-zpAyvgsw/edit#
  Format:
    data set name -> ([time window], machine_name)

    This allows us to collect and analyse data sets from parallel experiments
    being done on different gateways (attached to different machines). This
    works as long as the machines are of the same "extrude type" and the
    parameters being read from there are identical.

  Usage of "data set name" for box plot filename:
  -----------------------------------------------
  The box plot file name is derived from the data set name by replacing space
  with underscore.

ENABLE THIS FOR TOOL DEVELOPMENT MODE:
test_data_src = OrderedDict()
test_data_src["B2 Meanwell 12bit noise"] = (["2m-ago", "1m-ago"], "65mm_extruder")
test_data_src["B2 Meanwell 12bit 4mA"] = (["2m-ago", "1m-ago"], "65mm_extruder")
test_data_src["B2 Meanwell 12bit 12mA"] = (["2m-ago", "1m-ago"], "65mm_extruder")
test_data_src["B2 Meanwell 12bit 20mA"] = (["2m-ago", "1m-ago"], "65mm_extruder")
'''


def generate_filename(timewindow_id):
  return timewindow_id.replace(" ", "_")

'''
  The following 2 pieces of information (metric_list and hardware_channel_num)
  should be obtained from the data model via APIs. For now hardcoding it here.

  metric_list and hardware_channel_num server quite different purposes.

  metric_list:
   Needed to construct query URL for retrieving information from TSDB.

  hardware_channel_num:
   Needs to be printed in the report generated by this tool. That channel number
   is crucial information for the reader of that report.

  Source for metric_list & hardware_channel_num below is the 65mm & 90mm
  extruder machine configs from here:
  https://github.com/argusiot/authored-source-code/tree/master/deployments/customer_sites/pp-lab/input
'''
hardware_channel_num = [8, 7, 6, 5, 4, 3, 2, 1]
metric_list = ["raw_melt_temperature", "raw_melt_pressure", "raw_screw_speed", \
               "raw_line_speed", "raw_barrel_temperature_1", \
               "raw_barrel_temperature_2", "raw_machine_powerOn_state", \
               "raw_wire_output_diameter"] 


# For now, we hardcode the URL template. Ideally, we should not have to do this.
# This should be an API for us to get the data from.
url_template="http://34.221.154.248:4242/api/query?start=%s&end=%s&m=none:machine.sensor.%s{machine_name=%s}"

# Format:
# (label_str, metric_id, hw_chan_num, total_cnt, Min, Max, Mean, StdDev, %age-std-dev)
statistics_results = []

# Build a dictionary from the input CSV file. The dictionary should look like
# test_data_src.
# CSV schema:
# ['Board', 'Power supply', 'Sampling resolution', 'Input signal', 'Start time', 'End time', 'Machine', 'Manually audited', 'Start time (derived)', 'End time (derived)', 'Query URL']
label_format="Label format: <ADC board> <power_src> <sampling resolution> <input_signal>"
def build_test_data_src_from_csv(input_file):
  test_data = OrderedDict()
  with open(input_file) as csvfile:
      first_line = True
      reader = csv.reader(csvfile, delimiter=',')
      for line in reader:
        if first_line:  # skip the first line
          first_line = False
          continue

        board, power_supply, sampling_res, input_signal, \
        start_time_msec, end_time_msec, machine, audited, ignore1, \
        ignore2, ignore3 = line

        # The data_label is formatted per label_format above !
        data_label = "%s %s %s %s" % (board, power_supply, sampling_res, \
                                      input_signal)
        if start_time_msec == "" or \
           end_time_msec == "" or \
           machine == "":
          print("Skipping %s ...incomplete information !"  % data_label)
          continue

        # Add record into test_data{}
        test_data[data_label] = ([int(start_time_msec), int(end_time_msec)], \
                                  machine)
  return test_data

# Populate test_data_src from CSV file input.
test_data_src = build_test_data_src_from_csv(args.input_file)

for data_label, (time_window, machine_name) in test_data_src.items():
  
  print("Processing Label - %s " % data_label)
  if len(time_window) > 0:
    print("Time window: (%s, %s)" % (time_window[0], time_window[1]))
  else:
    print("Skipping\n")
    continue

  # A place to collect the results returned for each metric query.
  box_plot_data = []
  for idx in range(len(metric_list)):
    url = url_template % (time_window[0], time_window[1], \
                          metric_list[idx], machine_name)
    print(url)
    sorted_data_values = get_data_set(url).values()  # Extract list of values
                                                     # from the returned dict.
    sorted_data_values.sort()                        # ...and sort the list.
    
    # Calculate statistics for the data received and store in the stats result.
    np_stats_calculator = np.array([sorted_data_values])
    statistics_results.append( \
      (data_label, metric_list[idx], hardware_channel_num[idx], \
       len(sorted_data_values), \
       sorted_data_values[0], sorted_data_values[len(sorted_data_values) - 1], \
       np.mean(np_stats_calculator), np.std(np_stats_calculator), \
       (100.0 * np.std(np_stats_calculator)) / np.mean(np_stats_calculator)))

    # Collect this data for generating the box plot.
    box_plot_data.append(sorted_data_values)


  fig1, ax1 = plt.subplots()
  ax1.set_title(data_label)
  ax1.boxplot(box_plot_data, labels=hardware_channel_num, showmeans=True, showfliers=True)
  plt.ylabel('Value read on channel')
  plt.xlabel('Channel number (on ADC board)')
  plt.grid(True)

  # Save plot to file
  fq_file_path = "%s/%s" % (args.output_dir, generate_filename(data_label))
  plt.savefig(fq_file_path)
  print("\n")

print("See boxplots generated here: %s\n" % args.output_dir)

header_row = "%-25s %25s %7s %15s %8s %8s %8s %8s %8s" % \
            ("Label", "Metric", "HW chan", "DataPt", "Min", "Max", "Mean", "StdDev", \
             "percentDev")
print("%s\n%s" % (label_format, header_row))
for result in statistics_results:
  label, metric, hw_chan, dp_count, min_val, max_val, mean, stddev, percent_dev = result
  print("%-25s %25s %7d %15d %8d %8d %8.1f %8.02f %8.02f" % \
        (label, metric, hw_chan, dp_count, min_val, max_val, mean, stddev, percent_dev))
