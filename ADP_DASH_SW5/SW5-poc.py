from json import loads
from collections import OrderedDict

'''
TDB:
1. Using Enums for power state.
2. Storing Power states in tuples power_state_summary.
3. Making direct Http calls instead of files.
4. Passing maps between functions instead of refrences.
5. Rename Variables.
'''

# read file
with open('data.json', 'r') as dataFile:
    data=dataFile.read()

status = loads(data, object_pairs_hook=OrderedDict)
#status = {long(k):float(v) for k,v in status.items()}

with open('rate.json', 'r') as rateFile:
    rateData=rateFile.read()


rate = loads(rateData, object_pairs_hook=OrderedDict) # covert float
# rate = {long(k):float(v) for k,v in rate.items()}


with open('lineSpeed.json', 'r') as lineSpeedFile:
    lineSpeedData=lineSpeedFile.read()
lineSpeed = loads(lineSpeedData, object_pairs_hook=OrderedDict)

with open('screwSpeed.json', 'r') as screwSpeedFile:
    screwSpeedData=screwSpeedFile.read()
screwSpeed = loads(screwSpeedData, object_pairs_hook=OrderedDict)

with open('meltTemp.json', 'r') as meltTempFile:
    meltTempData=meltTempFile.read()
meltTemp = loads(meltTempData, object_pairs_hook=OrderedDict)

TotalTimeOn = 0
TotalTimeOff = 0
TotalReadyTime = 0
TotalPurgeTime = 0


#Assumation in range and out of range abs1
def checkIfReady(start,end):
    global TotalReadyTime 
    StartTime = 0
    i = start
    while i <= end:
        if float((rate.values()[i])) < -1 or float((rate.values()[i])) > 1: #outOfRange    check abs in range; 
            if StartTime != 0:
                TotalReadyTime += int((rate.keys()[i-1])) - StartTime
                StartTime = 0
        elif float((rate.values()[i])) < 1 and float((rate.values()[i])) > -1: #inRange
            if StartTime == 0:
                StartTime = int((rate.keys()[i]))
            elif i == end and StartTime != 0:
                TotalReadyTime += int((rate.keys()[i-1])) - StartTime

        i += 1


def checkIfPurge(start,end):
	global TotalPurgeTime
	Startkey = 0
	EndKey = 0
	stateList = []
	purgeStart = 0
	i = start
	while i <= end:
		if i == end and Startkey != 0:
			EndKey = lineSpeed.keys()[i]
			stateList.append(tuple((Startkey,EndKey)))
			Startkey = 0
		elif lineSpeed.values()[i] < 1000 and Startkey == 0:
			Startkey = lineSpeed.keys()[i]
		elif lineSpeed.values()[i] < 1000 and Startkey != 0:
			i +=1
			continue
		elif lineSpeed.values()[i] > 1000 and Startkey != 0:
			EndKey = lineSpeed.keys()[i-1]
			stateList.append(tuple((Startkey, EndKey)))
			Startkey = 0
		i +=1
	print(stateList)
	for entry in stateList:
		i = screwSpeed.keys().index(entry[0])
		end = screwSpeed.keys().index(entry[1])
		while i <= end:
			if 20<= int(screwSpeed.keys()[i]) <=200:
				continue
			else:
				stateList.remove(entry)
				break



	for entry in stateList:
		i = meltTemp.keys().index(entry[0])
		end = meltTemp.keys().index(entry[1])
		while i <= end:
			if float(meltTemp.values()[i]) > 160 or float(meltTemp.values()[i]) < 147:
				if purgeStart != 0:
					TotalPurgeTime += int((meltTemp.keys()[i-1])) - purgeStart
					purgeStart = 0
			elif 147.0 <= float(meltTemp.values()[i]) <= 160.0:
				if purgeStart == 0:
					purgeStart = int((meltTemp.keys()[i]))
				elif i == end and purgeStart != 0:
					TotalPurgeTime += int((meltTemp.keys()[i-1])) - purgeStart
			i += 1

Startkey = 0
EndKey = 0
StartValue = 0
stateList = []

for i, (k,v) in enumerate(status.items()):
    if i == 0:
        Startkey = k;
        StartValue = v;
    elif i == len(status)-1:
        EndKey = status.keys()[i]
        stateList.append(tuple((Startkey, EndKey, StartValue)))
    elif v == status.values()[i-1]:
        continue
    else:
        EndKey = status.keys()[i-1]
        stateList.append(tuple((Startkey, EndKey, StartValue)))
        Startkey = k;
        StartValue = v;


for entry in stateList:
    if entry[2] == 0.0:
        TotalTimeOff += int(entry[1]) - int(entry[0])
    elif entry[2] == 1.0:
        TotalTimeOn += int(entry[1]) - int(entry[0])
        # make query to get data.      func get Start and End data and pass map to checkRate
        checkIfReady((rate.keys().index(entry[0])), (rate.keys().index(entry[1])))
        checkIfPurge((lineSpeed.keys().index(entry[0])), (lineSpeed.keys().index(entry[1])))

print ("Total TimeOn: " + str(TotalTimeOn))
print ("Total TimeOff: " + str(TotalTimeOff))
print ("Total ReadyTime: " + str(TotalReadyTime))
print ("Total PurgeTime: " + str(TotalPurgeTime))
