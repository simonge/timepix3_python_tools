#  ------------------------------------------------------------------------------------- 
#  "counters.py" - Contains functions to encode and decode Timepix3 pixel counter values
#  -------------------------------------------------------------------------------------
#
#  As described in section 2.1.8 of the Timepix3 Manual v1.9 (specifically Tables 3, 4) 
#  the pixel counters (ToA, iToT, ToT, fToA, 10-b PC, 4-b PC) are encoded and contain
#  overflow control. 
#
#  This file provides the functions "counter_encode()" and "counter_decode()" which convert 
#  between a sequential count value and the encoded pixel counter values for each type of Timepix3 
#  pixel counter. 
#
#  Usage of the functions is explained in more detail at the end of the file.
#
#  Numpy is required.
#
#                                                                    David Amorim, 2022


# import relevant modules
import numpy as np


# runs one cycle of a general-purpose LFSR, with initial register value "n"
#       - taps specified via distance from LSB
#       - returns new value in register after the cycle is completed

def LFSR(n,register_size,tap_1, tap_2, tap_3=0, tap_4=0):

    # determine value of LSB in next cycle (from feedback function):
    n_0 = int(bool(n & (1 << tap_1)) ^ bool(n & (1 << tap_2))) 

    if (tap_3 !=0) & (tap_4 !=0):
        n_0 = int(bool(n & (1 << tap_1)) ^ bool(n & (1 << tap_2)) ^ bool(n & (1 << tap_3)) ^ bool(n & (1 << tap_4)) ) 
        
    # shift register to left and shift out leftmost bit (by setting leading bit to 0):
    n <<=1
    n &= ~( 2**register_size)

    # apply appropriate value to LSB from feedback function:
    if n_0:
        n |= 1
       
    # return new vlaue in register
    return n


# set up appropriate LFSR for each counter type by specifying register size, tap values, and overflow control
#        (see Tables 3 & 4 in the Timepix3 Manual v1.9 )

def set_LFSR(counter):
    
    # LFSR set-up for the 14-bit Integral ToT counter
    if (counter=='iToT') | (counter=='itot'):
        register_size, tap_1, tap_2, tap_3, tap_4, overflow_toggle, overflow_val= 14, 1, 11, 12, 13, False, 0
    
    # LFSR set-up for the 10-bit ToT counter and the 10-bit Event Counter
    elif (counter=='ToT') | (counter=='PC10b') | (counter=='tot') | (counter=='pc10b'):
        register_size, tap_1, tap_2, tap_3, tap_4, overflow_toggle, overflow_val=10, 6, 9, 0, 0, True, 0b0111111111
        
    # LFSR set-up for the 4-bit Event Counter
    elif (counter=='PC4b') | (counter=='pc4b'):
        register_size, tap_1, tap_2, tap_3, tap_4, overflow_toggle, overflow_val=4, 3, 2, 0, 0, True, 0b0111
        
    return register_size, tap_1,tap_2,tap_3,tap_4,overflow_toggle, overflow_val


# encode N sequential counts into the appropriate LFSR count for iToT, ToT, 10-bit PC, 4-bit PC counters
#      (runs the corresponding LFSR for N cycles)
def LFSR_encode(N,counter):

    # set up appropriate LFSR:
    register_size, tap_1,tap_2,tap_3,tap_4,overflow_toggle, overflow_val= set_LFSR(counter)

    # seed LFSR with appropriate start value:
    seed=2**register_size-1
    encoded=seed
    
    # run LFSR for N cycles
    for i in np.arange(N):
        encoded= LFSR(encoded,register_size,tap_1, tap_2, tap_3, tap_4)

    # implement overflow control
    if (overflow_toggle==True) & (N >= seed -1):
        encoded=overflow_val
           
    # return encoded LFSR counter
    return encoded


# decode LFSR counter value into sequential counter value for iToT, ToT, 10-bit PC, 4-bit PC counters
#       (runs the corresponding LFSR until the right value is encountered)
#
#       NOTE: this method of decoding is less efficient than approaches using look-up tables; 
#             might need to be changed if code executes too slowly for large data sets

def LFSR_decode(encoded,counter):
    
    # set up appropriate LFSR for each variable
    register_size, tap_1,tap_2,tap_3,tap_4,overflow_toggle, overflow_val= set_LFSR(counter)

    # seed LFSR with appropriate reset value
    seed=2**register_size-1
    m=seed
    
    # run LFSR until encoded value is encountered:
    # (if value is not encountered,or equal to seed, N is set to 0)
    N=0
    while N<seed:
        m= LFSR(m,register_size,tap_1, tap_2, tap_3, tap_4)
        N +=1
        if m==encoded:
            break
    if N==seed:
        N=0
            
    # implement overflow control  
    if (overflow_toggle==True) & (encoded==overflow_val):
        N=seed-1
    
    # return decoded (sequential) counter value
    return N


# convert from Binary encoding to Gray encoding

def bin_to_gray(n):
    n ^= (n >> 1)
    return n


# convert from Gray encoding to Binary encoding

def gray_to_bin(n):
    mask = n
    while mask != 0:
        mask >>= 1
        n ^= mask
    return n


# defining the fToA counter (binary counter with overflow value 15)

def ftoa_counter(n):
    if n>15:
        n=15
    return n

# # # # # # # # # # # # # # # # # # # # FINALISED FUNCTIONS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


# The value of the variable "counter" in the two functions below is limited to:
#         - 'iToT' or 'itot' for the iToT counter
#         - 'ToA' or 'toa' for the ToA counter
#         - 'ToT' or 'tot' for the ToT counter
#         - 'fToA' or 'ftoa' for the fToA counter
#         - 'PC10b' or 'pc10b' for the 10-bit Event Counter
#         - 'PC4b' or 'pc4b' for the 4-bit Event Counter


# convert N (sequential) counts to the appropriate counter value for iToT, ToT, ToA, fToA, 10-bit PC, 4-bit PC

def counter_encode(N, counter):
    
    if (counter=='ToA') | (counter=='toa'):
        encoded=bin_to_gray(N)
    elif (counter=='fToA') | (counter=='ftoa'):
        encoded=ftoa_counter(N)
    else:
        encoded=LFSR_encode(N,counter)
    
    return encoded  


# convert decoded counter value to the appropriate sequential count for iToT, ToT, ToA, fToA, 10-bit PC, 4-bit PC

def counter_decode(n,counter):
    
    if (counter=='ToA') | (counter=='toa'):
        decoded=gray_to_bin(n)
    elif (counter=='fToA') | (counter=='ftoa'):
        decoded=n
    else:
        decoded=LFSR_decode(n,counter)
   
    return decoded
    
    