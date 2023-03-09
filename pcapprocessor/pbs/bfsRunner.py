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

import cmdRunner
import ConfigParser
import csvWriter
import metricStats
import xscaleArray
from cmdRunner import *
from ConfigParser import *
from csvWriter import *
from metricStats import *
from numpy import *
from xscaleArray import *


def bfsRunner(configFile, scenario):
    config = ConfigParser()
    config.read(configFile)
    xscale = config.get(scenario, scenario).split(",")
    numFlows = len(config.get(scenario, "transProt").split(","))
    runs = config.getint(scenario, "runs")
    numMetrics = 12
    # convert xscale to a 1D array
    xArray = xscaleArray(xscale)
    # zeros matrix of needed dimensions to store metrics statistics
    stats = zeros(shape=(numFlows, 3, numMetrics))
    metrics = zeros(shape=(numFlows, len(xArray), numMetrics * 3))
    for x in xscale:
        # calculate stats for each run and store as a matrix of size (pcapFiles, runs, numMetrics)
        (runStats, pcapFiles) = cmdRunner(x, numMetrics, scenario, config)
        # calculate avg, std and conf Int for the run stats over all runs
        for p in range(len(pcapFiles)):
            stats[p, :, :] = metricStats(runStats[p, :, :], numMetrics, runs)
            # rearrange values to follow avg, std, confInt for each metric for each pcap for each x value
            metrics[p, xscale.index(x)] = array(
                stats[p, :, :].reshape(1, numMetrics * 3, order="F").copy()
            )
    # write labelled metrics to csv file once the scenario is over
    for pcapFile in pcapFiles:
        csvWriter(
            metrics[pcapFiles.index(pcapFile), :], xArray, scenario, config, pcapFile
        )
