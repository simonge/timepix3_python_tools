#  ------------------------------------------------------------------------------------- 
#  "time_conversion.py" - Contains functions to convert between single-hit timing 
#                         information and ToA, ToT, fToA for Timepix3 
#  -------------------------------------------------------------------------------------
#
#  As described in section 2.1 of the Timepix3 Manual v1.9, discriminator pulse timing
#  information is converted to a detection time stamp (ToA, fToA) and time-over-threshold (ToT)
#  value. The functions in this file enable that conversion for a single hit in a single pixel.
#  Note that it is assumed that the hit is accepted (see Section 2.1.4 of the Manual for 
#  information on hit acceptance and rejection).
#  
#
#  A discriminator pulse is described in terms of two time variables: "start" (the time at
#  which the discriminator goes high) and "stop" (the time at which it goes low). These times
#  are specified relative to some external clock. The time, relative to the external clock,
#  at which the ToA timestamp starts is the "epoch" (set to 0 by default, see Comment 2. below).
#
#
#  Key functions are "time_to_values()" and "values_to_time()" which convert between timing 
#  information and ENCODED pixel counter values.
#
#
#
#  This files requires numpy as well as functions from "counters.py".
#
#
#
#  Some open problems that are yet to be addressed by the code:
#
#         1. The Manual mentions synchronising the discriminator (e.g. Section 2.1.4) but gives no
#            information on what that means in practise. The functions in this file do not take 
#            synchronisation into account.
#
#         2. The epoch of the global ToA counter is not specified in the Manual. It might 
#            be linked to the time at which data acquisition is started. In the code below the variable
#            "epoch" is set to zero by default but functionality for a non-zero or even changing epoch
#            is provided.  
#
#         3. The timestamp range is limited to 0.4096 ms (Table 1 in Manual). It is unclear what happens 
#            to the timestamp counter once this range is exceeded (does it reset?). Since there is no
#            overflow control on the ToA counter the code below will still return results if time values
#            outside the timestamp range are given. These results might not accurately reflect the values
#            returned by Timepix3 in that context, however.
#        
#
#
#                                                                    David Amorim, 2022


# import modules

import numpy as np
from counters import counter_encode, counter_decode


# returns ToA timestamp associated with a point in time:
#   (defined as the number of rising system clock edges 
#    since epoch at time of detection) 

def time_to_toa(time, clk_speed=40e6, epoch=0):
    
    # clock resolution:
    res=1/clk_speed
    
    # clock ticks since epoch:
    if (time-epoch) % res ==0:
        ticks=int((time-epoch) // res)
    else:
        ticks=int((time-epoch) // res + 1) 
    
    # encrypt counter value
    toa=counter_encode(ticks, 'ToA')
    
    return toa


# returns point in time associated with ToA timestamp 
#      (resolution limited to 25ns;
#       range limited to 0.4096 ms)

def toa_to_time(toa, clk_speed=40e6, epoch=0):
    
    # decode encrypted counter
    ticks=counter_decode(toa, 'toa')
    
    # convert to timing information (limited resolution)
    time=epoch + ticks / clk_speed
    
    return time


# returns fToA timestamp associated with point in time:
#    (defined as number of rising ftoa-clock edges between 
#     hit and next rising system-clock edge)

def time_to_ftoa(time, clk_speed_1=40e6, clk_speed_2=640e6, epoch=0):
    
    # determine time of last system clock tick
    res= 1/clk_speed_1
    last_tick= epoch + res*( (time-epoch) // res )
        
    # determine time of next system clock tick
    next_tick=last_tick + res
    
    # determine ftoa clock ticks in the mean time (ftoa clk starts ticking at hit)
    ftoa_res = 1/ clk_speed_2
    ftoa_ticks=int( (next_tick - time) // ftoa_res )
    
    # encode counter
    ftoa=counter_encode(ftoa_ticks, 'ftoa')
    
    return ftoa


# returns point in time associated with fToA and ToA timestamps
#        (resolution limited to 1.56ns)

def ftoa_and_toa_to_time(ftoa, toa, clk_speed_1=40e6,clk_speed_2=640e6, epoch=0):
    
    # decode counter
    ftoa_ticks=counter_decode(ftoa, 'ftoa')
    
    # convert to timing information (resolution limited)
    time= toa_to_time(toa, clk_speed_1, epoch) - ftoa_ticks / clk_speed_2
    
    return time


# returns ToT for a hit of given start and end times:
#     (defined as number of rising system clock edges 
#      while the discriminator is up)

def time_to_tot(start, stop, clk_speed=40e6, epoch=0):
    
    # number of rising clock edges during signal
    res= 1/ clk_speed
    initial_ticks= (start - epoch) // res
    final_ticks= (stop - epoch) // res
    ticks=int( final_ticks- initial_ticks) 
    
    # encode counter
    tot=counter_encode(ticks, 'ToT')
    
    return tot


# returns start and end time of hit from ToT, ToA (and fToA);
#      (resolution limited as above)

def tot_and_toa_to_time(tot, toa, ftoa=0, clk_speed_1=40e6, clk_speed_2=640e6, epoch=0):
    
    # get start time of hit from ToA and fToA
    if ftoa:
        start=ftoa_and_toa_to_time(ftoa, toa, clk_speed_1,clk_speed_2, epoch)
    else:
        start=toa_to_time(toa, clk_speed_1, epoch)
        
    # get end time of hit from start time and ToA 
    ticks=counter_decode(tot, 'ToT')
    stop= start + ticks / clk_speed_1
    
    return start, stop

# # # # # # # # # # # # # # # # # # # # FINALISED FUNCTIONS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# convert hit timing information to ToA, ftoA, ToT
#   (if op_mode=1, corresponding to ToA-Only mode, 
#    a dummy value is returned for ToT)

def time_to_values(start, stop, op_mode=0):
    
    toa=time_to_toa(start)
    ftoa=time_to_ftoa(start)
    tot=time_to_tot(start, stop)
    
    if op_mode==0:
        return toa, tot, ftoa
    if op_mode==1:
        return toa, 0, ftoa
    
# convert encoded ToA, ftoA, ToT values to hit timing information    
    
def values_to_time(toa, ftoa, tot):
    
    start, stop =tot_and_toa_to_time(tot, toa, ftoa)
    
    return start, stop