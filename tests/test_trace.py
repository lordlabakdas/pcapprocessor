import pytest
from configparser import ConfigParser
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pcapprocessor.trace import TraceProcessor, _FlowAccumulator


def _make_config(scenario="myScenario"):
    config = ConfigParser()
    config[scenario] = {"pktSize": "100", "bottleneckSpeed": "10Mbps"}
    return config


def _make_processor(tmp_path, scenario="myScenario", unit="MB", buf_size=1000):
    ascii_file = tmp_path / "qsize.txt"
    ascii_file.write_text("0,100\n0,200\n")
    return TraceProcessor(
        pcap_file=str(tmp_path / "test.pcap"),
        unit=unit,
        config=_make_config(scenario),
        scenario=scenario,
        ascii_trace_file=str(ascii_file),
        buf_size=buf_size,
    )


def _fake_pkt(stream="0", src="1.1.1.1", srcport="1234",
              dst="2.2.2.2", dstport="80",
              payload_len=1000, ts=0.0,
              is_retrans=False, rtt_ms=None):
    """SimpleNamespace fake pyshark packet — hasattr behaves naturally."""
    tcp = SimpleNamespace(stream=stream, srcport=srcport, dstport=dstport, len=str(payload_len))
    if is_retrans:
        tcp.analysis_retransmission = "1"
    if rtt_ms is not None:
        tcp.analysis_ack_rtt = str(rtt_ms / 1000)
    ip = SimpleNamespace(src=src, dst=dst)
    pkt = SimpleNamespace(tcp=tcp, ip=ip)
    pkt.sniff_timestamp = str(ts)
    return pkt


def _mock_cap(packets):
    cap = MagicMock()
    cap.__iter__ = MagicMock(return_value=iter(packets))
    return cap


# --- _FlowAccumulator ---

def test_flow_accumulator_tracks_unique_bytes():
    acc = _FlowAccumulator()
    acc.add_packet(0.0, 500, False, None)
    acc.add_packet(1.0, 300, False, 10.0)
    assert acc.unique_bytes == 800
    assert acc.tx_packets == 2


def test_flow_accumulator_separates_retransmissions():
    acc = _FlowAccumulator()
    acc.add_packet(0.0, 1000, False, None)
    acc.add_packet(0.5, 500, True, None)
    assert acc.unique_bytes == 1000
    assert acc.rexmt_packets == 1
    assert acc.tx_packets == 2


def test_flow_accumulator_tx_time():
    acc = _FlowAccumulator()
    acc.add_packet(1.0, 100, False, None)
    acc.add_packet(3.5, 100, False, None)
    assert acc.tx_time == pytest.approx(2.5)


def test_flow_accumulator_avg_rtt_ms():
    acc = _FlowAccumulator()
    acc.add_packet(0.0, 100, False, 10.0)
    acc.add_packet(1.0, 100, False, 20.0)
    assert acc.avg_rtt_ms == pytest.approx(15.0)


def test_flow_accumulator_avg_rtt_ms_empty():
    assert _FlowAccumulator().avg_rtt_ms == 0.0


def test_flow_accumulator_tx_time_no_packets():
    assert _FlowAccumulator().tx_time == 0.0


# --- _unit_factor ---

def test_unit_factor_megabytes():
    assert TraceProcessor("f.pcap", "MB", None, "s", "t.txt", 100)._unit_factor() == 8_000_000


def test_unit_factor_megabits():
    assert TraceProcessor("f.pcap", "Mb", None, "s", "t.txt", 100)._unit_factor() == 1_000_000


def test_unit_factor_kilobytes():
    assert TraceProcessor("f.pcap", "KB", None, "s", "t.txt", 100)._unit_factor() == 8_000


def test_unit_factor_gigabits():
    assert TraceProcessor("f.pcap", "Gb", None, "s", "t.txt", 100)._unit_factor() == 1_000_000_000


# --- _bottleneck_speed ---

def test_bottleneck_speed_extracts_numeric(tmp_path):
    proc = _make_processor(tmp_path)
    assert proc._bottleneck_speed(1.0) == 10.0


# --- _dominant_flow ---

