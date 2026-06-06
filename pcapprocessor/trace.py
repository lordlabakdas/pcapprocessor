import re
from collections import defaultdict

import numpy as np
import pyshark


class _FlowAccumulator:
    """Accumulates per-packet stats for one TCP flow direction."""

    def __init__(self):
        self.tx_packets = 0
        self.unique_bytes = 0
        self.rexmt_packets = 0
        self.first_ts = None
        self.last_ts = None
        self.rtt_samples = []

    def add_packet(self, ts: float, payload_len: int, is_retrans: bool, rtt_ms) -> None:
        if self.first_ts is None:
            self.first_ts = ts
        self.last_ts = ts
        if payload_len > 0:
            self.tx_packets += 1
            if is_retrans:
                self.rexmt_packets += 1
            else:
                self.unique_bytes += payload_len
        if rtt_ms is not None:
            self.rtt_samples.append(rtt_ms)

    @property
    def tx_time(self) -> float:
        if self.first_ts is None:
            return 0.0
        return max(self.last_ts - self.first_ts, 0.0)

    @property
    def avg_rtt_ms(self) -> float:
        return float(np.mean(self.rtt_samples)) if self.rtt_samples else 0.0


class TraceProcessor:
    PACKET_OVERHEAD = 32  # TCP header with timestamp option

    def __init__(
        self,
        pcap_file: str,
        unit: str,
        config,
        scenario: str,
        ascii_trace_file: str = None,
        buf_size: int = 0,
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

        if self.ascii_trace_file is not None:
            pkt_size = int(self.config.get(self.scenario, "pktSize"))
            with open(self.ascii_trace_file) as fl:
                axis_y1 = [int(ln.strip().split(",")[1]) for ln in fl]
            a = np.array(axis_y1)
            queue_mean = float(a.mean())
            queue_variance = float(a.var())
            queue_pct = round(queue_mean * 100.0 / (self.buf_size / pkt_size), 3)
        else:
            queue_mean = queue_variance = queue_pct = 0.0

        flow = self._dominant_flow()
        if flow is None:
            raise ValueError("No TCP connections found in pcap file")

        tx_time = flow.tx_time
        throughput = flow.unique_bytes / tx_time if tx_time > 0 else 0.0
        utilization = throughput * 100.0 / bn_speed if bn_speed > 0 else 0.0

        return [
            flow.tx_packets,
            self.PACKET_OVERHEAD * flow.tx_packets,
            round(throughput / fact_by, 3),
            round(flow.avg_rtt_ms / 2, 3),
            round(throughput * 8 / fact_by, 3),
            flow.unique_bytes,
            flow.rexmt_packets,
            round(utilization, 3),
            round(queue_mean, 3),
            round(queue_variance, 3),
            queue_pct,
            round(tx_time * 1000, 3),
        ]

    def _dominant_flow(self):
        """Return the flow accumulator with the most unique bytes, or None."""
        flows = defaultdict(_FlowAccumulator)
        cap = pyshark.FileCapture(
            self.pcap_file,
            display_filter="tcp",
            keep_packets=False,
        )
        try:
            for pkt in cap:
                self._process_packet(pkt, flows)
        finally:
            cap.close()
        if not flows:
            return None
        best = max(flows.values(), key=lambda f: f.unique_bytes)
        return best if best.unique_bytes > 0 else None

    @staticmethod
    def _process_packet(pkt, flows) -> None:
        try:
            tcp = pkt.tcp
            key = (int(tcp.stream), pkt.ip.src, tcp.srcport, pkt.ip.dst, tcp.dstport)
            ts = float(pkt.sniff_timestamp)
            payload_len = int(tcp.len) if hasattr(tcp, "len") else 0
            is_retrans = hasattr(tcp, "analysis_retransmission")
            rtt_ms = float(tcp.analysis_ack_rtt) * 1000 if hasattr(tcp, "analysis_ack_rtt") else None
            flows[key].add_packet(ts, payload_len, is_retrans, rtt_ms)
        except AttributeError:
            pass

    def _unit_factor(self) -> float:
        first, second = list(self.unit)
        scale = {"K": 1_000, "M": 1_000_000, "G": 1_000_000_000}
        byte = {"B": 8, "b": 1}
        return scale.get(first, 1) * byte.get(second, 1)

    def _bottleneck_speed(self, fact_by: float) -> float:
        sp = self.config.get(self.scenario, "bottleneckSpeed")
        bn_speed = int(re.search(r"(\d+)", sp).group())
        return bn_speed * fact_by
