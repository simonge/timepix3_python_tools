#  -------------------------------------------------------------------------------------
#  "flask_app.py" - Implements Flask GUI for Timepix3 Simulations
#  -------------------------------------------------------------------------------------
#
#  This file contains functions to implement a Graphical User Interface to generate and
#  visualise Timepix3 data simulations in Flask.
#
#
#  Execute this file in the terminal as a regular python file. This will launch a local
#  server at
#
#        http://localhost:5000               (or, equivalently:  http://127.0.0.1:5000)
#
#  which can be accessed via a browser or by clicking the link that will appear in the
#  terminal. This starts the GUI. Note that changes to the code will not become active
#  in the GUI until the server has been re-started by re-executing this file.
#
#
#  Numpy and Flask are required, as well as the functions "simulate()" and "visualise()" which
#  are defined in "generate.py".
#
#
#                                                                    David Amorim, 2022


# import relevant modules
from flask import Flask, render_template, request, send_file
from timepix3.generate import simulate, visualise
from werkzeug.utils import secure_filename
import shutil
import numpy as np
import os


# initiate Flask application
app = Flask(__name__)


# set up home page at "http://localhost:5000" based on the template "index.html":

@app.route('/')
def index():
    return render_template('index.html')


# set up page at "http://localhost:5000/info" to display background information
#    (based on the Read Me file provided with the python code)

@app.route('/info')
def print_info():
   return render_template('read_me.html')


# zip up the python code files and download; triggered by visiting "http://localhost:5000/code"
# which is linked on the starting page

@app.route('/code')
def download_code():

    # zip code files
    shutil.make_archive('./output/timepix3', 'zip', './timepix3')

    # download zip file
    filename= os.path.join('output', 'timepix3.zip')
    return send_file(filename, as_attachment=True)

# generate simulated data based on form input, zip up output files and download;
# triggered by filling in the input forms on the starting page and pressing the
# "submit" button

@app.route('/processing', methods=['POST'])
def processing():

    # read form input
    N=int(request.form['hits'])
    op_mode=int(request.form['op_mode'])

    # generate data
    simulate(N, op_mode)

    # zip output files
    if not os.path.exists('./output/data'):
        os.mkdir('./output/data')
    shutil.move('packets.bin','./output/data/packets.bin')
    shutil.move('values.csv','./output/data/values.csv')
    shutil.make_archive('./output/sim_data','zip','./output/data' )

    # download files
    filename= os.path.join('output', 'sim_data.zip')
    return send_file(filename, as_attachment=True)


# read in a csv file with input data and return (automatically download) an animated GIF;
# triggered by filling in the input form on the starting page and pressing "submit"

@app.route('/visualising', methods=['POST'])
def visualising():

    # read form input
    steps=int(request.form['frames'])
    input_file=request.files['in_file']
    if not os.path.exists('./input'):
        os.mkdir('./input')
    in_file=os.path.join('input', secure_filename(input_file.filename))
    input_file.save(in_file)

    # create visualisation
    visualise(steps)
    out_file=os.path.join('output', 'timepix_simulations.gif')

    # download file
    return send_file(out_file, as_attachment=True)


# run Flask app when python file is executed:

if __name__ == '__main__':
    app.run()
