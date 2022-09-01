#  ------------------------------------------------------------------------------------- 
#  "equalisation.py" - Contains first attempt at implementing core features of a 
#                      Timepix3 equalisation procedure 
#  -------------------------------------------------------------------------------------
#  
#  Please see the associated READ_ME file for more information on usage.
#
#
#                                                                    David Amorim, 2022


# import relevant modules
import sys
from datetime import datetime
import numpy as np
import numpy.random as rd
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# set variables: pixel dimensions on chip [xPix * yPix]
# (for Timepix3: 256*256)
xPix=256
yPix=256


###################### AUXILIARY DUMMY FUNCTIONS: to be replaced later ##############

# executes a pre-scan to automatically find suitable "From" and "to" values
# threshold values for equalisation:
def get_range():
    ###
    return 0,0

# sets chip operation mode:
def set_mode(mode):
    ###
    return 0

# set DAC threshold in chip:
def set_threshold(threshold):    
    ###
    return 0

# do whatever thl_coarse does:
def coarse():    
    ###
    return 0


####################### FIRST ATTEMPTS AT FUNCTION IMPLEMENTATION #############################

# visualise output:

def visualise(From, to,steps, df, save=False):
    
    # set up figure
    plt.figure(figsize=[15,35])
    fig, (ax0, ax2, ax1) = plt.subplots(3,1, constrained_layout=True)
    fig.set_size_inches(15,10)
    fig.suptitle("Equalisation Output", fontsize=24)

    # visualise threshold distribution
    vals_15, bins_15, patches_15 =ax0.hist(df['thl_15'], label='1st Scan (mu ={0:.2f}, sig={1:.2f})'.format(df['thl_15'].mean(), df['thl_15'].std()), color='blue', density=True, bins=np.arange(From, to+steps, steps))
    vals_0, bins_0, patches_0 =ax0.hist(df['thl_0'], label='2nd Scan (mu ={0:.2f}, sig={1:.2f})'.format(df['thl_0'].mean(), df['thl_0'].std()), color='green',  density=True, bins=np.arange(From, to+steps, steps))
    vals_opt, bins_opt, patches_opt=ax0.hist(df['thl_opt'], label='3rd Scan (mu ={0:.2f}, sig={1:.2f})'.format(df['thl_opt'].mean(), df['thl_opt'].std()), color='red', density=True, bins=np.arange(From, to+steps, steps))

    thl=np.linspace(From, to, 1000)
    
    ax0.plot(thl,stats.norm.pdf(thl, df['thl_15'].mean(), df['thl_15'].std()),  color='navy', ls='--')
    ax0.plot(thl,stats.norm.pdf(thl, df['thl_0'].mean(), df['thl_0'].std()),  color='limegreen', ls='--')
    ax0.plot(thl,stats.norm.pdf(thl, df['thl_opt'].mean(), df['thl_opt'].std()),  color='darkred', ls='--')

    ax0.plot([df['thl_15'].mean(),df['thl_15'].mean()],[0,vals_15.max()],color='navy', ls='-')
    ax0.plot([df['thl_0'].mean(),df['thl_0'].mean()],[0,vals_0.max()],color='limegreen', ls='-')
    ax0.plot([df['thl_opt'].mean(),df['thl_opt'].mean()],[0,vals_opt.max()],color='darkred', ls='-')
    ax0.plot([0.5*(df['thl_15'].mean()+df['thl_0'].mean()),0.5*(df['thl_15'].mean()+df['thl_0'].mean())], [0,vals_opt.max()], color='black', ls='-', label='Mean of Means (mu={0:.2f})'.format(0.5*(df['thl_15'].mean()+df['thl_0'].mean())))
    
    ax0.set_ylabel('Fraction of Pixels')
    ax0.set_xlabel('Threshold Value')
    ax0.legend(fontsize=13)
    ax0.set_xlim(From,to)
    ax0.set_title("Threshold Distribution", fontsize=16)

    # visualise masking distribution
    ax1.hist(df['mask_final'], label='3rd Scan (ratio={0:.3f})'.format((df['mask_final']==0).astype('int').sum()/256**2), color='red', bins=[0,0.2,0.6,0.7,0.8,1])
    ax1.set_ylabel('Nmbr of Pixels')
    ax1.set_xlabel('Mask Value (0/1)')
    ax1.set_xlim(0,1)
    ax1.set_xticks(ticks=[0.1,0.9])
    ax1.set_xticklabels(['0 (Disabled)','1 (Active)'])
    ax1.legend(fontsize=13)
    ax1.set_title("Mask Distribution (Active  vs. Disabled Pixels)", fontsize=16)

    # visualise adjustment bit distribution
    vals, bins, bars = ax2.hist(df['adj'], label='3rd Scan (mu={0:.2f}, sig={1:.2f})'.format(df['adj'].mean(), df['adj'].std()),color='red', bins=np.linspace(0,16,17), density=True)
    ax2.set_ylabel('Fraction of of Pixels')
    ax2.set_xlabel('Adjustment Bit Value (0-15)')
    ax2.set_xticks(ticks=np.linspace(0.5,15.5,16))
    ax2.set_xticklabels(np.linspace(0,15,16, dtype='int'))
    ax2.set_xlim(0,16)
    ax2.legend(fontsize=13)
    ax2.set_title("Adjustment Bit Distribution", fontsize=16)

    # save output to file, if wanted
    if save:
        plt.savefig('equalisation_out.png')
    
    plt.show()
    
    return 0


