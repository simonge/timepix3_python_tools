#  ------------------------------------------------------------------------------------------
#  "packing.py" - Contains functions to convert raw input data to processed bit packets and 
#                 write to an output file as well as functions to read data from output files                       
#  -------------------------------------------------------------------------------------------
#
#  Timepix3 pixel counter values are packaged in 48-bit packets. The packaging depends
#  on the acquisition mode. See Figure 1 in the Timepix3 Manual v1.9 for more details. 
#  Note that the functions in this file only support operation in ToA & ToT Mode and ToA Only Mode
#  with superpixel VCO enabled in either case.
#
#
#  This file provides functions, most importantly "raw_to_file()", to convert raw input data to 
#  to 48-bit packets and write them to a binary output file. The input data must be passed as a 
#  Pandas DataFrame with columns 'x', 'y', 'start', 'stop' containing the pixel coordinates and hit 
#  timing data.  
#  
#
#  The function "file_to_df()" allows the reading of output files and to reconstruct hit timing data
#  as well as pixel counter values from the bit packets (can be saved to file). 
#
#
#  This file requires the modules numpy, warnings, and pandas as well as functions from "counters.py", 
#  "time_conversion.py" and "hits.py"
#
#
#
#                                                                    David Amorim, 2022

# import modules
import numpy as np
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)   # surpress FutureWarnings
import pandas as pd
from os.path import getsize
from timepix3.time_conversion import tot_and_toa_to_time, ftoa_and_toa_to_time
from timepix3.counters import counter_decode
from timepix3.hits import discr_to_data


# convert x,y coordinates of pixel to address:
#     (see Section 3.3 of the Manual)
def xy_to_addr(x,y):
    
    eoc         = int(x/2)
    supr        = int(y/4)
    pix         = (y%4)+(4*(x%2))                    
    addr        = (eoc<<9) + (supr<<3) + pix 
    
    return addr

# convert pixel address to x,y coordinates:
#     (see Section 3.3 of the Manual)
def addr_to_xy(addr):
    
    pix         = addr      & 0b111                  
    supr        = (addr>>3) & 0b111111
    eoc         = (addr>>9) & 0b1111111
    x           = 2*eoc  + int(pix/4)                 
    y           = 4*supr + pix - 4*(x%2)
    
    return x,y


# take data frame with raw input (hit timing & pixel coordinate data) and convert to encoded pixel counter values
# for each hit: 
#     (works for op_mode=00/01)

def raw_to_unpacked(in_df, op_mode=0):
    
    # replace x,y columns with address data:
    x=in_df['x']
    y=in_df['y']
    addr=np.arange(len(x))
    
    for i in addr:
        addr[i]=xy_to_addr(x.iloc[i], y.iloc[i])
    
    in_df['addr']=addr
    
    in_df=in_df.drop(columns=['x', 'y'])
    
    # create empty output array
    if op_mode==0:
        out_df=pd.DataFrame(columns=['addr', 'toa', 'tot', 'ftoa'])
    elif op_mode==1:
        out_df=pd.DataFrame(columns=['addr', 'toa', 'dummy', 'ftoa'])
    
    # split input into discr for each pixel
    addr=in_df['addr']
    
    for i in np.unique(addr):
            
        hits=in_df[in_df.addr == i]
        
        start=hits['start']
        stop=hits['stop']
         
        discr=np.arange(2*len(start), dtype=float)
        
        for j in np.arange(len(start)):
            discr[2*j]= start.iloc[j]
            discr[2*j+1]=stop.iloc[j]
         
        # convert discr to counter values for each pixel:
        df=discr_to_data(discr,i, op_mode)
        out_df=out_df.append(df,ignore_index=True)
        
    # sort resulting data frame by decoded ToA:
    toa=out_df['toa']
    toa_decoded=np.arange(len(toa))
    
    for i in toa_decoded:
        toa_decoded[i]=counter_decode(toa.iloc[i],'toa')
    
    out_df['toa_raw']=toa_decoded
    out_df.sort_values(by=['toa_raw'])
    out_df=out_df.drop(columns=['toa_raw'])
    
    # return output data frame
    return out_df 


