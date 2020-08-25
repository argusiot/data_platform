'''
   helpers.py

   Collection of helper routines for machine analytics testing.
'''

def power_only_on_state_url():
    return "http://172.1.1.1:4242/api/query?start=1234510&end=1234570" \
              "&m=none:machine.sensor.dummy_machine_powerOn_stat"
              "{machine_name=90mm_extruder}"