# take a measurement of the pixel array:
#
#    ARGUMENTS:  - df: DataFrame with one row for each pixel and 
#                      the following columns
#                     + x: horizontal coordinate
#                     + y: vertical coordinate
#                     + adj: adjustment bit 
#                     + sub_mask_X: 1 if pixel enabled/not masked, 0 if disabled/masked
#                          (number of sub_mask columns depends on spacing)
#                     + mean_noise: mean of noise 
#                     + std_noise: standard deviation of noise
#                - threshold: global DAC threshold
#                - time: exposure time in seconds
#                - itr: index variable (set "X" parameter in sub_masks)
#
#    RETURNS:    - list with number of times each pixel was triggered

def measure(df, time, threshold, itr):
    
    ## NOTE: this is currently a dummy function
    #      - in the long term, replace with a function that can
    #        interact with the actual detector and measure real data
    #      - the following code produces simulated (Gaussian) noise data 
    #        based on some general assumptions: noise frequency,
    #        impact of adjustment bits, noise mean and standard 
    #        deviation; the values of the first two parameters 
    #        can be changed below while those of the latter two 
    #        are specified in the function "equalisation" below
    
    # set parameters:
    noise_frequency=10e3      # noise frequency in Hz
    adj_impact=50             # impact of adjustment bits on local threshold in percent 
                              # (e.g. if adj_impact=50 then an adj=15 for a pixel results in a
                              # local threshold that is 50 percent higher than the global threshold)
    
    # determine noise count based on frequency and exposure time:
    num=np.rint(noise_frequency*time).astype('int')
    if num==0:
        num+=1
    
    # generate appropriate number of noise values for each pixel, 
    # with noise values based on noise distribution 
    mean_noise_local=np.tile(df['mean_noise'] , [num,1])
    std_noise_local=np.tile(df['std_noise'], [num,1])
    
    # calculate local threshold for each pixel (based on ajustment bit value)
    threshold_local=np.tile(threshold*(1+adj_impact/1500*df['adj']), [num,1])
    
    # count how many times the noise levels exceeded the local threshold in each active pixel
    raw_arr=(np.abs(rd.normal(0, std_noise_local, (num, xPix*yPix)))+mean_noise_local >= threshold_local).astype('int')
    vals=raw_arr.sum(axis=0) * (df['sub_mask_{0}'.format(itr)] == 1).astype('int')
    
    # return the result
    return vals.to_numpy(dtype='int')
    

