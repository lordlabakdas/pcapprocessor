import pytest
from configparser import ConfigParser
from unittest.mock import patch

from pcapprocessor.trace import TraceProcessor


_A2B_OUTPUT = "\n".join([
    "timestamp line 00:01:00.000000",
    "filler line",
    "#1 TCP connection traced:",
    "unique_bytes_sent_a2b,total_packets_a2b,rexmt_data_pkts_a2b,"
    "throughput_a2b,actual_data_bytes_a2b,RTT_avg_a2b",
    "extra line",
    "1000,10,0,1000,500,5.0",
    "",
])

_B2A_OUTPUT = "\n".join([
    "timestamp line 00:01:00.000000",
    "filler line",
    "#1 TCP connection traced:",
    "unique_bytes_sent_a2b,total_packets_b2a,rexmt_data_pkts_b2a,"
    "throughput_b2a,unique_bytes_sent_b2a,actual_data_bytes_b2a,RTT_avg_b2a",
    "extra line",
    "0,10,0,1000,1000,500,5.0",
    "",
])


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


def test_unit_factor_megabytes():
    proc = TraceProcessor("f.pcap", "MB", None, "s", "t.txt", 100)
    assert proc._unit_factor() == 8_000_000


def test_unit_factor_megabits():
    proc = TraceProcessor("f.pcap", "Mb", None, "s", "t.txt", 100)
    assert proc._unit_factor() == 1_000_000


def test_unit_factor_kilobytes():
    proc = TraceProcessor("f.pcap", "KB", None, "s", "t.txt", 100)
    assert proc._unit_factor() == 8_000


def test_unit_factor_gigabits():
    proc = TraceProcessor("f.pcap", "Gb", None, "s", "t.txt", 100)
    assert proc._unit_factor() == 1_000_000_000


def test_bottleneck_speed_extracts_numeric(tmp_path):
    proc = _make_processor(tmp_path)
    # bottleneckSpeed="10Mbps", fact_by=1 → 10*1 = 10
    assert proc._bottleneck_speed(1.0) == 10.0


def test_process_returns_12_metrics(tmp_path):
    proc = _make_processor(tmp_path)
    with patch("pcapprocessor.exe_comm.exe_comm", return_value=_A2B_OUTPUT):
        result = proc.process()
    assert isinstance(result, list)
    assert len(result) == 12


def test_process_a2b_tx_packets(tmp_path):
    proc = _make_processor(tmp_path)
    with patch("pcapprocessor.exe_comm.exe_comm", return_value=_A2B_OUTPUT):
        result = proc.process()
    assert result[0] == 10   # tx_packets
    assert result[1] == 320  # overhead = PACKET_OVERHEAD * tx_packets


def test_process_b2a_path_returns_12_metrics(tmp_path):
    proc = _make_processor(tmp_path)
    with patch("pcapprocessor.exe_comm.exe_comm", return_value=_B2A_OUTPUT):
        result = proc.process()
    assert isinstance(result, list)
    assert len(result) == 12


def test_process_raises_on_no_connections(tmp_path):
    proc = _make_processor(tmp_path)
    with patch("pcapprocessor.exe_comm.exe_comm", return_value="no tcp data here\n"):
        with pytest.raises(ValueError, match="No TCP connections found"):
            proc.process()


def test_process_flow_cmp_time_fallback_on_bad_timestamp(tmp_path):
    # Timestamp that can't be parsed → flow_cmp_time stays 0
    bad_ts_output = "\n".join([
        "no timestamp here",
        "filler line",
        "#1 TCP connection traced:",
        "unique_bytes_sent_a2b,total_packets_a2b,rexmt_data_pkts_a2b,"
        "throughput_a2b,actual_data_bytes_a2b,RTT_avg_a2b",
        "extra line",
        "1000,10,0,1000,500,5.0",
        "",
    ])
    proc = _make_processor(tmp_path)
    with patch("pcapprocessor.exe_comm.exe_comm", return_value=bad_ts_output):
        result = proc.process()
    assert result[-1] == 0  # flow_cmp_time defaults to 0
