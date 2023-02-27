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

import os
import cfgPbsWriter
from cfgPbsWriter import *


scenario = "error"
error = [0]
script = "script = single-multiple-flow"
simTime = [600]
runs = "runs = 1"
pktSize = "pktSize = 1500"
accessSpeed = "accessSpeed = 10Gbps"
accessDelay = "accessDelay = 0.1ms"
pcapFile = "pcapFile = /tmp/"
csvName = "csvName = "
qSize = [0.2, 0.4, 0.6, 0.8, 1]
outputFactor = "outputFactor = Mb"
dceProt = "dceProt = "
qSizeFileName = "qSizeFileName = "
cmd = (
    "cmd = /work/siddharth/ns-3/dce-Nov15/dce/source/ns-3-dce/build/bin/%(script)s"
    " --error=%(x)s --seed=%(runNo)s --pktSize=%(pktSize)s"
    " --accessSpeed=%(accessSpeed)s --accessDelay=%(accessDelay)s"
    " --bottleneckSpeed=%(bottleneckSpeed)s --bottleneckDelay=%(bottleneckDelay)s"
    " --pcapFile=%(pcapFile)s --queue_size=%(queue_size)s --dceProt=%(dceProt)s"
    " --stopTime=%(stopTime)s --qMonitoring=%(qMonitoring)s"
    " --qSizeFileName=%(qSizeFileName)s"
)
speed = [2000, 4000, 6000, 8000, 10000]
speedUnit = "Mbps"
delay = [10, 50, 100, 150, 200, 250]
tcpVariants = [
    "bic,bic",
    "cubic,cubic",
    "htcp,htcp",
    "highspeed,highspeed",
    "yeah,yeah",
    "scalable,scalable",
    "illinois,illinois",
    "bic,reno",
    "cubic,reno",
    "htcp,reno",
    "highspeed,reno",
    "yeah,reno",
    "scalable,reno",
    "illinois,reno",
]
delayUnit = "ms"

jobsDir = "mul-flows-Jan15_11-18"  # look into this later
driverFileName = "driver.sh"
driverFileName = os.path.join(jobsDir, driverFileName)

# Write config files in current directory

for err in error:
    for q in qSize:
        for sim in simTime:
            for spe in speed:
                for de in delay:
                    for tcp in tcpVariants:
                        bottleneckSpeed = "bottleneckSpeed = " + str(spe) + speedUnit
                        bottleneckDelay = "bottleneckDelay = " + str(de) + delayUnit
                        stopTime = "stopTime = " + str(sim)
                        bdpQsz = "bdpQsz = " + str(q)
                        errorValue = "error = " + str(err)
                        tcpNoComma = tcp.replace(",", "-")
                        cfgID = (
                            scenario
                            + "_"
                            + str(err)
                            + "_"
                            + str(spe)
                            + speedUnit
                            + "_"
                            + str(de)
                            + delayUnit
                            + "_"
                            + str(sim)
                            + "_"
                            + str(q)
                            + "_"
                            + tcpNoComma
                        )
                        cfgFileName = cfgID + ".cfg"
                        qMonFileName = "qSizeFileName = " + cfgID + ".mon"
                        cfgFile = open(cfgFileName, "wb")
                        cfgFile.write("[" + scenario + "]" + "\n")
                        cfgFile.write(errorValue + "\n")
                        cfgFile.write(script + "\n")
                        cfgFile.write(runs + "\n")
                        cfgFile.write(pktSize + "\n")
                        cfgFile.write(accessSpeed + "\n")
                        cfgFile.write(accessDelay + "\n")
                        cfgFile.write(bottleneckSpeed + "\n")
                        cfgFile.write(bottleneckDelay + "\n")
                        cfgFile.write(pcapFile + cfgID + "\n")
                        cfgFile.write(csvName + cfgID + "\n")
                        cfgFile.write(bdpQsz + "\n")
                        cfgFile.write(outputFactor + "\n")
                        cfgFile.write(dceProt + tcp + "\n")
                        cfgFile.write(stopTime + "\n")
                        cfgFile.write(qMonFileName + "\n")
                        cfgFile.write(bdpQsz + "\n")
                        cfgFile.write(cmd + "\n")
                        cfgFile.close()
                        cfgPbsWriter(cfgFileName, jobsDir)

# create a shell script to qsub all pbs jobs
driverFile = open(driverFileName, "wb")
for files in os.listdir(jobsDir):
    if files.endswith(".pbs"):
        driverFile.write("qsub " + files + "\n")
driverFile.close()
