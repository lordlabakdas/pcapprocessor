from configparser import ConfigParser
import pytest
from pcapprocessor.simulation import QueueSizeCalculator, WafCommandBuilder


def _make_config(section: str, options: dict) -> ConfigParser:
    config = ConfigParser()
    config[section] = options
    return config


def test_queue_size_bottleneck_delay():
    config = _make_config("bottleneckDelay", {
        "bdpQsz": "1.0",
        "bottleneckDelay": "10,20",   # key == scenario name → xscale
        "bottleneckSpeed": "10Mbps",
    })
    # speed=10*1e6, bdp=1.0, x=10, formula: int(1.0*1e7*2*0.001*(10.0/8)) = 25000
    result = QueueSizeCalculator("bottleneckDelay", "10", config).calculate()
    assert result == "25000"


def test_queue_size_bottleneck_speed():
    config = _make_config("bottleneckSpeed", {
        "bdpQsz": "1.0",
        "bottleneckSpeed": "10,20",   # xscale
        "bottleneckDelay": "10ms",
        "speedUnit": "Mbps",
    })
    # delay=10, x=10->10e6 Mbps, formula: int(1.0*10*2*0.001*(10e6/8)) = 25000
    result = QueueSizeCalculator("bottleneckSpeed", "10", config).calculate()
    assert result == "25000"


def test_waf_command_builder_appends_ms_for_bottleneck_delay():
    config = _make_config("bottleneckDelay", {
        "bdpQsz": "1.0",
        "bottleneckDelay": "10,20",
        "bottleneckSpeed": "10Mbps",
        "runs": "3",
        "cmd": "run --x=%(x)s --runNo=%(runNo)s --qs=%(queue_size)s --qm=%(qMonitoring)s",
    })
    cmd, q_size = WafCommandBuilder("1", "10", "bottleneckDelay", config).build()
    assert "10ms" in cmd
    assert isinstance(q_size, int)


def test_waf_command_builder_q_monitoring_is_0_when_runs_gt_1():
    config = _make_config("bottleneckDelay", {
        "bdpQsz": "1.0",
        "bottleneckDelay": "10",
        "bottleneckSpeed": "10Mbps",
        "runs": "3",
        "cmd": "run --qm=%(qMonitoring)s --x=%(x)s --runNo=%(runNo)s --qs=%(queue_size)s",
    })
    cmd, _ = WafCommandBuilder("1", "10", "bottleneckDelay", config).build()
    assert "qm=0" in cmd


def test_waf_command_builder_q_monitoring_is_1_when_single_run():
    config = _make_config("bottleneckDelay", {
        "bdpQsz": "1.0",
        "bottleneckDelay": "10",
        "bottleneckSpeed": "10Mbps",
        "runs": "1",
        "cmd": "run --qm=%(qMonitoring)s --x=%(x)s --runNo=%(runNo)s --qs=%(queue_size)s",
    })
    cmd, _ = WafCommandBuilder("1", "10", "bottleneckDelay", config).build()
    assert "qm=1" in cmd


def test_queue_size_else_branch():
    # scenario is neither "bottleneckDelay" nor "bottleneckSpeed" → else branch
    config = _make_config("changingDelay", {
        "bdpQsz": "1.0",
        "changingDelay": "5,10",       # xscale (key == scenario name)
        "bottleneckDelay": "10ms",
        "bottleneckSpeed": "10Mbps",
    })
    # delay = int("10ms"[:-2]) = 10, speed_numeric = 10*1_000_000 = 10_000_000
    # queue_size = int(1.0 * 10_000_000 * 2 * 0.001 * 10 / 8) = 25000
    result = QueueSizeCalculator("changingDelay", "5", config).calculate()
    assert result == "25000"


def test_waf_command_builder_appends_mbps_for_bottleneck_speed():
    config = _make_config("bottleneckSpeed", {
        "bdpQsz": "1.0",
        "bottleneckSpeed": "10,20",    # xscale
        "bottleneckDelay": "10ms",
        "speedUnit": "Mbps",
        "runs": "1",
        "cmd": "run --x=%(x)s --runNo=%(runNo)s --qs=%(queue_size)s --qm=%(qMonitoring)s",
    })
    cmd, _ = WafCommandBuilder("1", "10", "bottleneckSpeed", config).build()
    assert "10Mbps" in cmd
