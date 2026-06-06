from configparser import ConfigParser
from unittest.mock import patch

import numpy as np
import pytest

from pcapprocessor.runner import BfsRunner, SimulationRunner


def _make_config(section="myScenario", **kwargs):
    config = ConfigParser()
    config[section] = {
        "runs": "1",
        "pcapFile": "test",
        "outputFactor": "MB",
        "transProt": "tcp",
        "qSizeFileName": "qsize.txt",
        **kwargs,
    }
    return config


def test_simulation_runner_run_returns_correct_shape(tmp_path):
    config = _make_config()
    runner = SimulationRunner("10", 12, "myScenario", config)
    fake_pcap = str(tmp_path / "test-tcp0-0.pcap")
    fake_ascii = str(tmp_path / "qsize.txt")

    with (
        patch("pcapprocessor.runner.WafCommandBuilder") as mock_waf,
        patch("pcapprocessor.runner.exe_comm.exe_comm"),
        patch("pcapprocessor.runner.glob") as mock_glob,
        patch("pcapprocessor.runner.TraceProcessor") as mock_trace,
        patch("pcapprocessor.runner.os.remove"),
    ):
        mock_waf.return_value.build.return_value = ("./waf --x=10", 100)
        mock_glob.side_effect = [[fake_pcap], [fake_ascii]]
        mock_trace.return_value.process.return_value = list(np.ones(12))

        run_stats, pcap_files = runner.run()

    assert run_stats.shape == (1, 1, 12)
    assert fake_pcap in pcap_files


def test_simulation_runner_removes_pcap_after_trace(tmp_path):
    config = _make_config()
    runner = SimulationRunner("10", 12, "myScenario", config)
    fake_pcap = str(tmp_path / "test-tcp0-0.pcap")

    with (
        patch("pcapprocessor.runner.WafCommandBuilder") as mock_waf,
        patch("pcapprocessor.runner.exe_comm.exe_comm"),
        patch("pcapprocessor.runner.glob") as mock_glob,
        patch("pcapprocessor.runner.TraceProcessor") as mock_trace,
        patch("pcapprocessor.runner.os.remove") as mock_remove,
    ):
        mock_waf.return_value.build.return_value = ("./waf", 100)
        mock_glob.side_effect = [[fake_pcap], [str(tmp_path / "qsize.txt")]]
        mock_trace.return_value.process.return_value = list(np.ones(12))

        runner.run()

    mock_remove.assert_called_once_with(fake_pcap)


def test_simulation_runner_raises_on_missing_ascii_file():
    config = _make_config()
    runner = SimulationRunner("10", 12, "myScenario", config)

    with (
        patch("pcapprocessor.runner.WafCommandBuilder") as mock_waf,
        patch("pcapprocessor.runner.exe_comm.exe_comm"),
        patch("pcapprocessor.runner.glob") as mock_glob,
    ):
        mock_waf.return_value.build.return_value = ("./waf", 100)
        mock_glob.side_effect = [["test.pcap"], []]

        with pytest.raises(ValueError, match="No ASCII trace files"):
            runner.run()


def test_bfs_runner_iterates_xscale(tmp_path):
    config_file = tmp_path / "config.cfg"
    config_file.write_text(
        "[myScenario]\n"
        "myScenario = 1,2\n"
        "transProt = tcp\n"
        "runs = 1\n"
        "pcapFile = test\n"
        "csvName = out\n"
        "bdpQsz = 1.0\n"
        "bottleneckDelay = 10ms\n"
        "bottleneckSpeed = 10Mbps\n"
        "outputFactor = MB\n"
        "qSizeFileName = qsize.txt\n"
        "cmd = run\n"
    )
    runner = BfsRunner(str(config_file), "myScenario")
    fake_stats = np.zeros((1, 1, 12))
    fake_pcaps = ["test-tcp0-0.pcap"]

    with (
        patch("pcapprocessor.runner.SimulationRunner") as mock_sim,
        patch("pcapprocessor.runner.MetricsWriter") as mock_writer,
    ):
        mock_sim.return_value.run.return_value = (fake_stats, fake_pcaps)
        runner.run()

    # one SimulationRunner call per xscale value (1 and 2)
    assert mock_sim.call_count == 2
    mock_writer.return_value.write.assert_called()


def test_bfs_runner_writes_metrics_per_flow(tmp_path):
    config_file = tmp_path / "config.cfg"
    config_file.write_text(
        "[myScenario]\n"
        "myScenario = 5\n"
        "transProt = tcp,udp\n"
        "runs = 1\n"
        "pcapFile = test\n"
        "csvName = out\n"
        "bdpQsz = 1.0\n"
        "bottleneckDelay = 10ms\n"
        "bottleneckSpeed = 10Mbps\n"
        "outputFactor = MB\n"
        "qSizeFileName = qsize.txt\n"
        "cmd = run\n"
    )
    runner = BfsRunner(str(config_file), "myScenario")
    # 2 flows
    fake_stats = np.zeros((2, 1, 12))
    fake_pcaps = ["test-tcp0-0.pcap", "test-udp0-0.pcap"]

    with (
        patch("pcapprocessor.runner.SimulationRunner") as mock_sim,
        patch("pcapprocessor.runner.MetricsWriter") as mock_writer,
    ):
        mock_sim.return_value.run.return_value = (fake_stats, fake_pcaps)
        runner.run()

    # one write per flow
    assert mock_writer.return_value.write.call_count == 2
