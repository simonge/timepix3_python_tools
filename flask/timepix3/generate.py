#  ------------------------------------------------------------------------------------------
#  "generate.py" - Contains functions to randomly generate hit data as well as to visualise
#                  hit data               
#  -------------------------------------------------------------------------------------------
#
#  The function "gen_hits" generates a given number of hits on random pixels at random times 
#  within the ToA timestamp range. The associated time-over-threshold of each hit is also 
#  randomised. 
#
#
#  The function "simulate" generates hit data, processes it (ToA & ToT Mode or ToA Only Mode)
#  and writes the resulting bit packets to a binary file. At the same time, the associated 
#  hit timing data and decoded pixel counter values are written to a csv file for reference. 
#  See the comments below on more information about usage of the function.
#
#
#  The function "visualise" reads in a csv file containing hit information (columns: 'x', 
#  'y', 'start', 'stop') and returns an animated gif of the hits with the desired number of 
#  steps in time. Note that since the gif frame rate is constant increasing the number of steps 
#  will also increase the length of the gif. 
#
#
#  This file requires numpy, celluloid and pandas as well as functions from "packing.py" . 
#  The modules matplotlib and celluloid are additionally required for visualisation.
#
#                                                                    David Amorim, 2022        


# import modules
import pandas as pd 
import numpy as np
from numpy import random as rd
from celluloid import Camera
import matplotlib.pyplot as plt
from timepix3.packing import raw_to_file, file_to_df


# generate N hits of random pixels at random times:
#     NOTE: -essentially generates pixel noise
 
def gen_hits(N):
    
    # generate random coordinates
    x=rd.randint(0,256,size=N)
    y=rd.randint(0,256, size=N)

    # generate random timing data in ToA range
    start=rd.uniform(0, 409.6e-6, size=N)
    stop=np.empty(N)

    for i in np.arange(N):
        stop[i]=start[i]+ 25e-9 * rd.uniform(0,1022)
    
    # combine columns into DataFrame
    df=pd.DataFrame()
    df['x']=x
    df['y']=y
    df['start']=start
    df['stop']=stop

    # sort by start time:
    df=df.sort_values(by=['start'])
    
    # return data
    return df

# generates hits corresponding to N particle detections; returns DataFrame with raw hit timing and address data
#    NOTE:  - output DataFrame will be about 'mean_len' (default:10) times larger than number of particles (N) !      

