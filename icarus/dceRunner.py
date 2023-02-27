## -*- Mode:Python; -*- ##
##
## Copyright (c) 2018 ResiliNets, ITTC, University of Kansas
##
## Author: Siddharth Gangadhar
##
## James P.G. Sterbenz <jpgs@ittc.ku.edu>, director
## ResiliNets Research Group  http://wiki.ittc.ku.edu/resilinets
## Information and Telecommunication Technology Center (ITTC)
## and Department of Electrical Engineering and Computer Science
## The University of Kansas Lawrence, KS USA.
##

import sys
from sys import *
import pbsWriter
from pbsWriter import *
from ConfigParser import *
import bfsRunner
from bfsRunner import *

try:
    configFile = sys.argv[1]
    if len(sys.argv) == 2:
        pbsWriter(configFile)
    elif len(sys.argv) == 3:
        scenario = sys.argv[2]
        bfsRunner(configFile, scenario)
except IndexError:
    print("to run on cluster, python dceRunner.py [config file]")
    print("to run on BFS, python dceRunner.py [config file] [scenario]")