# take data frame containing encoded pixel counter values (and addresses) and write packets to binary output file:

def values_to_file(df,file, op_mode=0):
    
    # define header
    header=0b1010
    
    # get columns of data frame:
    addr=df['addr']
    toa=df['toa']
    ftoa=df['ftoa']

    if op_mode==0:
        tot=df['tot']
    elif op_mode==1:
        dummy=df['dummy']
    
    # define bit masks for packing:
    ftoaM, totM, toaM, dummy10bM, addrM, headerM     = 0b1111, 0b1111111111, 0b11111111111111,0b1111111111,0b1111111111111111,0b1111 
    
    # loop through rows of data frame and create packets using the bit masks:
    packets=np.arange(len(toa))
    for i in packets:
        if op_mode==0:
            packets[i]=((header&headerM)<<44)+((addr.iloc[i]&addrM)<<28)+((toa.iloc[i]&toaM)<<14)+((tot.iloc[i]&totM)<<4)+(ftoa.iloc[i]&ftoaM)
        elif op_mode==1:
            packets[i]=((header&headerM)<<44)+((addr.iloc[i]&addrM)<<28)+((toa.iloc[i]&toaM)<<14)+((dummy.iloc[i]&dummy10bM)<<4)+(ftoa.iloc[i]&ftoaM)
            
    # open stream to file (truncate first)
    dfile = open(file,'wb')

    # write each packet to file
    for i in np.arange(len(packets)):
        packet=int(packets[i])          
        dfile.write(packet.to_bytes(6,'big'))
    
    # close stream
    dfile.close()
    
    return 0 


# convert 48-bit packet to encoded pixel counter values in ToA & ToT Mode (op_mode=00)

def unpack_001(packet): 
    
    ftoaM, totM, toaM, addrM, headerM     = 0b1111, 0b1111111111, 0b11111111111111,0b1111111111111111,0b1111
    
    ftoa = (packet        ) & ftoaM
    tot  = (packet >>   4 ) & totM
    toa  = (packet >>  14 ) & toaM
    addr = (packet >>  28 ) & addrM
    header = (packet >>  44 ) & headerM
   
    return header,addr,toa,tot,ftoa


# convert 48-bit packet to encoded pixel counter values in ToA Only Mode (op_mode=01)

def unpack_011(packet): 
    
    ftoaM, totM, toaM, dummy10bM, addrM, headerM     = 0b1111, 0b11111111111111,0b1111111111,0b1111111111111111,0b1111
    
    ftoa      = (packet        ) & ftoaM
    dummy10b  = (packet >>   4 ) & dummy10bM
    toa       = (packet >>  14 ) & toaM
    addr      = (packet >>  28 ) & addrM
    header    = (packet >>  44 ) & headerM
   
    return header,addr,toa,dummy10b,ftoa


# read list of packets from binary output file:
#    (returns array of bit packets)

def file_to_packets(filename):
    
    # determine number of packets in file
    n=int(getsize(filename)/6)
    
    # create appropriate array to store packets
    packets=np.arange(n)
    
    # open stream to file
    dfile = open(filename,'rb')

    # read in each packet:
    for i in np.arange(n):
        data   = np.fromfile(dfile,dtype=np.byte, count=6)
        packet = int.from_bytes(data,'big')
        packets[i]=packet
    
    # close stream
    dfile.close()
   
    return packets


# convert a series of bit packets to a data frame containing the pixel counter and timing values
# for ToA & ToT Mode (op_mode=00):
# 
# ARGUMENTS:      - decode=0/1 : display decoded (=1) or encoded (=0) pixel counters
#                 - time_data=0/1:  do (=1) or do not (=0) display hit start and stop time  
#                 - binary=0/1: display counters in binary (=1) or decimal (=0) 

