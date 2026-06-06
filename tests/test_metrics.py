import os
from configparser import ConfigParser

import numpy as np
import pytest
from pcapprocessor.metrics import MetricsWriter


def _make_config():
    config = ConfigParser()
    config["myScenario"] = {
        "transProt": "tcp",
        "pcapFile": "/tmp/test",
        "csvName": "",
    }
    return config


def test_metrics_writer_creates_csv(tmp_path):
    config = _make_config()
    config["myScenario"]["csvName"] = str(tmp_path / "out")
    config["myScenario"]["transProt"] = "tcp"
    config["myScenario"]["pcapFile"] = "/tmp/test"

    x_array = np.array([1.0, 2.0])
    metrics = np.zeros((2, 36))  # 12 metrics * 3 stats

    pcap_file = "/tmp/test-tcp0-0.pcap"
    writer = MetricsWriter(metrics, x_array, "myScenario", config, pcap_file)
    writer.write()

    csv_path = str(tmp_path / "out") + "_tcp0.csv"
    assert os.path.exists(csv_path)


def test_metrics_writer_csv_has_correct_headers(tmp_path):
    import csv as csv_mod
    config = _make_config()
    config["myScenario"]["csvName"] = str(tmp_path / "out")

    x_array = np.array([1.0])
    metrics = np.zeros((1, 36))
    writer = MetricsWriter(metrics, x_array, "myScenario", config, "/tmp/test-tcp0-0.pcap")
    writer.write()

    csv_path = str(tmp_path / "out") + "_tcp0.csv"
    with open(csv_path, newline="") as f:
        reader = csv_mod.reader(f, delimiter="\t")
        headers = next(reader)
    assert headers[0] == "x-scale"
    assert "avg_throughput" in headers
    assert len(headers) == 37


def test_metrics_writer_raises_on_unmatched_pcap(tmp_path):
    config = _make_config()
    config["myScenario"]["csvName"] = str(tmp_path / "out")
    x_array = np.array([1.0])
    metrics = np.zeros((1, 36))
    writer = MetricsWriter(metrics, x_array, "myScenario", config, "/tmp/wrong-name.pcap")
    with pytest.raises(ValueError):
        writer.write()
