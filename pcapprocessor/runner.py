import os
import shlex
from configparser import ConfigParser
from glob import glob

import numpy as np

from pcapprocessor.metrics import MetricsWriter
from pcapprocessor.simulation import WafCommandBuilder
from pcapprocessor.stats import MetricStats, XScaleArray
from pcapprocessor.trace import TraceProcessor
from pcapprocessor import exe_comm


class SimulationRunner:
    def __init__(self, x: str, num_metrics: int, scenario: str, config: ConfigParser):
        self.x = x
        self.num_metrics = num_metrics
        self.scenario = scenario
        self.config = config

    def run(self) -> tuple[np.ndarray, list]:
        runs = self.config.getint(self.scenario, "runs")
        pcap_name = self.config.get(self.scenario, "pcapFile")
        output_factor = self.config.get(self.scenario, "outputFactor")
        num_flows = len(self.config.get(self.scenario, "transProt").split(","))
        ascii_file_name = self.config.get(self.scenario, "qSizeFileName")
        run_stats = np.zeros((num_flows, runs, self.num_metrics))

        for run in range(runs):
            run_no = str(run + 1)
            waf_cmd, q_size = WafCommandBuilder(run_no, self.x, self.scenario, self.config).build()
            print(waf_cmd)
            exe_comm.exe_comm(shlex.split(waf_cmd), capture=False)

            pcap_files = glob(pcap_name + "*.pcap")
            ascii_file = glob(ascii_file_name)
            if not ascii_file:
                raise ValueError(f"No ASCII trace files found matching: {ascii_file_name!r}")

            for p, item in enumerate(pcap_files):
                run_stats[p, run, :] = np.array(
                    TraceProcessor(
                        item, output_factor, self.config,
                        self.scenario, ascii_file[0], q_size,
                    ).process()
                )
                os.remove(item)

        return run_stats, pcap_files


class BfsRunner:
    NUM_METRICS = 12

    def __init__(self, config_file: str, scenario: str):
        self.config_file = config_file
        self.scenario = scenario

    def run(self) -> None:
        config = ConfigParser()
        config.read(self.config_file)

        xscale = config.get(self.scenario, self.scenario).split(",")
        num_flows = len(config.get(self.scenario, "transProt").split(","))
        runs = config.getint(self.scenario, "runs")

        x_array = XScaleArray(xscale).to_array()
        stats = np.zeros((num_flows, 3, self.NUM_METRICS))
        metrics = np.zeros((num_flows, len(x_array), self.NUM_METRICS * 3))

        for x in xscale:
            run_stats, pcap_files = SimulationRunner(
                x, self.NUM_METRICS, self.scenario, config
            ).run()
            for p in range(len(pcap_files)):
                stats[p, :, :] = MetricStats(
                    run_stats[p, :, :], self.NUM_METRICS, runs
                ).calculate()
                metrics[p, xscale.index(x)] = np.array(
                    stats[p, :, :].reshape(1, self.NUM_METRICS * 3, order="F").copy()
                )

        for pcap_file in pcap_files:
            MetricsWriter(
                metrics[pcap_files.index(pcap_file), :],
                x_array, self.scenario, config, pcap_file,
            ).write()