# runs a threshold scan:
#
#   ARGUMENTS: - from: starting point of the threshold range. Must be less than "to".
#              - to: end point of the threshold range. Must be greater than "From".
#              - step: spacing between threshold values. Must be geater than 0
#              - spacing: measure of how many pixels are blocked off during acquisition. 
#                  Ranges from 1 to 256 [1 to xPix]. Greater values mean higher quality equalisation but
#                  longer execution time. Default is 4 (based off Pixet)
#              - time: duration of each acquisition in seconds (i.e. exposure time).
#                  Default is 0.001 (based off Pixet)
#              - count: number of measurements per sub-acquisition. Defualt is 1 (based off Pixet)
#              - th_count: number of times a pixel has to be high during time to count
#                  as active at a given threshold. Default 5 (based off Pixet)
#              - df: data frame with columns:
#                      + x,y : pixel coordinates
#                      + adj :  pixel adjustment bits                                        
#
#    RETURNS: - mean: mean of pixel threshold distribution
#             - std: standard deviation of pixel threshold distribution
#             - thresh_list: pixel threshold distribution
#             - mask_list: recommended masking of noisy pixels (1: enabled/not masked; 0: disabled/masked)

def threshold_scan(From, to, step, spacing, time, count, df, th_count):
    
    # set up DataFrame
    df['counter']=np.zeros((xPix*yPix))
    df['thl']=np.full((xPix*yPix),From)
    
    # set mask for each sub-acquisition (1: enabled/not masked ; 0: disabled/masked):
    for i in np.arange(spacing**2):
             
        # loop through threshold values:
        for thl in np.arange(From, to, step):       
            
            # set global threshold in detector:
            set_threshold(thl)
                    
            # take measurement (average of several measurements, if count>1):
            tmp=np.zeros(xPix*yPix, dtype='int')
            for k in np.arange(count):
                tmp+=measure(df, time, thl, itr=i)
            df['val']=tmp/count
                    
            # records the highest threshold at which each pixel was still triggered
            df['thl']+= step*((df['val'] >= th_count) & (df['sub_mask_{0}'.format(i)])).astype('int')
                          
            # increment a counter if a pixel was triggered at a threshold greater than 95% of the maximum threshold:
            df['counter'] +=((df['val'] >= th_count) & (df['sub_mask_{0}'.format(i)])  & (thl > 0.95*to)).astype('int') 
                                    
    # calculate the mean and standard deviation of the threshold distribution
    mean=(df['thl'].loc[df['thl'] != 0]).mean()
    std=(df['thl'].loc[df['thl'] != 0]).std()
    
    # determine bits to be masked (1: enabled/not masked; 0: disabled/masked):
    #     - a bit will be masked if it is triggered at more than 
    #       95% of threshold values which are greater than 95% 
    #       of the maximum threshold value
    #     - this is meant to filter out pixels that are intrinsically
    #       noisy 
    #     - note that the numerical values used (95%, 95%) are arbitrary
    #       and might have to be adjusted 
    df['mask']=( ~(df['counter'] > (np.arange(From, to, step) > 0.95 * to).sum()) ).astype('int')
    
    # return output: mean, std, threshold distribution, masking distribution
    return mean,std,df['thl'],df['mask']