def packets_to_df_001(packets, decode=1, time_data=1, binary=0):

    # to provide start and stop time for each pulse:
    if time_data==1:
        
        # create data frame
        df=pd.DataFrame(columns=['x', 'y','start', 'stop', 'toa', 'tot', 'ftoa' ])
        
        # loop through bit packets
        for i in np.arange(len(packets)):
            
            # unpack each packet
            header,addr,toa,tot,ftoa = unpack_001(packets[i])
            x,y = addr_to_xy(addr)
            start, stop= tot_and_toa_to_time(tot, toa, ftoa)
            
            # if wanted, decode
            if decode:
                toa=counter_decode(toa, 'toa')
                tot=counter_decode(tot, 'tot')
                ftoa=counter_decode(ftoa, 'ftoa')
            
            # add to data frame (if wanted, in binary)
            row={'x': int(x), 'y': int(y), 'start': start, 'stop': stop, 'toa': int(toa), 'tot': int(tot), 'ftoa': int(ftoa)}
                    
            if binary:
                row={'x': int(x), 'y': int(y), 'start': start, 'stop': stop, 'toa': bin(int(toa)), 'tot': bin(int(tot)), 'ftoa': bin(int(ftoa))}
            
            df=df.append(row, ignore_index=True)
    
    # if pulse timing data is not required:
    elif time_data==0:
        
        # create data frame
        df=pd.DataFrame(columns=['x', 'y', 'toa', 'tot', 'ftoa' ])
        
        # loop through bit packets
        for i in np.arange(len(packets)):
            
            # unpack each packet
            header,addr,toa,tot,ftoa = unpack_001(packets[i])
            x,y = addr_to_xy(addr)
            
            # if wanted, decode
            if decode:
                toa=counter_decode(toa, 'toa')
                tot=counter_decode(tot, 'tot')
                ftoa=counter_decode(ftoa, 'ftoa')
            
            # add to data frame (if wanted, in binary)
            row={ 'x': int(x), 'y': int(y),'toa': int(toa), 'tot': int(tot), 'ftoa': int(ftoa)}
                    
            if binary:
                row={ 'x': int(x), 'y': int(y),  'toa': bin(int(toa)), 'tot': bin(int(tot)), 'ftoa': bin(int(ftoa))}
            
            df=df.append(row, ignore_index=True)

    # ensure correct data types:
    if binary==0:    
        df=df.astype( {'x': 'int64', 'y': 'int64', 'toa': 'int64', 'tot': 'int64', 'ftoa': 'int64'})       
    
    # sort by start time:
    df=df.sort_values(by=['start'], ignore_index=True)
    
    return df


# convert a series of bit packets to a data frame containing the pixel counter and timing values
# for ToA Only Mode (op_mode=01):
# 
# ARGUMENTS:      - decode=0/1 : display decoded (=1) or encoded (=0) pixel counters
#                 - time_data=0/1:  do (=1) or do not (=0) display hit start time  
#                 - binary=0/1: display counters in binary (=1) or decimal (=0)

