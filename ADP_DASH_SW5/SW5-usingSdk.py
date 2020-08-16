#!/usr/bin/python3
from builtins import print

from argus_tal import query_api
from argus_tal import timeseries_id as ts_id
from argus_tal import timestamp as ts
from argus_tal import basic_types as bt
from argus_tal.timeseries_datadict import LookupQualifier as LQ

TotalTimeOn = 0
TotalTimeOff = 0
TotalReadyTime = 0
TotalPurgeTime = 0

def getTimeSeriesData(timeseries_id, start_timestamp, end_timestamp,flag_compute_rate=False):

    foo = query_api.QueryApi(
        "34.221.154.248", 4242,
        start_timestamp, end_timestamp,
        [timeseries_id],
        bt.Aggregator.NONE,
        flag_compute_rate,
        )

    rv = foo.populate_ts_data()
    assert rv == 0

    result_list = foo.get_result_set()
    assert len(result_list) == 1

    # for result in result_list:
    #     for kk, vv in result:
    #         print("\t%s->%d" % (kk, vv))
    return result_list[0]

def createPowerStateList():
    Startkey = 0
    EndKey = 0
    StartValue = 0
    stateList = []
    #Timeseries ID for powerstate calulation, should be passed by caller
    timeseries_id = ts_id.TimeseriesID("machine.sensor.dummy_machine_powerOn_stat",
                                       {"machine_name": "90mm_extruder"})
    #Primary start and end time stamps, should be provided by the caller.
    start_timestamp = ts.Timestamp(1587947403)
    end_timestamp = ts.Timestamp(1587949197)

    result = getTimeSeriesData(timeseries_id, start_timestamp, end_timestamp)

    #Below block traverses the result and forms tuple of start and end timestamps with powerstate
    i=0
    for k, v in result:
        if i == 0:
            Startkey = k
            StartValue = v
        elif i == len(result) - 1:
            EndKey = k
            stateList.append(tuple((Startkey, EndKey, StartValue)))
        elif v == result.get_datapoint(k, LQ.NEAREST_SMALLER)[1]:
            # print(k,v,result.get_datapoint(k, LQ.NEAREST_SMALLER)[0],result.get_datapoint(k, LQ.NEAREST_SMALLER)[1])
            i += 1
            continue
        else:
            EndKey = result.get_datapoint(k, LQ.NEAREST_SMALLER)[0]
            stateList.append(tuple((Startkey, EndKey, StartValue)))
            Startkey = k
            StartValue = v
        i += 1

    # print(stateList)
    return stateList

#Uses powestate tuples and calculates overall timeon and timeoff 
def calculateTotalTimeOnOff(stateList):
    global TotalTimeOn
    global TotalTimeOff
    for entry in stateList:
        if entry[2] == 0.0:
            TotalTimeOff += (entry[1]) - (entry[0])
        elif entry[2] == 1.0:
            TotalTimeOn += (entry[1]) - (entry[0])
    print(TotalTimeOff)
    print(TotalTimeOn)


def calculateTotalReadyTime(stateList):
    global TotalReadyTime
    #MeltTemperatre timeseries ID should be provided by caller
    timeseries_id = ts_id.TimeseriesID("machine.sensor.dummy_melt_temperature", \
                                       {"machine_name": "90mm_extruder"})
    for entry in stateList:
        if entry[2] == 1.0: #Checks the power state list and if in ON state proceeds
            start_timestamp = ts.Timestamp(entry[0])
            end_timestamp = ts.Timestamp(entry[1])
            rate = getTimeSeriesData(timeseries_id,start_timestamp,end_timestamp,flag_compute_rate=True)

            StartTime = 0
            for k,v in rate:
                if v < -1 or v > 1: #Rate is considered stable if within -1 and +1 so result set is checked
                    if StartTime != 0:
                        TotalReadyTime += rate.get_datapoint(k, LQ.NEAREST_SMALLER)[0] - StartTime #Rate out of range stop and add time to total ready time
                        StartTime = 0
                elif 1 > v > -1: #Rate in range proceed to next datapoint
                    if StartTime == 0:
                        StartTime = k
                    elif k == rate.get_max_key() and StartTime != 0: #rate in range throught dataset so add time on the last entry
                        TotalReadyTime += rate.get_datapoint(k, LQ.NEAREST_SMALLER)[0] - StartTime
    print(TotalReadyTime)


