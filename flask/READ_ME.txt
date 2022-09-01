===================================================================================
                        FLASK GUI FOR TIMEPIX3 DATA SIMULATIONS
===================================================================================
                                    David Amorim (2538354a@student.gla.ac.uk), 2022

General:
--------
The files in this package provide functionality to generate and visualise simulated
hit data for the Timepix3 ASIC in ToA & ToT mode and ToA Only mode (with superpixel
VCO enabled) using a graphical user interface.

File Structure:
---------------
Due to various dependencies the file structure in this package should not be changed!

The directories "static" and "templates" contain the CSS and HTML files which form 
the basis of the GUI. The python code responsible for generating the simulated data 
and the visualisation is stored in the directory "timepix3". The code is commented and
comes with an additional READ ME file. It is self-containted and can be used 
independently of the GUI. The directories "input" and "output" are used for data handling
and can be deleted or altered without consequence. Finally, the python file "flask_app.py"
uses Flask to link the CSS and HTML files to the python code and thus enables the GUI.   

Requirements:
-------------
The following python modules are required:
 - numpy
 - pandas
 - matplotlib
 - celluloid
 - flask 
Any missing our outdated module can be installed in the terminal using pip:
 >>> pip install --upgrade <module_name>

Usage:
------
Once the GUI is launched, its usage is self-explanatory. To launch the GUI, execute the 
file "flask_app.py" in the terminal. This will launch a local server at 

					http://localhost:5000               
	(or, equivalently:  http://127.0.0.1:5000)

which can be accessed via a browser or by clicking the link that will appear in the
terminal. The GUI is launched by accessing the above server. 

An example session in the terminal (once in the appropriate directory) might look like 
this: 

>>> python3 flask_app.py
	 * Serving Flask app 'flask_app' (lazy loading)
 	 * Environment: production
 	   WARNING: This is a development server. Do not use it in a production deployment.
   	   Use a production WSGI server instead.
 	 * Debug mode: off
 	 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)

The server will keep running until shut down using CTRL+C. Note that changes in the code
will not become active until the server has been re-started. 

Potential Issues and Fixes:
---------------------------
Issues with the GUI might arise if, e.g. 
	- a "submit" button is repeatedly pressed without leaving time to process the request;
	- invalid input is given (e.g. files chosen which are subsequently deleted or moved)'
This might result in corrupted output files, error messages in the terminal or an "Internal
Server Issue" error message in the GUI. Please note that ALL OF THESE PROBLEMS CAN BE RESOLVED
BY RE-STARTING THE SERVER! 

Generally, try to avoid interrupting the kernel while processing takes place. It may take 
several seconds or minutes to generate visualisations with a high number of frames or data 
simulations with a high number of hits. Submitting any further requests while the page is still
loading will most likely result in a crash. 


	
