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
  

'''
  Qualifies the timestamp parameter (key) being supplied. The API knows
  how to use the timestamp value based on the LookupParamQualifier supplied.

   e.g. data set: timestamp->value
                  12345->10
                  12350->20
                  12365->30
  
        ts_obj.get_datapoint(12350, EXACT_MATCH) returns 20
        ts_obj.get_datapoint(12351, EXACT_MATCH) returns None

        ts_obj.get_datapoint(12348, NEAREST_SMALLER_STRICT) returns 10
Exact-> ts_obj.get_datapoint(12345, NEAREST_SMALLER_STRICT) returns None
OOB->   ts_obj.get_datapoint(12340, NEAREST_SMALLER_STRICT) returns None

        ts_obj.get_datapoint(12352, NEAREST_LARGER_STRICT) returns 30
Exact-> ts_obj.get_datapoint(12365, NEAREST_LARGER_STRICT) returns None
OOB->   ts_obj.get_datapoint(12367, NEAREST_LARGER_STRICT) returns None

        ts_obj.get_datapoint(12348, NEAREST_SMALLER_WEAK) returns 10
Exact-> ts_obj.get_datapoint(12345, NEAREST_SMALLER_WEAK) returns 10
OOB->   ts_obj.get_datapoint(12340, NEAREST_SMALLER_WEAK) returns 10

        ts_obj.get_datapoint(12352, NEAREST_LARGER_WEAK) returns 30
Exact-> ts_obj.get_datapoint(12365, NEAREST_LARGER_WEAK) returns 30
OOB->   ts_obj.get_datapoint(12367, NEAREST_LARGER_WEAK) returns 30
'''
class LookupParamQualifier(Enum):
  # Treat the timestamp as an exact match key.
  EXACT_MATCH = 1

  # First check if an exact match exists, if found, return it.
  # If no exact match is found, then return the nearest element smaller (larger)
  # than the supplied timestamp.
  NEAREST_SMALLER = 2
  NEAREST_LARGER = 3

  # First check if an exact match exists, if found, return it.
  # If no exact match is found, then return the nearest element smaller (larger)
  # than the supplied timestamp.
  # If supplied timestamp is smaller (larger) than the smallest (largest) time
  # stamp in the data set i.e. nothing smaller (larger) is found (and we know
  # there's no exact match), then return the actual smallest (largest) element
  # from the dataset. 
  NEAREST_SMALLER_WEAK = 4
  NEAREST_LARGER_WEAK = 5

'''
  Stores timeseries data returned from a query.

  Data is stored ordered by time.

  Accessor APIs:
    get_identifier()
      Returns the metadata that idenfities the timeseries i.e the following
      pair - (metric_id, tag_value_pair_dict)

    get_keys()
      Returns a reference to a list of all keys ordered by timestamp. Well
      suited to use if you want to iterate over the entire time series.

    get_key_slice(timestamp1, lookup_qualifier1, timestamp2, lookup_qualifier2)
      Returns a slice of the key space ordered by timestamp. The slice is
      bounded by timestamp1 & timestamp2. The qualifiers determine exactly how
      to carve up the slice.

    get_datapoint(timestamp, lookup_qualifier)
      Returns pair (timestamp, data_point) corresponding to the supplied
      timestamp depending upon lookup_qualifier. See documentation above
      LookupParamQualifier for details.

    get_first_datapoint()
    get_last_datapoint()
      Returns pair (timestamp, data_point) corresponding to the first (last)
      data point in the timeseries.

    is_empty()
      Returns True if timeseries is empty, False otherwise.

  Usage idioms:
  ============
    1. Full timeseries iteration:
       --------------------------
       To iterate in ascesnding order using keys from the object:
       keys = ts_obj.get_keys()
       for timestamp in keys:
         (ts, value) = ts_obj.get_datapoint(timestamp, EXACT_MATCH)
         # process value
         # ...

    2. Getting datapoint at an arbitrary timestamp:
       --------------------------------------------
       Given a 'timestamp' if you're not sure whether the datapoint exists in
       the timeseries object, use this:
          
       (a) To get the datapoint at a time value just larger than 'timestamp':
       (new_ts, value) = ts_obj.get_datapoint(timestamp, NEAREST_LARGER)
       if value != None:
         # Use value
       else:
         # We got None for value means that the timestamp we supplied is larger
         # than the largest. Decide what we want to do !

       (b) To get the datapoint at a time value just smaller than 'timestamp':
       (new_ts, value) = ts_obj.get_datapoint(timestamp, NEAREST_SMALLER)
       if value != None:
         # Use value
       else:
         # We got None for value means that the timestamp we supplied is smaller
         # than the first value, so lets . By changing to WEAK
         (new_ts, value) = ts_obj.get_last_datapoint()

     3. Slice retrieval and processing :
        --------------------------------
        Given a pair of timestamps get a slice of timestamps. We dont want to
        this *ever* fail thus keeping error handling simple.

        if ts_obj.is_empty():
          # return error.

        time_slice = ts_obj.get_key_slice(timestamp1, NEAREST_SMALLER_WEAK,
                                          timestamp2, NEAREST_LARGER_WEAK)
        for timestamp in time_slice:
         (ts, value) = ts_obj.get_datapoint(timestamp, EXACT_MATCH)
'''
class TimeseriesData(object):
  pass


'''
1. Input:
   1a) a FQ timeseries (metric_id + tags).
       No '*' permitted in request.
   1b) qualifiers e.g. rate
   1c) Query sets aggregation by 'none'.
2. Convert each timeseries from the response to into a collection of
   TimeseriesData objects.
'''
Class QueryApi(object):
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
  def populate_timeseries_data(metric_name, tag_value_pairs, rate_or_actual,
                               start_time, end_time):
    pass

  
  ##############################################################################
  ## PARAG TO INVESTIGATE NEED AND SEMANTICS FOR populate_timeseries_set().
  ##############################################################################

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
  def populate_timeseries_set(metric_name_set, tag_value_pairs_set, start_time, end_time):
    pass
