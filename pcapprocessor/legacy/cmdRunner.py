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

import glob
import shlex
from glob import *

import pp_trace
import wafCmd
from ConfigParser import *
from exe_comm import *
from numpy import *
from pp_trace import *
from wafCmd import *


def cmdRunner(x, numMetrics, scenario, config):
    runs = config.getint(scenario, "runs")
    pcapName = config.get(scenario, "pcapFile")
    outputFactor = config.get(scenario, "outputFactor")
    numFlows = len(config.get(scenario, "transProt").split(","))
    asciiFileName = config.get(scenario, "qSizeFileName")
    runStats = zeros(shape=(numFlows, runs, numMetrics))
    for run in range(runs):
        runNo = str(run + 1)
        waf_cmd, qSize = wafCmd(runNo, x, scenario, config)
        print(waf_cmd)
        # execute waf command
        exe_com(shlex.split(waf_cmd))
        pcapFiles = glob(pcapName + "*.pcap")
        asciiFile = glob(asciiFileName)
        # pdb.set_trace()
        # execute tcptrace command
        for p, item in enumerate(pcapFiles):
            runStats[p, run, :] = array(
                pp_trace(
                    item, outputFactor, config, scenario, asciiFile[0], qSize
                )
            )
            exe_com(shlex.split("rm " + item))
    return (runStats, pcapFiles)
