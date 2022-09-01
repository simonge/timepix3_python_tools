#  ------------------------------------------------------------------------------------- 
#  "hits.py" - Contains functions to convert discriminator pulses associated with a
#              sequence of hits on the same pixel to Timepix3  pixel counter values                        
#  -------------------------------------------------------------------------------------
#
#  Timepix3 detection events are based on the discriminator: each rising edge of the 
#  discriminator corresponds to a "hit" and each falling edge signals the end of that hit. 
#  As outlined in Sections 2.1.2, 2.1.9 of the Timepix3 Manual v1.9, not all hits are 
#  accepted. 
#
#
#  This file provides functionality to convert discriminator pulses to pixel counter values
#  for a series of hits ON THE SAME PIXEL. Each hit in the pulse is either accepted or
#  rejected and then, based on the operation mode (ToA & ToT mode or ToA Only; superpixel 
#  VCO enabled in either case), appropriate pixel counter values for each of the hits in
#  the sequence are returned. The key function for this is "discr_to_data()".
#
#
#  The data handling of discriminator pulses, denoted "discr", in this file is as 
#  follows: A discriminator pulse is an array of timing information with an even number of 
#  entries. The "2i"th entry of the array is the start time of the "i"th hit while the 
#  "2i+1"th entry is the end time of the same hit ("i"being an integer index starting at 0).
#  The data handling of the output (that is, pixel counter values) is solved using Pandas
#  DataFrames.
#
#
#  This file requires numpy and pandas as well as functions from "counters.py"
#  and "time_conversion.py".
#
#
#
#  Some open problems that are yet to be addressed by the code:
#         
#         1. While Section 2.1.2 of the Manual only list minimum pulse width
#            and pixel dead time as reasons for hit acceptance/rejection, later 
#            sections suggest that other factors, like readout and shutter values,
#            are also relevant. This is not accounted for in the code below, which 
#            assumes that the given equation for pixel dead time includes these
#            factors.
#           
#
#
#
#                                                                    David Amorim, 2022


# import modules and functions
import numpy as np
import pandas as pd
from timepix3.time_conversion import time_to_values, time_to_tot
from timepix3.counters import counter_decode


# returns pixel dead time after a hit with given ToT: 
#       (see Timepix3 Manual v1.9 Section 2.1.9)

def dead_time(tot, op_mode=0, clk_speed=40e6):
    
    tot_decoded=counter_decode(tot, 'tot')
    
    if (op_mode==0):
        deadtime= (19 + tot_decoded) / clk_speed
    elif (op_mode==1):
        deadtime= (19) / clk_speed    
    elif (op_mode==10) | (op_mode==2):
        deadtime= (3 + tot_decoded) / clk_speed
   
    return deadtime  


# for a series of hits, determines whether to accept or reject each hit
#        (returns original array with rejected hits set to zero)
#
#        NOTE: solely based on mimimum pulse width and maximum hit rate
#               (see Comment 1. above)

def accept_or_reject(discr, op_mode=0):
    
    # set up variables: 
    prev_tot=0     # value of previous ToT measurement
    prev_pulse=0   # end time of previous pulse
    
    # loop through contents of array
    for i in np.arange(0, len(discr),2):
    
        # check if hit has minimum length (ToT >= 1):
        tot=counter_decode(time_to_tot(discr[i],discr[i+1]), 'tot')
        if tot < 1:
            discr[i]=0
            discr[i+1]=0
        
        # check if too close to previous accpted hit (if there has been one):
        dtime=discr[i]-prev_pulse
        if (dtime < dead_time(prev_tot,op_mode=op_mode)) & (prev_pulse != 0):
            discr[i]=0
            discr[i+1]=0
            
        # if accepted, update previous hit values:
        if (discr[i] !=0) & (discr[i+1] !=0):
            prev_tot=time_to_tot(discr[i], discr[i+1])
            prev_pulse=discr[i+1]
      
    # return array with rejected hits set to zero 
    return discr


# read in discriminator data and pixel address and return encoded pixel counter values for each 
# accepted hit:

def discr_to_data(discr,addr, op_mode=0):
    
    # reject or accept hits:
    discr=accept_or_reject(discr, op_mode)
             
    # ToA & ToT mode with superpixel VCO enabled:
    if (op_mode==0):
        
        # set up data frame
        df=pd.DataFrame(columns=['addr','toa','tot','ftoa'])
        
        # loop through hits:
        for i in np.arange(0,len(discr),2):
            
            # compute counter values for accepted hits
            if ((discr[i]==0) & (discr[i+1]==0)) ==False:
                toa, tot, ftoa=time_to_values(discr[i],discr[i+1], op_mode=op_mode)
                
                # add values to data frame
                row={'addr': addr,'toa': toa, 'tot': tot, 'ftoa': ftoa }
                df=df.append(row, ignore_index=True)
         
        return df

    # ToA Only mode with superpixel VCO enabled:
    if (op_mode==1):
        
        # set up data frame
        df=pd.DataFrame(columns=['addr','toa','dummy','ftoa'])
        
        # loop through hits:
        for i in np.arange(0,len(discr),2):
            
            # compute counter values for accepted hits
            if ((discr[i]==0) & (discr[i+1]==0)) ==False:
                toa, dummy, ftoa =time_to_values(discr[i],discr[i+1], op_mode=op_mode)
                
                # add values to data frame
                row={'addr':addr,'toa': toa, 'dummy': 0, 'ftoa': ftoa }
                df=df.append(row, ignore_index=True)
        
        return df
