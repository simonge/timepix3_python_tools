===================================================================================
                           DATA SIMULATIONS FOR TIMEPIX3
===================================================================================
                                    David Amorim (2538354a@student.gla.ac.uk), 2022

General:
--------
The Python files "counters.py", "time_conversion.py", "hits.py" , "packing.py" and 
"generate.py" together provide functionality to generate simulated hit data for the 
Timepix3 ASIC in ToA & ToT mode and ToA Only mode (with superpixel VCO enabled).

Requirements:
-------------
Due to various dependencies the files should be kept in the same  directory to ensure
the code runs without problems. The "numpy" and "pandas" modules are also required to 
execute most relevant functions. The module "warnings" is used to surpress some 
compiler outputs but not relevant to code execution. The modules "matplotlib" and 
"celluloid" are needed to visualise hit data (using the function "visualise()" in
"generate.py").
Any missing our outdated modules can be installed or upgraded using pip:
    >>> pip install --upgrade <module>

Help:
-----
Each file contains a detailed header comment as well as various in-line comments 
giving information on individual functions. Reference is made to the Timepix3 Manual
v1.9 at various points. 

Usage:
------
The function "simulate()" in "generate.py" is a general-purpose function to generate 
random hit data. It processes the hits and writes the resulting 48-bit packets to a 
binary output file. Further, a csv file containing the pixel address, timing data 
and decoded pixel counter values for each generated hit is created. 
The function takes the following arguments:
        - N: integer number of detections to be generated
        - op_mode: operation mode; 0 for ToA & ToT, 1 for ToA Only [optional; default: 0]
        - bin_name: name of the binary output file [optional; default: "packets.bin"]
        - csv_name: name of the csv output file [optional; default: "values.csv"]
If the function executes without error it returns "0". 

As an example, the following terminal input (in the appropriate directory) will generate
150 hits in ToA & ToT mode (with default names for the output files):
    [user dir]$  python3
    >>> from generate import simulate
    >>> simulate(150)
    0
    >>>
    
Using the comments and descriptions provided in the individual files, functions can also
be combined into more purpose-built tools for specific applications involving Timepix3 pixel
encoding/decoding, packing/unpacking of bit packets, etc. A useful tool, for example, is 
the function "visualise()" in "generate.py" which can be used to create animated gifs to
visualise hit data.  

Computational Time:
-------------------
Most of the code in this package was not written with optimisation of computational time in mind. 
This results in rather slow execution for larger data sets. The results of some tests on the 
function "simulate()" (described above) are shown below. They indicate that the time it takes to 
generate a given number of hits scales linearly with the number of hits, taking ~10ms for each hit:

            nmbr of hits:  time                
            10          :  ~0.1s              
            100         :  ~1s                
            1000        :  ~10s               
            10,000      :  ~120s              
            100,000     :  ~1100s

NOTE THAT A SINGLE GENERATED PARTICLE DETECTION CORRESPONDS TO ~10 GENERATED HITS DUE TO CLUSTERING. 
