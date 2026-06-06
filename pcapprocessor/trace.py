import re
import sys
import shlex
import datetime

import numpy as np

from pcapprocessor import exe_comm


class TraceProcessor:
    PACKET_OVERHEAD = 32  # TCP header with timestamp option

    def __init__(
        self,
        pcap_file: str,
        unit: str,
        config,
        scenario: str,
        ascii_trace_file: str,
        buf_size: int,
    ):
        self.pcap_file = pcap_file
        self.unit = unit
        self.config = config
        self.scenario = scenario
        self.ascii_trace_file = ascii_trace_file
        self.buf_size = buf_size

    def process(self) -> list:
        fact_by = self._unit_factor()
        bn_speed = self._bottleneck_speed(fact_by)

        print("Processing ascii trace output")
        pkt_size = int(self.config.get(self.scenario, "pktSize"))
        with open(self.ascii_trace_file, "r") as fl:
            lines = list(fl)
        axis_y1 = [int(line.strip().split(",")[1]) for line in lines]
        a = np.array(axis_y1)
        queue_mean = a.mean()
        queue_variance = a.var()

        trace_cmd = "tcptrace -l -r -n -W --csv " + self.pcap_file
        print("Executing tcptrace command. it may take few seconds")
        result = exe_comm.exe_comm(shlex.split(trace_cmd))
        print("Processing trace output")

        pcap_lines = result.split("\n")
        regex_con = re.compile(r"#([0-9]*) TCP connection traced:")
        matches = [
            pcap_lines.index(ln)
            for ln in pcap_lines
            if re.match(regex_con, ln)
        ]

        if not matches:
            print("No TCP connections found")
            sys.exit()

        connections = [
            pcap_lines[matches[j]: matches[j + 1]]
            for j in range(len(matches) - 1)
        ]
        connections.append(pcap_lines[matches[-1]:])

        result_str = "\n"
        for i, item in enumerate(connections):
            flow_cmp_time = 0
            try:
                time_stamp = pcap_lines[matches[i] - 2].split()[-1]
                t = datetime.datetime.strptime(time_stamp, "%H:%M:%S.%f")
                flow_cmp_time = (
                    t.time().hour * 3600 + t.time().minute * 60 + t.time().second
                ) * 1000 + t.time().microsecond / 1000
            except Exception:
                print("Couldn't parse the flow completion time")

            labels = item[1].split(",")
            values = item[3].split(",")

            conn_suffix = "a2b"
            if int(values[labels.index("unique_bytes_sent_a2b")]) <= 0:
                conn_suffix = "b2a"

            tx_packets = int(values[labels.index("total_packets_" + conn_suffix)])
            rexmt_packets = int(values[labels.index("rexmt_data_pkts_" + conn_suffix)])
            overhead = self.PACKET_OVERHEAD * tx_packets
            goodput = 8 * int(values[labels.index("throughput_" + conn_suffix)])
            unique_bytes = int(values[labels.index("unique_bytes_sent_" + conn_suffix)])
            tx_time = (1.0 * unique_bytes) / goodput
            throughput = (
                int(values[labels.index("actual_data_bytes_" + conn_suffix)]) / tx_time
            )
            rtt = float(values[labels.index("RTT_avg_" + conn_suffix)]) / 2
            utilization = throughput * 100.0 / bn_speed

            result_str = [
                tx_packets,
                overhead,
                round(throughput / fact_by, 3),
                round(rtt, 3),
                round(goodput / fact_by, 3),
                unique_bytes,
                rexmt_packets,
                round(utilization, 3),
                round(queue_mean, 3),
                round(queue_variance, 3),
                round(queue_mean * 100.0 / (self.buf_size / pkt_size), 3),
                round(flow_cmp_time, 3),
            ]

        return result_str

    def _unit_factor(self) -> float:
        first, second = list(self.unit)
        scale = {"K": 1_000, "M": 1_000_000, "G": 1_000_000_000}
        byte = {"B": 8, "b": 1}
        return scale.get(first, 1) * byte.get(second, 1)

    def _bottleneck_speed(self, fact_by: float) -> float:
        sp = self.config.get(self.scenario, "bottleneckSpeed")
        bn_speed = int(re.search(r"(\d+)", sp).group())
        return bn_speed * fact_by
