===================================================================================
                        EQUALISATION PROCEDURE FOR TIMEPIX3
===================================================================================
                                    David Amorim (2538354a@student.gla.ac.uk), 2022

General:
--------
The Python code in "equalisation.py" implements an equalisation procedure for the 
Timepix3 ASIC (with suitable modifications possibly also for Timepix1 or Timepix4).
The procedure is mostly based on an equivalent routine for Timepix1 equalisation, 
written by Dima Maneuski (Dima.Maneuski@glasgow.ac.uk), and the implementation of 
Timepix3 equalisation by ADCACAM's Pixet software. The code in "equalisation.py" 
aims to reproduce all of the core features and settings of equalisation available in
the above two approaches.
At this point (August 2022), the code is unfinished in two regards:
     1. Some features of Pixet equalisation have not been implemented (e.g. autorange,
        THL Coarse). Suitable dummy functions have been arranged, which are to be 
        replaced in the future.
     2. All functions that would require I/O interaction with the Timepix3 ASIC 
        (e.g. taking measurements or re-setting parameters) have been replaced with
        suitable simulations. These are also to be replaced in the future. 


Requirements:
-------------
The following Python modules are required to execute the code:
    - numpy
    - pandas
    - scipy
    - matplotlib
A missing or outdated module can be installed using the command 
   >>> pip install --upgrade <module_name>


Usage:
------
To run the equalisation procedure, the function "equalisation" has to be executed. 
As the procedure runs, status updates are printed to the terminal, including a 
visualisation of the output. By default, three parameters are returned:
    - dac_thl: the new global threshold value 
    - mask : a list containing the recommended masking values (0/1) for 
               each pixel 
    - adj_list: a list containing the recommended adjustment bit values
               for each pixel
Additionally, the visualisation of the output can be saved to file (save=True) and
a DataFrame containing more detailed information can be returned instead of the two
lists (return_df=True). Note that at this point (August 2022) the output of 
equalisation cannot be fed into the ASIC to update its settings. Once I/O with the
chip is possible an additional function to implement this will have to be provided.

The "equalisation" function takes a variety of input arguments. The required ones are:
    - From: starting point of the threshold range
    - to: end point of the threshold range (to > From)
    - step: step size in the threshold range (step>0)
Further important arguments are:
    - save: if True, save the provided visualisation [Boolean, default: False]
    - return_df: if True, return a more detailed DataFrame [Boolean, default: False]  
    - spacing: measure of how many rows/cols of pixels are blocked off during each scan;
         a higher spacing means higher quality equalisation but quadratically increases
         execution time [Int in range 1-256, default: 4]; NOTE: when working with simulated
         data there is no benefit in setting spacing>1! 
(Additional arguments include:
    - count: if set to greater than 1, each measurement is repeated "count" times and the 
         result is averaged [Int >=1, default: 1]
    - time: exposure time of each noise measurement in seconds [Float, default: 0.001] 
    - th_count: number of noise counts in a pixel during exposure that has to be exceeded 
         in order for the pixel to be viewed as active in that period [Int, default: 5]
A range of further arguments can additionally be passed to the function which are linked to 
yet to be provided dummy functions and hence currently (August 2022) are not relevant to 
running the procedure:
    - autorange, timepix_mode, thl_coarse, polarity, x_space, y_space, tp1_thl
)
    
When working with simulated noise data only the following arguments are really relevant:
    - From, to, step, save, return_df, spacing
Spacing should always be set to 1 when working with simulated data! Further note that the
default mean of the noise distribution is ~100 and hence it is recommended to set From<100
and to>100 for meaningful results. 

The following command-line input (run in the appropriate directory) provides an example of
how to execute equalisation:

        [user dir]$ python3
        >>> from equalisation import equalise
        >>> dac_thl, mask, adj = equalise(50, 125, 1, spacing=1)
        
Note that when return_df=True only two variables are returned so that the third line should
be altered to

       >>> dac_thl, df = equalise(50, 125, 1, spacing=1, return_df=True)
       
in order to avoid a ValueError. Since there is so far (August 2022) no way to meaningfully
adjust the settings of the ASIC based on the results of equalisation it is also viable to
not save the outputs at all and simply focus on the visualisation:
      
      [user dir]$ python3
      >>> from equalisation import equalise
      >>> equalise(50,125,1, spacing=1, save=True)


About Equalisation:
-------------------
Equalisation is a means of calibrating the Timepix3 ASIC by taking into account the varying 
noise levels across the pixel array. Noise in pixels can be managed in three ways:
    1) changing the global DAC threshold for the entire array
    2) individually setting adjustment bits for each pixel
    3) masking (disabling) individual pixels
Adjustment bits are used to locally increase the DAC threshold above the global level in order
to offset noiser-than-average pixels whereas masking is used to completely disable "hot" and
inherently noisy pixels. Equalisation is a procedure which determines optimised values for all
three of those quantities: global DAC threshold, local adjustment bit values, and masking values.

Equalisation involves performing three threshold scans. In each threshold scan, pixel noise values
are measured for different global threshold values in a given range while adjustment bit values 
remain constant. To avoid correlation effects between the noise levels in adjacent pixels, noise 
measurements are performed in a number of sub-acquisitions during each of which some pixels are 
blocked off (related to the variable "spacing" mentioned above). A threshold scan returns a 
distribution of the highest global threshold value at which each pixel was triggered by noise (the
"trigger threshold"). The mean of this distribution gives a good indication of the average pixel 
noise level. Additionally, pixels with especially high noise levels are noted during a scan (for
later masking). 

The first threshold scan is run with all adjustment bits set to their maximum value (15). This 
means that the local threshold at each pixel will be higher than the global threshold.
The second threshold scan is run with all adjustment bits set to their minimum value (0). Thus, the
local threshold is equal to the global threshold for all cases. The difference in the resulting 
threshold distributions is indicative of the effect of the adjustment bits on regulating local 
thresholds. 
The optimised adjustment bit value for each pixel is that value which results in a trigger threshold
closest to the mean of the means of the two threshold distributions (found using a simple linear 
scaling).

Finally, a third threshold scan is run with the pixel adjustment bits set to the value determined in
the previous step. The mean of the resulting threshold distribution is then the optimised global 
threshold value (and should be close to the mean of the means of the first two distributions). 
