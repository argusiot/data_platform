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
import numpy as np
import sys
from metric_query import get_data_set
from collections import OrderedDict

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
'''
test_data_src = OrderedDict()
label_format="Label format: <power_src> <ADC board> <sampling resolution> <input_signal>"
# NCD powered at 12bit resolution
test_data_src["NCD B1 12bit noise"] = ([1590266436000, 1590531327000], "65mm_extruder")
test_data_src["NCD B1 12bit 12mA"] = ([1590535460459, 1590795803317], "65mm_extruder")
test_data_src["NCD B1 12bit 4mA"] = ([1590797194095, 1591054653037], "65mm_extruder")
test_data_src["NCD B1 12bit 20mA"] = ([1591056123708, 1591195347829], "65mm_extruder")
# Meanwell powered at 12bit resolution
test_data_src["Meanwell B2 12bit noise"] = ([1590776274005, 1591121874005], "90mm_extruder")
test_data_src["Meanwell TBD 12bit 4mA"] = ([], "90mm_extruder")
test_data_src["Meanwell B1 12bit 12mA"] = ([1591253982240, 1591310984083], "65mm_extruder")
test_data_src["Meanwell TBD 12bit 20mA"] = ([], "90mm_extruder")
# Meanwell powered at 16bit resolution
test_data_src["Meanwell TBD 16bit noise"] = ([], "")
test_data_src["Meanwell TBD 16bit 4mA"] = ([], "")
test_data_src["Meanwell TBD 16bit 12mA"] = ([], "")
test_data_src["Meanwell TBD 16bit 20mA"] = ([], "")

''' Leaving it here it so it can be enabled for a quick test of the logic.
    NOT TO BE USED FOR ACTUAL DATA RUN  !!
test_data_src["NCD B1 12bit noise"] = (["2m-ago", "1m-ago"], "65mm_extruder")
test_data_src["NCD B1 12bit 12mA"] = (["2m-ago", "1m-ago"], "65mm_extruder")
test_data_src["NCD B1 12bit 4mA"] = (["2m-ago", "1m-ago"], "65mm_extruder")
test_data_src["NCD B1 12bit 20mA"] = (["2m-ago", "1m-ago"], "65mm_extruder")
'''


def generate_filename(timewindow_id):
  return timewindow_id.replace(" ", "_")

parser = argparse.ArgumentParser(description="Tool to generate box plot for" \
   " all 8 channels of extruder machine")
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

for data_label, (time_window, machine_name) in test_data_src.items():
  
  print "Processing Label '", data_label, "' -- ",
  if len(time_window) > 0:
    print("Time window: (%s, %s)" % (time_window[0], time_window[1]))
  else:
    print("Skipping\n")
    continue

  # A place to collect the results returned for each metric query.
  box_plot_data = []
  for metric_id in metric_list:
    url = url_template % (time_window[0], time_window[1], \
                          metric_id, machine_name)
    print(url)
    sorted_data_values = get_data_set(url).values()  # Extract list of values
                                                     # from the returned dict.
    sorted_data_values.sort()                        # ...and sort the list.
    
    # Calculate statistics for the data received and store in the stats result.
    np_stats_calculator = np.array([sorted_data_values])
    statistics_results.append( \
      (data_label, metric_id, len(sorted_data_values), \
       sorted_data_values[0], sorted_data_values[len(sorted_data_values) - 1], \
       np.mean(np_stats_calculator), np.std(np_stats_calculator), \
       (100.0 * np.std(np_stats_calculator)) / np.mean(np_stats_calculator)))

    # Collect this data for generating the box plot.
    box_plot_data.append(sorted_data_values)


  fig1, ax1 = plt.subplots()
  ax1.set_title(data_label)
  ax1.boxplot(box_plot_data, labels=metric_labels, showmeans=True, showfliers=True)
  plt.ylabel('Value read on channel')
  plt.xlabel('Channel number (on ADC board)')
  plt.grid(True)

  # Save plot to file
  fq_file_path = "%s/%s" % (args.output_dir, generate_filename(data_label))
  plt.savefig(fq_file_path)
  print("\n")

print("See boxplots generated here: %s\n" % args.output_dir)

header_row = "%-25s %25s %15s %8s %8s %8s %8s %8s" % \
            ("Label", "Metric", "DataPt", "Min", "Max", "Mean", "StdDev", \
             "percentDev")
print("%s\n%s" % (label_format, header_row))
for result in statistics_results:
  label, metric, dp_count, min_val, max_val, mean, stddev, percent_dev = result
  print("%-25s %25s %15d %8d %8d %8.1f %8.02f %8.02f" % \
        (label, metric, dp_count, min_val, max_val, mean, stddev, percent_dev))
