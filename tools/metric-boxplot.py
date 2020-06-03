#!/usr/bin/python
'''
   Usage: ./metric-boxplot.py <out-put-dir>
   Example usage: ./metric-boxplot.py /vagrant/boxplots/

   FIXME: Add elaborate notes explainining what is happening here !!
'''

import argparse
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from metric_query import get_data_set
import sys
import numpy as np

# These values come from:
# https://docs.google.com/document/d/1gE8gTbTKHgaSs3BjsOmuH920oyZDiPX0nw-zpAyvgsw/edit#
#  Format:
#    data set name -> [time window]
#  The box plot file name is derived from the data set name by replacing space
#  with underscore.
test_time_windows = { \
  "NCD power supply noise" : [1590266436000, 1590531327000],
  "NCD power supply 12 mA" : [1590535460459, 1590795803317],
  "NCD power supply 4 mA" : [1590797194095, 1591054653037],
  "NCD power supply 20 mA" : [],
}

''' Leaving it here it so it can be enabled for a quick test of the logic !!
test_time_windows = { \
  "NCD power supply noise" : ["2m-ago", "1m-ago"],
  "NCD power supply 12 mA" : ["2m-ago", "1m-ago"],
  "NCD power supply 4 mA" : ["2m-ago", "1m-ago"],
  "NCD power supply 20 mA" : [],
}
'''


def generate_filename(timewindow_id):
  return timewindow_id.replace(" ", "_")

machine_name="65mm_extruder"
parser = argparse.ArgumentParser(description="Tool to generate box plot for" \
   " all metrics of %s" % machine_name)
parser.add_argument("output_dir", help="Location to save the generated boxplots")
args = parser.parse_args()

# List of metrics to process. This is fixed for the 65mm_extruder
# machine. This can be easily generalized later.
metric_list = ["raw_melt_temperature", "raw_melt_pressure", "raw_screw_speed", \
               "raw_line_speed", "raw_barrel_temperature_1", \
               "raw_barrel_temperature_2", "raw_machine_powerOn_state", \
               "raw_wire_output_diameter"] 
metric_labels = [8, 7, 6, 5, 4, 3, 2, 1]
url_template="http://34.221.154.248:4242/api/query?start=%s&end=%s&m=none:machine.sensor.%s{machine_name=%s}"

# Format:
# (label_str, total_cnt, Min, Max, Mean, StdDev, %age-std-dev)
statistics_results = []

for time_window_id, window_range in test_time_windows.items():
  print "Processing Label '", time_window_id, "' -- ",
  if len(window_range) > 0:
    print("Time window: (%s, %s)" % (window_range[0], window_range[1]))
  else:
    print("Skipping\n")
    continue

  # A place to collect the results returned for each metric query.
  box_plot_data = []
  for metric_id in metric_list:
    url = url_template % (window_range[0], window_range[1], \
                          metric_id, machine_name)
    print(url)
    sorted_data_values = get_data_set(url).values()  # Extract list of values
                                                     # from the returned dict.
    sorted_data_values.sort()                        # ...and sort the list.
    
    # Calculate statistics for the data received and store in the stats result.
    np_stats_calculator = np.array([sorted_data_values])
    statistics_results.append( \
      (time_window_id, len(sorted_data_values), sorted_data_values[0], \
       sorted_data_values[len(sorted_data_values) - 1], 
       np.mean(np_stats_calculator), np.std(np_stats_calculator), \
       (100.0 * np.std(np_stats_calculator)) / np.mean(np_stats_calculator)))

    # Collect this data for generating the box plot.
    box_plot_data.append(sorted_data_values)

  fig1, ax1 = plt.subplots()
  ax1.set_title(time_window_id)
  ax1.boxplot(box_plot_data, labels=metric_labels, showmeans=True, showfliers=True)
  fq_file_path = "%s/%s" % (args.output_dir, generate_filename(time_window_id))
  plt.savefig(fq_file_path)
  print("\n")

print("See boxplots generated here: %s\n" % args.output_dir)

print("\tLabel\t\t\tDataPts\t\tMin\t\tMax\t\tMean\t\tStdDev\t\t%ageDev")
for result in statistics_results:
  label, dp_count, min_val, max_val, mean, stddev, percent_dev = result
  print("%s\t\t%d\t\t%d\t\t%d\t\t%0.1f\t\t%.02f\t\t%.02f" % \
        (label, dp_count, min_val, max_val, mean, stddev, percent_dev))