def gen_phys_hits(N):
    
    # simulation parameters [adjust later!]
    
    speed       = 3e8 / 55e-6     # particle speed in pixels per second [assumes light speed]
    decay_const = 1e5             # rate at which ToT decays as particle slows down 
    snr         = 0.8             # ratio of tracks to noisy pixels
    scatter_ang = 0.2 * np.pi     # mean particle deflection angle [assumes Poisson distr]
    scatter_prob= 0.01            # probability that particle will scatter at each pixel
    mean_tot    = 250             # mean of ToT distribution [assumes Gaussian]
    std_tot     = 15              # std of ToT distribution
    mean_len    = 10              # mean track length [Gaussian]
    std_len     = 5               # std of track length
    
    # declare arrays
    X, Y= np.array([], dtype='int'), np.array([], dtype='int') 
    Start, Stop = np.array([], dtype='float'), np.array([], dtype='float')
    
    # loop through number of particles
    for i in np.arange(N):
        
        # generate a random initial hit:
        x_0=int(rd.uniform(0,256))
        y_0=int(rd.uniform(0,256))
        start_0=rd.uniform(0, 409.6e-6)
        stop_0= start_0 + 25e-9 * np.abs(rd.normal(loc=mean_tot, scale=std_tot))
        theta_0=rd.uniform(0, 2*np.pi)
        
        # randomly determine the length of the track
        l=int(np.abs(rd.normal(mean_len,std_len)))
        
        # declare arrays
        x, y              = np.array([], dtype='int'), np.array([], dtype='int')
        start, stop       = np.array([], dtype='float'), np.array([], dtype='float')
        x, y, start, stop = np.append(x,x_0),np.append(y,y_0), np.append(start,start_0),np.append(stop,stop_0)
    
        # loop through track:
        for j in np.arange(l)+1:
            
            # determine new position of particle
            x_new= int(x[0]+ j * np.cos(theta_0))
            y_new= int(y[0]+j * np.sin(theta_0))
            
            # confirm that particle still in pixel array:
            if (x_new >= 0) & (x_new <= 255) & (y_new >= 0) & (y_new <= 255):
                
                # update particle position
                x=np.append(x,x_new)
                y=np.append(y,y_new)
                
                # calculate distance travelled, update timing data accordingly:
                r= np.sqrt( (x_0-x_new)**2+ (y_0-y_new)**2)
                start=np.append(start,start_0+ r/speed)
                stop=np.append(stop,stop_0+r/speed-np.exp(-r*decay_const))
                
                # allow for particle scattering
                theta_0 += rd.choice([0, 1, -1], p=[1-scatter_prob,0.5* scatter_prob,0.5* scatter_prob])*rd.poisson(scatter_ang)
            
            # stop if particle has left sensor area 
            else:
                break
        
        # add track to arrays
        Y=np.append(Y,y)
        X=np.append(X,x)
        Start=np.append(Start, start)
        Stop=np.append(Stop, stop)
     
    # combine columns into DataFrame
    df=pd.DataFrame()
    df['x']=X
    df['y']=Y
    df['start']=Start
    df['stop']=Stop

    # add noise
    df2=gen_hits(int(N*(1-snr)))
    df=pd.concat([df,df2])

    # sort by start time:
    df=df.sort_values(by=['start']) 
    
    # return DataFrame
    return df

# generate N random hits, process (ToA & ToT Mode or ToA Only Mode) and packets to binary file; write 
# corresponding decoded pixel counter values to csv file for reference 
#        ARGUMENTS:   - N : number of hits
#                     - op_mode=0/1: ToA & ToT Mode (=0) or ToA Only Mode (=1) 
#                     - bin_name: filename of binary file
#                     - csv_name: filename of csv file

def simulate(N, op_mode=0, bin_name='packets.bin', csv_name='values.csv'):
    
    # generate N hits
    df=gen_phys_hits(N)
    
    # pack and write to binary file
    raw_to_file(bin_name, df,op_mode)
    
    # save csv file with corresponding decoded pixel counter values for each hit
    file_to_df(bin_name,op_mode, decode=1, save=1, name=csv_name)
    
    return 0


# takes input file containing decoded pixel counter values and animates a GIF with the desired step size:
#     (NOTE: input file must be csv with columns 'x', 'y', 'start', 'stop' ;
#            thus, only works for decoded data in ToA & ToT Mode)

def visualise(steps, in_file='./input/values.csv', out_file='./output/timepix_simulations.gif'):
    
    # read input data 
    df=pd.read_csv(in_file)
    
    # define time range and number of steps in the animation
    time=np.linspace(0, 409.6e-6, steps)
    
    # set up animation
    fig = plt.figure(figsize=[10,10])
    camera = Camera(fig)
    
    # animate heatmap
    for i in time:
        
        # set up empty pixel grid
        data=np.zeros( (256,256)) 
        
        # set active pixels to 1
        for j in np.arange(len(df['start'])):
            x=df['x'].iloc[j]
            y=df['y'].iloc[j]
            if (df['start'].iloc[j] <= i) & (df['stop'].iloc[j] >= i):
                data[x][y]=1
        
        # plot pixel array
        plt.title("Timepix3 pixel array", fontsize=30)
        plt.text(20,0, 't={0:.3e}'.format(i), animated=True, fontsize=18, ha="center",va="bottom")
        plt.imshow(data, cmap="hot")
        plt.axis('off')
        plt.xticks([])
        plt.yticks([])
        
        # take a snap shot to animate
        camera.snap()
    
    
    # render and save animation
    animation = camera.animate()
    animation.save(out_file)
    
    return 0