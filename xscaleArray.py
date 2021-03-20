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

import numpy
from numpy import *
import pdb

def xscaleArray(xscale):
    #pdb.set_trace()
    xscaleArray = array(map(float, xscale))
    xArray=xscaleArray.reshape(len(xscaleArray),1)
    xArray=xArray.flatten()
    return xArray
