from pathlib import Path

from pcapprocessor.metrics import MetricsWriter
from pcapprocessor.trace import TraceProcessor


class PcapProcessor:
    def __init__(
        self,
        pcap_file_path: str,
        unit: str,
        config,
        scenario: str,
        ascii_trace_file: str,
        buf_size: int,
    ):
        self.pcap_file_path = str(Path(pcap_file_path))
        self.unit = unit
        self.config = config
        self.scenario = scenario
        self.ascii_trace_file = ascii_trace_file
        self.buf_size = buf_size

    def process(self) -> list:
        return TraceProcessor(
            self.pcap_file_path,
            self.unit,
            self.config,
            self.scenario,
            self.ascii_trace_file,
            self.buf_size,
        ).process()

    def process_and_write(self, x_array, pcap_file: str) -> None:
        metrics = self.process()
        MetricsWriter(
            metrics, x_array, self.scenario, self.config, pcap_file
        ).write()
