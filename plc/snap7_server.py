import  snap7 
import  time

server = snap7.server.Server() 
size = 10

inputs = (snap7.snap7types.wordlen_to_ctypes[snap7.snap7types.S7WLByte ]*size)()

server.register_area(snap7.snap7types.srvAreaPE, 0 , inputs)

server.start () 

snap7.util.set_real(inputs, 0 , 3.234)

while  True : 
    while  True : 
        event = server.pick_event() 
        if  event : 
            print(server.event_text(event)) 
        else : 
            break 
        time.sleep(1) 
server.stop() 
server.destroy()