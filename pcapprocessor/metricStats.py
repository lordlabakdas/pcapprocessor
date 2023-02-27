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

from numpy import *
from confInt import *


def metricStats(runStats, numMetrics, runs):
    meanArray = runStats.mean(axis=0)
    if runs > 1:
        stdArray = runStats.std(axis=0)
        confArray = zeros(shape=(1, numMetrics))
        for col in range(numMetrics):
            confArray[0, col] = ConfInt(runStats[:, col])
        confArray = array(confArray.flatten())
    elif runs == 1:
        stdArray = zeros(shape=(1, numMetrics)).flatten()
        confArray = zeros(shape=(1, numMetrics)).flatten()
    stats = array([meanArray, stdArray, confArray])
    return stats
