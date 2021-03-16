'''
the following import is only necessary because eip is not in this directory
'''
import sys
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

meltTemperature = comm.Read('meltTemperature')
screwSpeed = comm.Read('screwSpeed')
lineSpeed = comm.Read('lineSpeed')

print(meltTemperature.Value)
print(screwSpeed.Value)
print(lineSpeed.Value)
comm.Close()