# runs equalisation
#
#   ARGUMENTS: - (see arguments of "threshold_scan")
#              - autorange: if True, automatically find values for 
#                  "from" and "to". CURRENTLY DUMMY
#              - timepix_mode: set operation mode. Can be 0, 1, 10. Default 0. CURRENTLY DUMMY
#              - thl_coarse: CURRENTLY DUMMY and unknown what it is meant to do
#              - polarity: detector polarity. Either -1 (electrons) or 1 (holes). 
#                   Default 1. CURRENTLY DUMMY und unknown what it is supposed to mean
#              - return_df: if True, return entire data frame (default False)
#              - save: if True, saves image of output (default False)
#              - x_space, y_space : define vertical and horizontal pixel spacing; works like "spacing" but applied 
#                     throughtout all measurements, not just during one sub-acquisition;
#                     must be an integer power of 2 between 1 and 256; default 1/no pixels skipped 
#              - tp1_thl: if True, calculate output threshold value based on a method used in the equalisation procedure
#                     for Timepix1, which increased or decreases the threshold based on detector polarity and 
#                     the standard deviation of the procedure threshold distribution; default False
#              
#   RETURNS:   - dac_thl: new, optimised global threshold.
#              - mask_list: list containing pixel masking information (0: disabled/masked; 1: enabled/not masked)
#              - adj_list: list containing optimised pixel adjustment bits (0-15)

