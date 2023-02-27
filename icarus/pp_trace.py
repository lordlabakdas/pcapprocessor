## -*- Mode:Python; -*- ##
##
## Copyright (c) 2018 ResiliNets, ITTC, University of Kansas
##
## Author: Santosh Gondi
##
## James P.G. Sterbenz <jpgs@ittc.ku.edu>, director
## ResiliNets Research Group  http://wiki.ittc.ku.edu/resilinets
## Information and Telecommunication Technology Center (ITTC)
## and Department of Electrical Engineering and Computer Science
## The University of Kansas Lawrence, KS USA.
##


# Single connection version.
# output format [tx_packets, overhead, throughput, delay, goodput, cumm_goodput, rexmt_packets, utilization
#         queue_mean, queue_variance, queue_percentage, flow_cmp_time, numpy_obj ]


import re
import sys
import datetime
import shlex
import exe_comm
from ConfigParser import *
from numpy import *


# input to this fuction are, a pcap file and date rate unit
def pp_trace(pcap_file, unit, config, scenario, ascii_trace_file, buf_size):
    # supported data rate units are : KB, Kb, MB, Mb, GB, Gb
    # anything other are treated as b/s

    first, second = list(unit)
    scale_dict = {"K": 1000, "M": 1000000, "G": 1000000000}
    byte_dict = {"B": 8, "b": 1}
    scale_unit = scale_dict[first] if first in scale_dict else 1
    byte_unit = byte_dict[second] if second in byte_dict else 1
    fact_by = scale_unit * byte_unit
    # config = ConfigParser()
    # config.read(config_file)
    sp = config.get(scenario, "bottleneckSpeed")
    # extract the numeric value from bottleneck field
    bn_speed = int(re.search(r"(\d+)", sp).group())
    bn_speed = bn_speed * fact_by

    PACKET_OVERHEAD = 32  # TCP header with timestamp option

    print("Processing ascii trace output")
    pktSize = int(config.get(scenario, "pktSize"))
    fl = open(ascii_trace_file, "r")
    ascii_trace_lines = list(fl)
    axis_x = [double(line.strip().split(",")[0]) for line in ascii_trace_lines]
    axis_y1 = [int(line.strip().split(",")[1]) for line in ascii_trace_lines]

    a = array(axis_y1)
    queue_mean = a.mean()
    queue_variance = a.var()
    array([axis_x, axis_y1])

    trace_cmd = "tcptrace -l -r -n -W --csv " + pcap_file

    print("Executing tcptrace command. it may take few seconds")
    result = exe_comm.exe_comm(shlex.split(trace_cmd))

    print("Processing trace output")

    pcap_trace_lines = result.split("\n")

    regex_con = re.compile("#([0-9]*) TCP connection traced:")

    # find the index of lines in trace containing 'TCP connection X:'
    matches = [
        pcap_trace_lines.index(ln) for ln in pcap_trace_lines if re.match(regex_con, ln)
    ]

    if len(matches) <= 0:
        print("No TCP connections found")
        sys.exit()

    # create a list of TCP connections, each list contains lines in trace for that connection
    connections_list = [
        pcap_trace_lines[matches[j] : matches[j + 1]] for j in range(len(matches) - 1)
    ]
    connections_list.append(pcap_trace_lines[matches[-1] :])

    # following parsing is dependent on the tcptrace long format.
    result_str = "\n"
    for i in range(len(connections_list)):
        flow_cmp_time = 0
        try:
            time_stamp = pcap_trace_lines[matches[i] - 2].split()[-1]
            t = datetime.datetime.strptime(time_stamp, "%H:%M:%S.%f")
            flow_cmp_time = (
                t.time().hour * 60 * 60 + t.time().minute * 60 + t.time().second
            ) * 1000 + (t.time().microsecond / 1000)
        except:
            print("Couldn't parse the flow completion time")

        item = connections_list[i]
        item[0]
        labels = item[1].split(",")
        values = item[3].split(",")

        conn_suffix = "a2b"
        # hack for incomplete connections
        if int(values[labels.index("unique_bytes_sent_a2b")]) <= 0:
            conn_suffix = "b2a"

        values[labels.index("host_a")]
        values[labels.index("host_b")]
        tx_packts = int(values[labels.index("total_packets_" + conn_suffix)])
        rexmt_packts = int(values[labels.index("rexmt_data_pkts_" + conn_suffix)])
        overhead = PACKET_OVERHEAD * int(
            values[labels.index("total_packets_" + conn_suffix)]
        )
        goodput = 8 * int(values[labels.index("throughput_" + conn_suffix)])
        unique_bytes = int(values[labels.index("unique_bytes_sent_" + conn_suffix)])
        tx_time = (1.0 * unique_bytes) / goodput
        throughput = int(values[labels.index("actual_data_bytes_" + conn_suffix)]) / (
            tx_time
        )
        rtt = float(values[labels.index("RTT_avg_" + conn_suffix)]) / 2
        utilization = throughput * 100.0 / bn_speed

        # output formatting...
        # print host_a + ' -> ' +host_b
        result_str = [
            tx_packts,
            overhead,
            round(throughput / fact_by, 3),
            round(rtt, 3),
            round(goodput / fact_by, 3),
            unique_bytes,
            rexmt_packts,
            round(utilization, 3),
            round(queue_mean, 3),
            round(queue_variance, 3),
            round(queue_mean * 100.0 / (buf_size / pktSize), 3),
            round(flow_cmp_time, 3)
            # numpy_obj
        ]

        # b -> a: TODO
        # print (result_str)
    return result_str
    # fl.close()


# Testing
# print pp_trace('../dump123.pcap','Mb','../error_10Mbps_100ms_20_cubic-reno.cfg', 'error','../routerQueueSize.txt', 61362)
