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

from ConfigParser import *
import calcQsz
from calcQsz import *


def wafCmd(runNo, x, scenario, config):
    queue_size = calcQsz(scenario, x, config)
    runs = config.getint(scenario, "runs")
    if runs == 1:
        qMonitoring = 1
    else:
        qMonitoring = 0
    if scenario == "bottleneckDelay" or scenario == "changingDelay":
        x = x + "ms"
    elif scenario == "bottleneckSpeed":
        x = x + "Mbps"
    waf_cmd = config.get(
        section=scenario,
        option="cmd",
        vars=dict(queue_size=queue_size, x=x, runNo=runNo, qMonitoring=qMonitoring),
    )
    qSize = int(queue_size)
    return waf_cmd, qSize