def equalise(From, to, step, spacing=4, time=1e-3, count=1, autorange=False, timepix_mode=0, thl_coarse=False, th_count=5, polarity=1, return_df=False, save=False, x_space=1, y_space=1, tp1_thl=False):
     
    print('-------------------------------------------------------------------------')    
        
    ## IMPLEMENT CHECKS FOR CORRECT DATA TYPES, VALUES, RANGES AND ABORT IF NECESSARY:
    
    if  (spacing < 1) or (spacing > xPix) or (count < 1):
        sys.exit('RangeError: provided value(s) out of range of variable(s).')
    if (From > to) or (step <= 0):
        sys.exit('SignError: interval of threshold values must be increasing.')
    if (timepix_mode != 0) and (timepix_mode != 1) and (timepix_mode != 10):
        sys.exit('ValueError: timepix mode must be 0, 1, or 10')
    if (polarity != 1) and (polarity != -1):
        sys.exit('ValueError: polarity must be 1 (holes) or -1 (electrons)')
    if ( (type(From) != type(1)) and (type(From) != type(0.1)) )  or ( (type(to) != type(1)) and (type(to) != type(0.1)) ):
        sys.exit('TypeError: value(s) of wrong type(s) passed to variable(s)')
    if ((type(step) != type(1)) and (type(step) != type(0.1)))  or (type(count) != type(1)):
        sys.exit('TypeError: value(s) of wrong type(s) passed to variable(s)')
    if (type(th_count) != type(1)) or (type(spacing) != type(1)) or (type(x_space) != type(1)) or (type(y_space) != type(1)):
        sys.exit('TypeError: value(s) of wrong type(s) passed to variable(s)')
    if (type(time) != type(0.1)) and (type(time) != type(1)):
        sys.exit('TypeError: value of wrong type passed to variable')
    if (type(autorange) != type(False)) or (type(thl_coarse) != type(False)):
        sys.exit('TypeError: value(s) of wrong type(s) passed to variable(s)')
       
    
    ## PREPRARE THRESHOLD SCANS:
    print('[{0}] Initialising equalisation. \n'.format(datetime.now()))
    
    # set correct timepix mode:
    set_mode(timepix_mode)
    
    # if autorange is enabled, get new values for From and to:
    if autorange:
        From, to = get_range()
        
    # if thl_coarse is enabled, do whatever thl_coarse does:
    if thl_coarse:
        coarse()
    
    # set up DataFrame
    df = pd.DataFrame(index=np.arange(xPix* yPix))
    df['x'] = df.index % xPix
    df['y'] = df.index//xPix
    df['adj']=np.zeros((xPix*yPix), dtype='int')
    
    # skip pixel rows or columnsm, if desired [useful if working with superpixels]:
    df['skip_mask']=((df['x'] % x_space == 0) & (df['y'] % y_space == 0)).astype('int')
    
    # set up sub-masks for sub-acquisitions [taking into account skipped pixel rows, as above]
    for i in np.arange(spacing):
        for j in np.arange(spacing):
            df['sub_mask_{0}'.format(i*spacing+j)]=(df['x'] % spacing == i) & (df['y'] % spacing==j) & (df['skip_mask']==1)   
            df['sub_mask_{0}'.format(i*spacing+j)]=df['sub_mask_{0}'.format(i*spacing+j)].astype('int')
    
    # set up randomly generated pixel noise 
    #    NOTE: these noise values are use in the dummy version of the 
    #          "measurement" function, which simulates noise; 
    #          once that function is replaced by one which can actually
    #          measure pixel noise the lines below can be deleted
    df['mean_noise']=np.abs(rd.normal(100, 5, size=(xPix*yPix)))  # default values: 100, 5
    df['std_noise']=np.abs(rd.normal(1,0.2,size=(xPix*yPix)))     # defualt values: 1, 0.2
    
    
    ## FIRST THRESHOLD SCAN:
    print('[{0}] Starting threshold scan 1 out of 3. \n'.format(datetime.now()))
    
    # set all adjustment bits to 15:
    df['adj'] += 15
    
    # initialise scan and save output:
    mean_15, std_15, df['thl_15'], df['mask_15'] = threshold_scan(From, to, step, spacing, time, count, df, th_count)
    
    ## SECOND THRESHOLD SCAN:
    print('[{0}] Starting threshold scan 2 out of 3. \n'.format(datetime.now()))
    
    # set all adjustment bits to 0:
    df['adj'] *= 0
    
    # initialise scan and save output:
    mean_0, std_0, df['thl_0'], df['mask_0'] = threshold_scan(From, to, step, spacing, time, count, df, th_count)
    
    ## THIRD THRESHOLD SCAN:
    print('[{0}] Starting threshold scan 3 out of 3. \n'.format(datetime.now()))
    
    # find target threshold from mean of means:
    target= 0.5 * (mean_15 + mean_0)
    
    # calculate new values for adj_list based on linear scaling:
    #   NOTE:  if the local threshold of a pixel is unaffected
    #          by changing its adjustment bit then the pixel 
    #          will be masked;
    #          this both disables broken or overly noisy pixels
    #          and avoids division by 0 errors
    df['mask_tmp'] = (df['thl_15'] != df['thl_0']).astype('int')
    df['adj']=(np.rint(15* (target-df['thl_0'])/(df['thl_15']-df['thl_0']))* df['mask_tmp']).to_numpy(dtype='int')
            
    # make sure the new adjustment bit values are in the right range
    df['adj']=df['adj'].clip(0,15)    
                
    # initialise scan and save output:
    mean_opt, std_opt, df['thl_opt'], df['mask_opt'] =threshold_scan(From, to, step, spacing, time, count, df, th_count)
    
    print('[{0}] Finishing up equalisation. \n'.format(datetime.now()))
    
    
    ## UPDATE MASK LIST: combine the masking recommendations of the previous scans
    df['mask_final'] = (df['mask_0'] & df['mask_15'] & df['mask_opt'] & df['mask_tmp'] & df['skip_mask']).to_numpy(dtype='int')
    
    
    ## CALCULATE OPTIMISED GLOBAL THRESHOLD VALUE:
    dac_thl= mean_opt
    if tp1_thl:
        dac_thl+=polarity * std_opt * 15 
     

    ## VISUALISE RESULTS (and save figure, if wanted)
    print('[{0}] Visualising results. \n'.format(datetime.now()))
    visualise(From, to, step,df, save)
    
    ## RETURN OUTPUTS:
    print('[{0}] The recommended global threshold is {1:.2f} . '.format(datetime.now(), dac_thl))
    print('-------------------------------------------------------------------------')
    
    if return_df:
        return dac_thl, df
    else:
        return dac_thl, df['mask_final'].to_numpy(dtype='int'), df['adj'].to_numpy(dtype='int')