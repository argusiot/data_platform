from time import sleep
import snap7
from snap7.util import *

plc = snap7.client.Client()
plc.connect('127.0.0.1',0,1)

InputArea = 0x81 # srvAreaPE

start = 0
length = 4

readValue=plc.read_area(InputArea,0,start,length)

print "Area=PE, [0,4]={}".format(get_real(readValue,0))

plc.disconnect()