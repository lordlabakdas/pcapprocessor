import csv

import numpy as np


METRIC_LABELS = [
    "x-scale",
    "avg_tx_packets", "std_tx_packets", "confInt_tx_packets",
    "avg_overhead", "std_overhead", "confInt_overhead",
    "avg_throughput", "std_throughput", "confInt_throughput",
    "avg_delay", "std_delay", "confInt_delay",
    "avg_goodput", "std_goodput", "confInt_goodput",
    "avg_cum_goodput", "std_cum_goodput", "confInt_cum_goodput",
    "avg_retxPackets", "std_retxPackets", "confInt_retxPackets",
    "avg_utilization", "std_utilization", "confInt_utilization",
    "avg_queue_mean", "std_queue_mean", "confInt_queue_mean",
    "avg_queue_variance", "std_queue_variance", "confInt_queue_variance",
    "avg_queue_percentage", "std_queue_percentage", "confInt_queue_percentage",
    "avg_flow_cmp_time", "std_flow_cmp_time", "confInt_flow_cmp_time",
]


class MetricsWriter:
    def __init__(self, metrics, x_array, scenario: str, config, pcap_file: str):
        self.metrics = metrics
        self.x_array = x_array
        self.scenario = scenario
        self.config = config
        self.pcap_file = pcap_file

    def write(self) -> None:
        csv_name = self._resolve_csv_name()
        labelled = np.vstack(([METRIC_LABELS], np.column_stack((self.x_array, self.metrics))))
        with open(csv_name, "w", newline="") as fl:
            writer = csv.writer(fl, delimiter="\t")
            writer.writerows(labelled)

    def _resolve_csv_name(self) -> str:
        trans_prots = self.config.get(self.scenario, "transProt").split(",")
        pcap_base = self.config.get(self.scenario, "pcapFile")
        prot = ""
        for i, item in enumerate(trans_prots):
            if (pcap_base + "-" + item + str(i) + "-0.pcap") == self.pcap_file:
                prot = item + str(i)
        return self.config.get(self.scenario, "csvName") + "_" + prot + ".csv"
