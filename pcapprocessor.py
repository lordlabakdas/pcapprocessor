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


if __name__ == "__main__":
    import sys
    from configparser import ConfigParser

    if len(sys.argv) < 7:
        print(
            "Usage: python pcapprocessor.py <pcap_file> <unit> <config_file>"
            " <scenario> <ascii_trace_file> <buf_size>"
        )
        sys.exit(1)

    cfg = ConfigParser()
    cfg.read(sys.argv[3])

    proc = PcapProcessor(
        pcap_file_path=sys.argv[1],
        unit=sys.argv[2],
        config=cfg,
        scenario=sys.argv[4],
        ascii_trace_file=sys.argv[5],
        buf_size=int(sys.argv[6]),
    )
    result = proc.process()
    print(result)