def calculateTotalPurgeTime(stateList): #linespeed zero, screw speed non-zero
    global TotalPurgeTime
    #LineSpeed timeseries ID should be provided by caller
    timeseries_id = ts_id.TimeseriesID("machine.sensor.dummy_line_speed", \
                                       {"machine_name": "90mm_extruder"})
    for entry in stateList:
        if entry[2] == 1.0: #Checks if machine state is on
            start_timestamp = ts.Timestamp(entry[0])
            end_timestamp = ts.Timestamp(entry[1])
            data = getTimeSeriesData(timeseries_id, start_timestamp, end_timestamp)

            Startkey = 0
            EndKey = 0
            tempStateList = []
            purgeStart = 0
            i=0
            for k, v in data:
                if i == len(data) and Startkey != 0: #if whole dataset has zero line speed, create tuple at last value
                    EndKey = k
                    tempStateList.append(tuple((Startkey, EndKey)))
                    Startkey = 0
                elif v < 1000 and Startkey == 0: #LineSpeed is considered zero if lesser than 1000(job parameter) so need to find that
                    Startkey = k
                elif v < 1000 and Startkey != 0: #If speed zero, continue
                    i += 1
                    continue
                elif v > 1000 and Startkey != 0: #If speed non zero, stop and make a tuple with start and end
                    EndKey = data.get_datapoint(k, LQ.NEAREST_SMALLER)[0]
                    tempStateList.append(tuple((Startkey, EndKey)))
                    Startkey = 0
                i += 1
            
            #ScrewSpeed timeseries ID should be provided by caller
            screw_timeseries_id = ts_id.TimeseriesID("machine.sensor.dummy_screw_speed", \
                                               {"machine_name": "90mm_extruder"})

            for entry in tempStateList: #check screwspeed at all intervals for every tuple created above
                start_timestamp = ts.Timestamp(entry[0])
                end_timestamp = ts.Timestamp(entry[1])
                screwdata = getTimeSeriesData(screw_timeseries_id, start_timestamp, end_timestamp)
                for k,v in screwdata:
                    if 20 <= v <= 200: #If screw speed is non zero and in range (Values needs to discussed!!)
                        continue
                    else: 
                        tempStateList.remove(entry) #If screwspeed not in range remove the tuple entry
                        break

            melt_timeseries_id = ts_id.TimeseriesID("machine.sensor.dummy_melt_temperature", \
                                               {"machine_name": "90mm_extruder"})
            #after pruning the tuple need to check if melt temprature has reached stable set values
            for entry in tempStateList:
                start_timestamp = ts.Timestamp(entry[0])
                end_timestamp = ts.Timestamp(entry[1])
                meltdata = getTimeSeriesData(melt_timeseries_id, start_timestamp, end_timestamp)

                for k,v in meltdata:
                    if v > 160 or v < 147: #Stable target temperature, provided by caller (JOB Parameters)
                        if purgeStart != 0:
                            TotalPurgeTime += meltdata.get_datapoint(k, LQ.NEAREST_SMALLER)[0] - purgeStart
                            purgeStart = 0
                    elif 147.0 <= v <= 160.0:
                        if purgeStart == 0:
                            purgeStart = k
                        elif k == meltdata.get_max_key() and purgeStart != 0:
                            TotalPurgeTime += meltdata.get_datapoint(k, LQ.NEAREST_SMALLER)[0] - purgeStart
    print(TotalPurgeTime)




def main():
    stateList = createPowerStateList()
    calculateTotalTimeOnOff(stateList)
    calculateTotalReadyTime(stateList)
    calculateTotalPurgeTime(stateList)



# if __name__ == "__main__":
#   # execute only if run as a script
main()


