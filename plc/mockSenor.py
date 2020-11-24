'''
the following import is only necessary because eip is not in this directory
'''
import sys
from time import sleep
from random import uniform
sys.path.append('..')


'''
The simplest example of reading a tag from a PLC
NOTE: You only need to call .Close() after you are done exchanging
data with the PLC.  If you were going to read in a loop or read
more tags, you wouldn't want to call .Close() every time.
'''
from pylogix import PLC

comm = PLC()
comm.IPAddress = '127.0.0.1'

while True:
	comm.Write('meltTemperature',uniform(55.0, 100.0))
	comm.Write('screwSpeed',uniform(25.0, 50.0))
	comm.Write('lineSpeed',uniform(35.0, 70.0))
	sleep(5)

# ret = comm.Read('scada')
# print(ret.Value)
comm.Close()
