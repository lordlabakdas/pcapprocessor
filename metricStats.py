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
import confInt
from confInt import *
import pdb

#calculate mean, standard deviation and confidence intervals for each metrics over multiple runs

def metricStats(runStats, numMetrics, runs):
    meanArray = runStats.mean(axis=0)
    if runs > 1:
     #   meanArray = runStats.mean(axis=0)
        stdArray = runStats.std(axis=0)
        confArray=zeros(shape=(1,numMetrics))
    #pdb.set_trace()
        for col in range(numMetrics):
            confArray[0,col]=ConfInt(runStats[:,col])
        confArray = array(confArray.flatten())
    elif runs==1:
    #    meanArray = zeros(shape=(1,numMetrics)).flatten()
        stdArray = zeros(shape=(1,numMetrics)).flatten()
        confArray = zeros(shape=(1,numMetrics)).flatten()
    stats = array([meanArray, stdArray, confArray])
#    print stats
#    print stats.shape
    #pdb.set_trace()
    return stats
    
