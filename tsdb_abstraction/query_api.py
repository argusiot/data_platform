'''
  API for Argus Data Platform queries. 

  This API is to be used by applications that are developed for using the ADP.
  
  Current status: Proposed API
  (Possible statuses: Reviewed | Experimental Use | Accepted)
'''

from enum import Enum

class AggregateLevel(Enum):
  NONE,  # 
  PER_PARAMETER,
  
class TsdbPlatform(Enum):
  OPENTSDB = 1
  PROMETHEUS = 2
  METRICTANK = 3
  

Class TSDBQueryApi(object):
  def __init__(self, tsdb_platform=OPENTSDB):
    self.__tsdb_platform = tsdb_platform
  pass

  '''
    metric_name:
      Fully qualified name of the metric e.g. machine.sensor.melt_temperature.

    tag_value_pair:
      A dictionary of tags and values to identify a specific timeseries. No wild
      carding for value is permitted. 
  '''
  def get_timeseries_data(metric_name, tag_value_pairs, start_time, end_time):
    pass

  

  '''
     metric_name_set = {melt_temp, line_speed, screw_speed,....}
     This will ensure all the timestamp alignment of data for different timeseries
     is done by the TSDB layer.

     STUDY NOTES:
       (1) If the timeseries are based off different metrics, can we still
           guarantee a value for each timestamp.  .....PARAG TO INVESTIGATE.

        Input: {metric1, metric2, metric3, metric4}
     Return:
        { v1:
            'timestamp1' = [val1, val2, val3, val4]
            'timestamp2' = [val1, val2, val3, val4]
            'timestamp3' = [val1, val2, val3, val4]
            'timestamp4' = [val1, val2, val3, val4]
            'timestamp5' = [val1, val2, val3, val4]
            ...
        }

        
     foo =  {v2:
           {'metric1' :  {  # metric1
                           timestamp1: val1,
                           timestamp2: val,
                           timestamp3: val,
                           timestamp4: val,
                           ...
                          },
            {metric2 :   {  # metric2
                               timestamp1: val1,
                               timestamp2: val,
                               timestamp3: val,
                               timestamp4: val,
                               ...
                            },
                            {  # metric3
                               timestamp1: val1,
                               timestamp2: val,
                               timestamp3: val,
                               timestamp4: val,
                               ...
                            },
                            {  # metric4
                               timestamp1: val1,
                               timestamp2: val,
                               timestamp3: val,
                               timestamp4: val,
                               ...
            },
        }
      }
     }
  '''
  def get_timeseries_data_set(metric_name_set, tag_value_pairs_set, start_time, end_time):
    pass
