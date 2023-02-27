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


def calcQsz(scenario, x, config):
    bdpQsz = config.getfloat(scenario, "bdpQsz")
    xscale = config.get(scenario, scenario).split(",")
    if scenario == "bottleneckDelay":
        bottleneckSpeed = config.get(scenario, "bottleneckSpeed")
        speedUnit = bottleneckSpeed[-4:]
        if speedUnit[0] == "K":
            bottleneckSpeed = 1000 * int(bottleneckSpeed[:-4])
        elif speedUnit[0] == "M":
            bottleneckSpeed = 1000000 * int(bottleneckSpeed[:-4])
        elif speedUnit[0] == "G":
            bottleneckSpeed = 1000000000 * int(bottleneckSpeed[:-4])
        queue_size = str(
            int(
                bdpQsz
                * bottleneckSpeed
                * 2
                * 0.001
                * (float(xscale[xscale.index(x)]) / 8)
            )
        )
    elif scenario == "bottleneckSpeed":
        bottleneckDelay = config.get(scenario, "bottleneckDelay")
        bottleneckDelay = int(bottleneckDelay[:-2])
        speedUnit = config.get(scenario, "speedUnit")
        if speedUnit[0] == "K":
            x = 1000 * int(x)
        elif speedUnit[0] == "M":
            x = 1000000 * int(x)
        elif speedUnit[0] == "G":
            x = 1000000000 * int(x)
        queue_size = str(int(bdpQsz * bottleneckDelay * 2 * 0.001 * (float(x / 8))))
    else:
        bottleneckDelay = config.get(scenario, "bottleneckDelay")
        bottleneckDelay = int(bottleneckDelay[:-2])
        bottleneckSpeed = config.get(scenario, "bottleneckSpeed")
        speedUnit = bottleneckSpeed[-4:]
        if speedUnit[0] == "K":
            bottleneckSpeed = 1000 * int(bottleneckSpeed[:-4])
        elif speedUnit[0] == "M":
            bottleneckSpeed = 1000000 * int(bottleneckSpeed[:-4])
        elif speedUnit[0] == "G":
            bottleneckSpeed = 1000000000 * int(bottleneckSpeed[:-4])
        queue_size = str(
            int(bdpQsz * bottleneckSpeed * 2 * 0.001 * bottleneckDelay / 8)
        )
    return queue_size
