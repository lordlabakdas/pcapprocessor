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

import csv
from numpy import *
from ConfigParser import *


# write metrics statistics along with labels to csv file
def csvWriter(metrics, xArray, scenario, config, pcapFile):
    transProt = config.get(scenario, "transProt").split(",")
    pcapName = config.get(scenario, "pcapFile")
    for i in range(len(transProt)):
        if (pcapName + "-" + str(i) + "-0.pcap") == pcapFile:
            prot = transProt[i] + str(i)
    csvName = config.get(scenario, "csvName") + "_" + prot + ".csv"
    labels = [
        [
            "x-scale",
            "avg_tx_packets",
            "std_tx_packets",
            "confInt_tx_packets",
            "avg_overhead",
            "std_overhead",
            "confInt_overhead",
            "avg_throughput",
            "std_througput",
            "confInt_throughput",
            "avg_delay",
            "std_delay",
            "confInt_delay",
            "avg_goodput",
            "std_goodput",
            "confInt_goodput",
            "avg_cum_goodput",
            "std_cum_goodput",
            "confInt_cum_goodput",
            "avg_retxPackets",
            "std_retxPackets",
            "confInt_retxPackets",
            "avg_utilization",
            "std_utilization",
            "confInt_utilization",
            "avg_queue_mean",
            "std_queue_mean",
            "confInt_queue_mean",
            "avg_queue_variance",
            "std_queue_variance",
            "confInt_queue_variance",
            "avg_queue_percentage",
            "std_queue_percentage",
            "confInt_queue_percentage",
            "avg_flow_cmp_time",
            "std_flow_cmp_time",
            "confInt_flow_cmp_time",
        ]
    ]
    metrics = column_stack((xArray, metrics))
    labeldMetrics = vstack((labels, metrics))
    with open(csvName, "wb") as fl:
        writer = csv.writer(fl, delimiter="\t")
        print
        "Saving to file"
        writer.writerows(labeldMetrics)
