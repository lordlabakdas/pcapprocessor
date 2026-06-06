import os
from configparser import ConfigParser

import numpy as np
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