def test_dominant_flow_returns_none_when_no_packets(tmp_path):
    proc = _make_processor(tmp_path)
    with patch("pcapprocessor.trace.pyshark.FileCapture", return_value=_mock_cap([])):
        assert proc._dominant_flow() is None


def test_dominant_flow_selects_flow_with_most_bytes(tmp_path):
    proc = _make_processor(tmp_path)
    pkts = [
        _fake_pkt(src="1.1.1.1", srcport="1234", dst="2.2.2.2", dstport="80",
                  payload_len=1000, ts=0.0),
        _fake_pkt(src="2.2.2.2", srcport="80", dst="1.1.1.1", dstport="1234",
                  payload_len=50, ts=0.1),
    ]
    with patch("pcapprocessor.trace.pyshark.FileCapture", return_value=_mock_cap(pkts)):
        flow = proc._dominant_flow()
    assert flow.unique_bytes == 1000


def test_dominant_flow_counts_retransmissions(tmp_path):
    proc = _make_processor(tmp_path)
    pkts = [
        _fake_pkt(payload_len=1000, ts=0.0),
        _fake_pkt(payload_len=500, ts=0.1, is_retrans=True),
    ]
    with patch("pcapprocessor.trace.pyshark.FileCapture", return_value=_mock_cap(pkts)):
        flow = proc._dominant_flow()
    assert flow.rexmt_packets == 1
    assert flow.unique_bytes == 1000


def test_dominant_flow_collects_rtt_samples(tmp_path):
    proc = _make_processor(tmp_path)
    pkts = [
        _fake_pkt(payload_len=1000, ts=0.0, rtt_ms=10.0),
        _fake_pkt(payload_len=500, ts=0.5, rtt_ms=20.0),
    ]
    with patch("pcapprocessor.trace.pyshark.FileCapture", return_value=_mock_cap(pkts)):
        flow = proc._dominant_flow()
    assert flow.avg_rtt_ms == pytest.approx(15.0)


# --- process ---

def test_process_returns_12_metrics(tmp_path):
    proc = _make_processor(tmp_path)
    pkts = [
        _fake_pkt(payload_len=1000, ts=0.0, rtt_ms=10.0),
        _fake_pkt(payload_len=1000, ts=1.0),
    ]
    with patch("pcapprocessor.trace.pyshark.FileCapture", return_value=_mock_cap(pkts)):
        result = proc.process()
    assert isinstance(result, list)
    assert len(result) == 12


def test_process_overhead_is_packet_overhead_times_tx_packets(tmp_path):
    proc = _make_processor(tmp_path)
    pkts = [_fake_pkt(payload_len=500, ts=0.0), _fake_pkt(payload_len=500, ts=1.0)]
    with patch("pcapprocessor.trace.pyshark.FileCapture", return_value=_mock_cap(pkts)):
        result = proc.process()
    assert result[1] == result[0] * TraceProcessor.PACKET_OVERHEAD


def test_process_flow_completion_time_in_ms(tmp_path):
    proc = _make_processor(tmp_path)
    pkts = [_fake_pkt(payload_len=1000, ts=0.0), _fake_pkt(payload_len=500, ts=1.0)]
    with patch("pcapprocessor.trace.pyshark.FileCapture", return_value=_mock_cap(pkts)):
        result = proc.process()
    assert result[-1] == pytest.approx(1000.0)


def test_process_raises_on_no_connections(tmp_path):
    proc = _make_processor(tmp_path)
    with patch("pcapprocessor.trace.pyshark.FileCapture", return_value=_mock_cap([])):
        with pytest.raises(ValueError, match="No TCP connections found"):
            proc.process()


def test_process_without_ascii_trace_returns_zero_queue_metrics(tmp_path):
    cfg = _make_config()
    proc = TraceProcessor(
        pcap_file="dummy.pcap",
        unit="MB",
        config=cfg,
        scenario="myScenario",
    )
    pkts = [_fake_pkt(payload_len=1000, ts=0.0), _fake_pkt(payload_len=1000, ts=1.0)]
    with patch("pcapprocessor.trace.pyshark.FileCapture", return_value=_mock_cap(pkts)):
        result = proc.process()
    assert len(result) == 12
    assert result[8] == 0.0   # queue_mean
    assert result[9] == 0.0   # queue_variance
    assert result[10] == 0.0  # queue_percentage