def packets_to_df_011(packets, decode=1, time_data=1, binary=0):

    # to provide start time for each pulse:
    if time_data==1:
        
        # create data frame
        df=pd.DataFrame(columns=['x', 'y','start', 'toa', 'ftoa' ])
        
        # loop through bit packets
        for i in np.arange(len(packets)):
            
            # unpack each packet
            header,addr,toa,dummy10b,ftoa = unpack_011(packets[i])
            x,y   = addr_to_xy(addr)
            start = ftoa_and_toa_to_time(toa=toa, ftoa=ftoa)
            
            # if wanted, decode
            if decode:
                toa=counter_decode(toa, 'toa')
                ftoa=counter_decode(ftoa, 'ftoa')
            
            # add to data frame (if wanted, in binary)
            row={'x': int(x), 'y': int(y), 'start': start, 'toa': int(toa), 'ftoa': int(ftoa)}
                    
            if binary:
                row={'x': int(x), 'y': int(y), 'start': start,  'toa': bin(int(toa)), 'ftoa': bin(int(ftoa))}
            
            df=df.append(row, ignore_index=True)
    
    # if pulse timing data is not required:
    elif time_data==0:
        
        # create data frame
        df=pd.DataFrame(columns=['x', 'y', 'toa', 'tot', 'ftoa' ])
        
        # loop through bit packets
        for i in np.arange(len(packets)):
            
            # unpack each packet
            header,addr,toa,dummy10b,ftoa = unpack_011(packets[i])
            x,y = addr_to_xy(addr)
            
            # if wanted, decode
            if decode:
                toa=counter_decode(toa, 'toa')
                ftoa=counter_decode(ftoa, 'ftoa')
            
            # add to data frame (if wanted, in binary)
            row={ 'x': int(x), 'y': int(y),'toa': int(toa), 'ftoa': int(ftoa)}
                    
            if binary:
                row={ 'x': int(x), 'y': int(y),  'toa': bin(int(toa)), 'ftoa': bin(int(ftoa))}
            
            df=df.append(row, ignore_index=True)

    # ensure correct data types:
    if binary==0:    
        df=df.astype( {'x': 'int64', 'y': 'int64', 'toa': 'int64',  'ftoa': 'int64'})        
    
    # sort by start time:
    df=df.sort_values(by=['start'], ignore_index=True)
    
    return df    


# read packets from output file and return a data frame containing the pixel counter and timing values
# for ToA & ToT Mode (op_mode=00):
# 
# ARGUMENTS:      - decode=0/1 : display decoded (=1) or encoded (=0) pixel counters
#                 - time_data=0/1:  do (=1) or do not (=0) display hit start and stop time  
#                 - binary=0/1: display counters in binary (=1) or decimal (=0)

def file_to_df_001(file, decode=1, time_data=1, binary=0):
    
    packets=file_to_packets(file)
    
    df=packets_to_df_001(packets, decode, time_data, binary)
    
    return df


# read packets from output file and return a data frame containing the pixel counter and timing values
# for ToA Only Mode (op_mode=01):
# 
# ARGUMENTS:      - decode=0/1 : display decoded (=1) or encoded (=0) pixel counters
#                 - time_data=0/1:  do (=1) or do not (=0) display hit start time  
#                 - binary=0/1: display counters in binary (=1) or decimal (=0)

def file_to_df_011(file, decode=1, time_data=1, binary=0):
    
    packets=file_to_packets(file)
    
    df=packets_to_df_011(packets, decode, time_data, binary)
    
    return df


# # # # # # # # # # # # # # # # # # # # FINALISED FUNCTIONS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# take data frame with raw input (x,y coordinate of each hit; start, stop time of each hit) and write bit packets  to file:
#    ( - works for op_mode=00/01
#      - input_df must have columns 'x', 'y', 'start', 'stop')

def raw_to_file(file, in_df, op_mode=0):

    df=raw_to_unpacked(in_df, op_mode)
    
    values_to_file(df,file, op_mode)

    return 0


# read packets from output file and return a data frame containing the pixel counter and timing values
# for ToA & ToT Mode (op_mode=00) or ToA Only Mode (op_mode=01):
# 
# ARGUMENTS:      - decode=0/1 : display decoded (=1) or encoded (=0) pixel counters
#                 - time_data=0/1:  do (=1) or do not (=0) display hit start and stop time  
#                 - binary=0/1: display counters in binary (=1) or decimal (=0)
#                 - save=0/1: save DataFrame as ".csv" file

def file_to_df(file, op_mode=0, decode=1, time_data=1, binary=0, save=0, name=' '):
    
    if op_mode==0:
        df=file_to_df_001(file, decode, time_data, binary)
    elif op_mode==1:
        df=file_to_df_011(file, decode, time_data, binary)
    
    if save:
        df.to_csv(name)
    
    return df