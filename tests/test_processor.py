from configparser import ConfigParser
from unittest.mock import patch

import numpy as np

from pcapprocessor.processor import PcapProcessor


def _make_config():
    config = ConfigParser()
    config["myScenario"] = {"transProt": "tcp", "pcapFile": "/tmp/t", "csvName": ""}
    return config


def test_init_stores_all_params():
    config = _make_config()
    proc = PcapProcessor("/tmp/t.pcap", "MB", config, "myScenario", "trace.txt", 1000)
    assert proc.pcap_file_path == "/tmp/t.pcap"
    assert proc.unit == "MB"
    assert proc.scenario == "myScenario"
    assert proc.ascii_trace_file == "trace.txt"
    assert proc.buf_size == 1000


def test_process_delegates_to_trace_processor():
    config = _make_config()
    proc = PcapProcessor("/tmp/t.pcap", "MB", config, "myScenario", "trace.txt", 1000)
    fake = [1, 2, 3]
    with patch("pcapprocessor.processor.TraceProcessor") as mock_tp:
        mock_tp.return_value.process.return_value = fake
        result = proc.process()
    assert result == fake
    mock_tp.assert_called_once_with("/tmp/t.pcap", "MB", config, "myScenario", "trace.txt", 1000)


def test_process_and_write_chains_trace_and_metrics():
    config = _make_config()
    proc = PcapProcessor("/tmp/t.pcap", "MB", config, "myScenario", "trace.txt", 1000)
    x_array = np.array([1.0, 2.0])
    with (
        patch("pcapprocessor.processor.TraceProcessor") as mock_tp,
        patch("pcapprocessor.processor.MetricsWriter") as mock_mw,
    ):
        mock_tp.return_value.process.return_value = [0] * 12
        proc.process_and_write(x_array, "test.pcap")
    mock_mw.return_value.write.assert_called_once()
    mock_mw.assert_called_once_with(
        [0] * 12, x_array, "myScenario", config, "test.pcap"
    )
