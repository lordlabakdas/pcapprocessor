# Class-Level Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all procedural functions with simple stateful classes and reorganize the module layout to reflect responsibility.

**Architecture:** Inputs move into `__init__`, the work goes into a clearly named method (`process()`, `run()`, `write()`, `calculate()`). The `legacy/` and old `pbs/` files are deleted; their contents land in `stats.py`, `simulation.py`, `trace.py`, `metrics.py`, `runner.py`, and `pbs/job_writer.py` / `pbs/dce_runner.py`. The root `PcapProcessor` is wired to chain `TraceProcessor → MetricsWriter`.

**Tech Stack:** Python 3, numpy, scipy, configparser (stdlib), csv (stdlib), pytest

---

## File Map

| New file | Classes | Replaces |
|---|---|---|
| `pcapprocessor/exe_comm.py` | `exe_comm()` utility | deleted `packet_collator/` subprocess helper |
| `pcapprocessor/stats.py` | `ConfidenceInterval`, `XScaleArray`, `MetricStats` | `legacy/confInt.py`, `legacy/xscaleArray.py`, deleted `metrics_calculator/metricStats.py` |
| `pcapprocessor/simulation.py` | `QueueSizeCalculator`, `WafCommandBuilder` | `legacy/calcQsz.py`, `legacy/wafCmd.py` |
| `pcapprocessor/trace.py` | `TraceProcessor` | `legacy/pp_trace.py` |
| `pcapprocessor/metrics.py` | `MetricsWriter` | `legacy/csvWriter.py` |
| `pcapprocessor/runner.py` | `SimulationRunner`, `BfsRunner` | `legacy/cmdRunner.py`, `pbs/bfsRunner.py` |
| `pcapprocessor/pbs/job_writer.py` | `PbsJobWriter` | `pbs/pbsWriter.py`, `pbs/cfgPbsWriter.py` |
| `pcapprocessor/pbs/dce_runner.py` | `DceRunner` | `pbs/dceRunner.py`, `pbs/cfgWrapper.py` |
| `pcapprocessor.py` | `PcapProcessor` (updated) | itself |
| `pcapprocessor/__init__.py` | public exports | itself |
| `tests/test_stats.py` | — | new |
| `tests/test_simulation.py` | — | new |
| `tests/test_pbs.py` | — | new |

---

## Task 0: `pcapprocessor/exe_comm.py` — subprocess utility

**Files:**
- Create: `pcapprocessor/exe_comm.py`

`TraceProcessor` and `SimulationRunner` both need `exe_comm.exe_comm()` — a thin subprocess wrapper that was in the deleted `packet_collator/` package.

- [ ] **Step 1: Create `pcapprocessor/exe_comm.py`**

```python
import subprocess


def exe_comm(cmd: list, capture: bool = True) -> str:
    """Run a shell command. Returns stdout as a string when capture=True."""
    if capture:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode("utf-8")
    subprocess.run(cmd, check=True)
    return ""
```

- [ ] **Step 2: Commit**

```bash
git add pcapprocessor/exe_comm.py
git commit -m "feat: add exe_comm subprocess utility"
```

---

## Task 1: `pcapprocessor/stats.py` — `ConfidenceInterval`, `XScaleArray`, `MetricStats`

**Files:**
- Create: `pcapprocessor/stats.py`
- Create: `tests/test_stats.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_stats.py`:

```python
import math
import numpy as np
import pytest
from pcapprocessor.stats import ConfidenceInterval, XScaleArray, MetricStats


def test_confidence_interval_zero_variance():
    data = np.ones(10)
    assert ConfidenceInterval(data).calculate() == pytest.approx(0.0)


def test_confidence_interval_small_sample_positive():
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = ConfidenceInterval(data).calculate()
    assert isinstance(result, float)
    assert result > 0.0


def test_confidence_interval_large_sample_uses_z():
    data = np.arange(1, 52, dtype=float)  # 51 elements → uses 1.95
    result = ConfidenceInterval(data).calculate()
    assert result > 0.0


def test_xscale_array_converts_strings_to_floats():
    result = XScaleArray(["1", "2", "3"]).to_array()
    np.testing.assert_array_almost_equal(result, np.array([1.0, 2.0, 3.0]))


def test_xscale_array_is_1d():
    result = XScaleArray(["10", "20"]).to_array()
    assert result.ndim == 1


def test_metric_stats_shape():
    run_stats = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    result = MetricStats(run_stats, num_metrics=2, runs=3).calculate()
    assert result.shape == (3, 2)


def test_metric_stats_mean_row():
    run_stats = np.array([[2.0, 4.0], [4.0, 6.0]])
    result = MetricStats(run_stats, num_metrics=2, runs=2).calculate()
    assert result[0, 0] == pytest.approx(3.0)
    assert result[0, 1] == pytest.approx(5.0)
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_stats.py -v
```

Expected: `ModuleNotFoundError: No module named 'pcapprocessor.stats'`

- [ ] **Step 3: Create `pcapprocessor/stats.py`**

```python
import math

import numpy as np
from scipy import stats as scipy_stats


class ConfidenceInterval:
    _T_TABLE = {
        2: 4.3027, 3: 3.1824, 4: 2.7765, 5: 2.5706, 6: 2.4469,
        7: 2.3646, 8: 2.3060, 9: 2.2622, 10: 2.2281, 11: 2.1010,
        12: 2.1788, 13: 2.1604, 14: 2.1448, 15: 2.1315, 16: 2.1199,
        17: 2.1098, 18: 2.1009, 19: 2.0930, 20: 2.0860, 21: 2.0796,
        22: 2.0739, 23: 2.0687, 24: 2.0639, 25: 2.0595, 26: 2.0555,
        27: 2.0518, 28: 2.0484, 29: 2.0452, 30: 2.0423,
    }

    def __init__(self, data: np.ndarray):
        self.data = data

    def calculate(self) -> float:
        flat = self.data.flatten()
        _, _, _, var, _, _ = scipy_stats.describe(flat)
        std = math.sqrt(var)
        n = len(flat)
        mul = self._T_TABLE.get(n, 1.95)
        return 2 * mul * std / math.sqrt(n)


class XScaleArray:
    def __init__(self, xscale: list):
        self.xscale = xscale

    def to_array(self) -> np.ndarray:
        arr = np.array(list(map(float, self.xscale)))
        return arr.reshape(len(arr), 1).flatten()


class MetricStats:
    def __init__(self, run_stats: np.ndarray, num_metrics: int, runs: int):
        self.run_stats = run_stats
        self.num_metrics = num_metrics
        self.runs = runs

    def calculate(self) -> np.ndarray:
        result = np.zeros((3, self.num_metrics))
        for i in range(self.num_metrics):
            col = self.run_stats[:, i]
            result[0, i] = np.mean(col)
            result[1, i] = np.std(col)
            result[2, i] = ConfidenceInterval(col).calculate()
        return result
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_stats.py -v
```

Expected: all 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pcapprocessor/stats.py tests/test_stats.py
git commit -m "feat: add ConfidenceInterval, XScaleArray, MetricStats classes"
```

---

## Task 2: `pcapprocessor/simulation.py` — `QueueSizeCalculator`, `WafCommandBuilder`

**Files:**
- Create: `pcapprocessor/simulation.py`
- Create: `tests/test_simulation.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_simulation.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_simulation.py -v
```

Expected: `ModuleNotFoundError: No module named 'pcapprocessor.simulation'`

- [ ] **Step 3: Create `pcapprocessor/simulation.py`**

```python
from configparser import ConfigParser


class QueueSizeCalculator:
    def __init__(self, scenario: str, x: str, config: ConfigParser):
        self.scenario = scenario
        self.x = x
        self.config = config

    def calculate(self) -> str:
        bdp_qsz = self.config.getfloat(self.scenario, "bdpQsz")
        xscale = self.config.get(self.scenario, self.scenario).split(",")

        if self.scenario == "bottleneckDelay":
            speed = self.config.get(self.scenario, "bottleneckSpeed")
            speed_numeric = self._parse_speed(speed)
            queue_size = int(
                bdp_qsz * speed_numeric * 2 * 0.001
                * (float(xscale[xscale.index(self.x)]) / 8)
            )

        elif self.scenario == "bottleneckSpeed":
            delay = int(self.config.get(self.scenario, "bottleneckDelay")[:-2])
            speed_unit = self.config.get(self.scenario, "speedUnit")
            x = self._apply_unit(int(self.x), speed_unit)
            queue_size = int(bdp_qsz * delay * 2 * 0.001 * (float(x) / 8))

        else:
            delay = int(self.config.get(self.scenario, "bottleneckDelay")[:-2])
            speed = self.config.get(self.scenario, "bottleneckSpeed")
            speed_numeric = self._parse_speed(speed)
            queue_size = int(
                bdp_qsz * speed_numeric * 2 * 0.001 * delay / 8
            )

        return str(queue_size)

    @staticmethod
    def _parse_speed(speed_str: str) -> int:
        unit = speed_str[-4:]
        numeric = int(speed_str[:-4])
        multipliers = {"K": 1_000, "M": 1_000_000, "G": 1_000_000_000}
        return multipliers.get(unit[0], 1) * numeric

    @staticmethod
    def _apply_unit(value: int, unit: str) -> int:
        multipliers = {"K": 1_000, "M": 1_000_000, "G": 1_000_000_000}
        return multipliers.get(unit[0], 1) * value


class WafCommandBuilder:
    def __init__(self, run_no: str, x: str, scenario: str, config: ConfigParser):
        self.run_no = run_no
        self.x = x
        self.scenario = scenario
        self.config = config

    def build(self) -> tuple:
        queue_size = QueueSizeCalculator(self.scenario, self.x, self.config).calculate()
        runs = self.config.getint(self.scenario, "runs")
        q_monitoring = 1 if runs == 1 else 0

        x = self.x
        if self.scenario in ("bottleneckDelay", "changingDelay"):
            x = x + "ms"
        elif self.scenario == "bottleneckSpeed":
            x = x + "Mbps"

        waf_cmd = self.config.get(
            section=self.scenario,
            option="cmd",
            vars=dict(
                queue_size=queue_size,
                x=x,
                runNo=self.run_no,
                qMonitoring=q_monitoring,
            ),
        )
        return waf_cmd, int(queue_size)
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_simulation.py -v
```

Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pcapprocessor/simulation.py tests/test_simulation.py
git commit -m "feat: add QueueSizeCalculator and WafCommandBuilder classes"
```

---

## Task 3: `pcapprocessor/trace.py` — `TraceProcessor`

**Files:**
- Create: `pcapprocessor/trace.py`

No unit test added here — `TraceProcessor` shells out to `tcptrace` and reads real pcap files. Integration testing requires real capture fixtures outside this refactor's scope.

- [ ] **Step 1: Create `pcapprocessor/trace.py`**

```python
import re
import sys
import shlex
import datetime

import numpy as np

from pcapprocessor import exe_comm


class TraceProcessor:
    PACKET_OVERHEAD = 32  # TCP header with timestamp option

    def __init__(
        self,
        pcap_file: str,
        unit: str,
        config,
        scenario: str,
        ascii_trace_file: str,
        buf_size: int,
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

        print("Processing ascii trace output")
        pkt_size = int(self.config.get(self.scenario, "pktSize"))
        with open(self.ascii_trace_file, "r") as fl:
            lines = list(fl)
        axis_y1 = [int(line.strip().split(",")[1]) for line in lines]
        a = np.array(axis_y1)
        queue_mean = a.mean()
        queue_variance = a.var()

        trace_cmd = "tcptrace -l -r -n -W --csv " + self.pcap_file
        print("Executing tcptrace command. it may take few seconds")
        result = exe_comm.exe_comm(shlex.split(trace_cmd))
        print("Processing trace output")

        pcap_lines = result.split("\n")
        regex_con = re.compile(r"#([0-9]*) TCP connection traced:")
        matches = [
            pcap_lines.index(ln)
            for ln in pcap_lines
            if re.match(regex_con, ln)
        ]

        if not matches:
            print("No TCP connections found")
            sys.exit()

        connections = [
            pcap_lines[matches[j]: matches[j + 1]]
            for j in range(len(matches) - 1)
        ]
        connections.append(pcap_lines[matches[-1]:])

        result_str = "\n"
        for i, item in enumerate(connections):
            flow_cmp_time = 0
            try:
                time_stamp = pcap_lines[matches[i] - 2].split()[-1]
                t = datetime.datetime.strptime(time_stamp, "%H:%M:%S.%f")
                flow_cmp_time = (
                    t.time().hour * 3600 + t.time().minute * 60 + t.time().second
                ) * 1000 + t.time().microsecond / 1000
            except Exception:
                print("Couldn't parse the flow completion time")

            labels = item[1].split(",")
            values = item[3].split(",")

            conn_suffix = "a2b"
            if int(values[labels.index("unique_bytes_sent_a2b")]) <= 0:
                conn_suffix = "b2a"

            tx_packets = int(values[labels.index("total_packets_" + conn_suffix)])
            rexmt_packets = int(values[labels.index("rexmt_data_pkts_" + conn_suffix)])
            overhead = self.PACKET_OVERHEAD * tx_packets
            goodput = 8 * int(values[labels.index("throughput_" + conn_suffix)])
            unique_bytes = int(values[labels.index("unique_bytes_sent_" + conn_suffix)])
            tx_time = (1.0 * unique_bytes) / goodput
            throughput = (
                int(values[labels.index("actual_data_bytes_" + conn_suffix)]) / tx_time
            )
            rtt = float(values[labels.index("RTT_avg_" + conn_suffix)]) / 2
            utilization = throughput * 100.0 / bn_speed

            result_str = [
                tx_packets,
                overhead,
                round(throughput / fact_by, 3),
                round(rtt, 3),
                round(goodput / fact_by, 3),
                unique_bytes,
                rexmt_packets,
                round(utilization, 3),
                round(queue_mean, 3),
                round(queue_variance, 3),
                round(queue_mean * 100.0 / (self.buf_size / pkt_size), 3),
                round(flow_cmp_time, 3),
            ]

        return result_str

    def _unit_factor(self) -> float:
        first, second = list(self.unit)
        scale = {"K": 1_000, "M": 1_000_000, "G": 1_000_000_000}
        byte = {"B": 8, "b": 1}
        return scale.get(first, 1) * byte.get(second, 1)

    def _bottleneck_speed(self, fact_by: float) -> float:
        sp = self.config.get(self.scenario, "bottleneckSpeed")
        bn_speed = int(re.search(r"(\d+)", sp).group())
        return bn_speed * fact_by
```

- [ ] **Step 2: Commit**

```bash
git add pcapprocessor/trace.py
git commit -m "feat: add TraceProcessor class"
```

---

## Task 4: `pcapprocessor/metrics.py` — `MetricsWriter`

**Files:**
- Create: `pcapprocessor/metrics.py`
- Create: `tests/test_metrics.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_metrics.py`:

```python
import csv
import os
import tempfile
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
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/test_metrics.py -v
```

Expected: `ModuleNotFoundError: No module named 'pcapprocessor.metrics'`

- [ ] **Step 3: Create `pcapprocessor/metrics.py`**

```python
import csv

import numpy as np


METRIC_LABELS = [
    "x-scale",
    "avg_tx_packets", "std_tx_packets", "confInt_tx_packets",
    "avg_overhead", "std_overhead", "confInt_overhead",
    "avg_throughput", "std_throughput", "confInt_throughput",
    "avg_delay", "std_delay", "confInt_delay",
    "avg_goodput", "std_goodput", "confInt_goodput",
    "avg_cum_goodput", "std_cum_goodput", "confInt_cum_goodput",
    "avg_retxPackets", "std_retxPackets", "confInt_retxPackets",
    "avg_utilization", "std_utilization", "confInt_utilization",
    "avg_queue_mean", "std_queue_mean", "confInt_queue_mean",
    "avg_queue_variance", "std_queue_variance", "confInt_queue_variance",
    "avg_queue_percentage", "std_queue_percentage", "confInt_queue_percentage",
    "avg_flow_cmp_time", "std_flow_cmp_time", "confInt_flow_cmp_time",
]


class MetricsWriter:
    def __init__(self, metrics, x_array, scenario: str, config, pcap_file: str):
        self.metrics = metrics
        self.x_array = x_array
        self.scenario = scenario
        self.config = config
        self.pcap_file = pcap_file

    def write(self) -> None:
        csv_name = self._resolve_csv_name()
        labelled = np.vstack(([METRIC_LABELS], np.column_stack((self.x_array, self.metrics))))
        with open(csv_name, "w", newline="") as fl:
            writer = csv.writer(fl, delimiter="\t")
            writer.writerows(labelled)

    def _resolve_csv_name(self) -> str:
        trans_prots = self.config.get(self.scenario, "transProt").split(",")
        pcap_base = self.config.get(self.scenario, "pcapFile")
        prot = ""
        for i, item in enumerate(trans_prots):
            if (pcap_base + "-" + item + str(i) + "-0.pcap") == self.pcap_file:
                prot = item + str(i)
        return self.config.get(self.scenario, "csvName") + "_" + prot + ".csv"
```

- [ ] **Step 4: Run test to confirm it passes**

```
pytest tests/test_metrics.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pcapprocessor/metrics.py tests/test_metrics.py
git commit -m "feat: add MetricsWriter class"
```

---

## Task 5: `pcapprocessor/runner.py` — `SimulationRunner`, `BfsRunner`

**Files:**
- Create: `pcapprocessor/runner.py`

No isolated unit tests — both classes shell out to external programs (`waf`, `tcptrace`) and depend on real filesystem state. They are tested end-to-end when the full pipeline runs.

- [ ] **Step 1: Create `pcapprocessor/runner.py`**

```python
import shlex
from configparser import ConfigParser
from glob import glob

import numpy as np

from pcapprocessor.metrics import MetricsWriter
from pcapprocessor.simulation import WafCommandBuilder
from pcapprocessor.stats import MetricStats, XScaleArray
from pcapprocessor.trace import TraceProcessor
from pcapprocessor import exe_comm


class SimulationRunner:
    def __init__(self, x: str, num_metrics: int, scenario: str, config: ConfigParser):
        self.x = x
        self.num_metrics = num_metrics
        self.scenario = scenario
        self.config = config

    def run(self) -> tuple:
        runs = self.config.getint(self.scenario, "runs")
        pcap_name = self.config.get(self.scenario, "pcapFile")
        output_factor = self.config.get(self.scenario, "outputFactor")
        num_flows = len(self.config.get(self.scenario, "transProt").split(","))
        ascii_file_name = self.config.get(self.scenario, "qSizeFileName")
        run_stats = np.zeros((num_flows, runs, self.num_metrics))

        for run in range(runs):
            run_no = str(run + 1)
            waf_cmd, q_size = WafCommandBuilder(run_no, self.x, self.scenario, self.config).build()
            print(waf_cmd)
            exe_comm.exe_comm(shlex.split(waf_cmd))

            pcap_files = glob(pcap_name + "*.pcap")
            ascii_file = glob(ascii_file_name)

            for p, item in enumerate(pcap_files):
                run_stats[p, run, :] = np.array(
                    TraceProcessor(
                        item, output_factor, self.config,
                        self.scenario, ascii_file[0], q_size,
                    ).process()
                )
                exe_comm.exe_comm(shlex.split("rm " + item))

        return run_stats, pcap_files


class BfsRunner:
    NUM_METRICS = 12

    def __init__(self, config_file: str, scenario: str):
        self.config_file = config_file
        self.scenario = scenario

    def run(self) -> None:
        config = ConfigParser()
        config.read(self.config_file)

        xscale = config.get(self.scenario, self.scenario).split(",")
        num_flows = len(config.get(self.scenario, "transProt").split(","))
        runs = config.getint(self.scenario, "runs")

        x_array = XScaleArray(xscale).to_array()
        stats = np.zeros((num_flows, 3, self.NUM_METRICS))
        metrics = np.zeros((num_flows, len(x_array), self.NUM_METRICS * 3))

        for x in xscale:
            run_stats, pcap_files = SimulationRunner(
                x, self.NUM_METRICS, self.scenario, config
            ).run()
            for p in range(len(pcap_files)):
                stats[p, :, :] = MetricStats(
                    run_stats[p, :, :], self.NUM_METRICS, runs
                ).calculate()
                metrics[p, xscale.index(x)] = np.array(
                    stats[p, :, :].reshape(1, self.NUM_METRICS * 3, order="F").copy()
                )

        for pcap_file in pcap_files:
            MetricsWriter(
                metrics[pcap_files.index(pcap_file), :],
                x_array, self.scenario, config, pcap_file,
            ).write()
```

- [ ] **Step 2: Commit**

```bash
git add pcapprocessor/runner.py
git commit -m "feat: add SimulationRunner and BfsRunner classes"
```

---

## Task 6: `pcapprocessor/pbs/job_writer.py` — `PbsJobWriter`

**Files:**
- Create: `pcapprocessor/pbs/job_writer.py`
- Create: `tests/test_pbs.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_pbs.py`:

```python
import os
import pytest
from pcapprocessor.pbs.job_writer import PbsJobWriter


def test_pbs_job_writer_creates_jobs_dir(tmp_path):
    jobs_dir = str(tmp_path / "jobs")
    writer = PbsJobWriter("test.cfg", jobs_dir=jobs_dir)
    writer.write()
    assert os.path.isdir(jobs_dir)


def test_pbs_job_writer_creates_pbs_files(tmp_path):
    jobs_dir = str(tmp_path / "jobs")
    writer = PbsJobWriter("test.cfg", jobs_dir=jobs_dir)
    writer.write()
    pbs_files = [f for f in os.listdir(jobs_dir) if f.endswith(".pbs")]
    assert len(pbs_files) > 0


def test_pbs_job_writer_creates_driver_script(tmp_path):
    jobs_dir = str(tmp_path / "jobs")
    writer = PbsJobWriter("test.cfg", jobs_dir=jobs_dir)
    writer.write()
    assert os.path.exists(os.path.join(jobs_dir, "driver.sh"))


def test_pbs_job_writer_write_single_creates_pbs(tmp_path):
    jobs_dir = str(tmp_path / "jobs")
    writer = PbsJobWriter("error_test.cfg", jobs_dir=jobs_dir)
    writer.write_single()
    pbs_files = [f for f in os.listdir(jobs_dir) if f.endswith(".pbs")]
    assert len(pbs_files) == 1
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/test_pbs.py -v
```

Expected: `ModuleNotFoundError: No module named 'pcapprocessor.pbs.job_writer'`

- [ ] **Step 3: Create `pcapprocessor/pbs/job_writer.py`**

```python
import os


class PbsJobWriter:
    _NODE_SPECS_SIMPLE = "#PBS -l nodes=1:ppn=2,mem=1000M"
    _NODE_SPECS_CFG = "#PBS -l nodes=1:ppn=2,mem=2000M,walltime=120:0:0"

    def __init__(
        self,
        config_file: str,
        jobs_dir: str,
        email: str = "",
        work_dir: str = "",
    ):
        self.config_file = config_file
        self.jobs_dir = jobs_dir
        self.email = email
        self.work_dir = work_dir
        self._cfg_name = config_file[:-4]

    def write(self) -> None:
        """Generate PBS job files for TCP variants × scenarios (was pbsWriter)."""
        tcp_variants = ["bic"]
        scenarios = ["error"]
        os.makedirs(self.jobs_dir, exist_ok=True)
        driver_path = os.path.join(self.jobs_dir, "driver.sh")

        with open(driver_path, "w") as driver_file:
            for tcp in tcp_variants:
                for scen in scenarios:
                    pbs_name = self._write_job(tcp, scen)
                    driver_file.write("qsub " + pbs_name + "\n")

    def write_single(self) -> None:
        """Generate a single PBS job for this config file (was cfgPbsWriter)."""
        scenario = self.config_file.split("_", 1)[0]
        cfg_id = self._cfg_name
        os.makedirs(self.jobs_dir, exist_ok=True)

        pbs_filename = os.path.join(self.jobs_dir, cfg_id + ".pbs")
        run_cmd = (
            "python " + self.work_dir + "dceRunner.py "
            + self.config_file + " " + scenario
        )
        run_dir = "/tmp/tmp_" + cfg_id

        with open(pbs_filename, "w") as pbs_file:
            pbs_file.write(self._NODE_SPECS_CFG + "\n")
            pbs_file.write("#PBS -j oe\n")
            pbs_file.write("#PBS -S /bin/sh\n")
            pbs_file.write("#PBS -M " + self.email + "\n")
            pbs_file.write("#PBS -m a\n")
            pbs_file.write("#PBS -N " + cfg_id + "\n\n")
            pbs_file.write("cd $PBS_O_WORKDIR\n")
            pbs_file.write("cd " + self.work_dir + "\n")
            pbs_file.write("mkdir " + run_dir + "\n")
            pbs_file.write("cp " + self.config_file + " " + run_dir + "\n")
            pbs_file.write("cd " + run_dir + "\n")
            pbs_file.write(run_cmd + "\n")
            pbs_file.write("mv *.csv *.mon " + self.work_dir + "\n")
            pbs_file.write("cd " + run_dir + "\n")
            pbs_file.write("rm -rf " + run_dir + "\n")

    def _write_job(self, tcp: str, scen: str) -> str:
        unique_id = self._cfg_name + "_" + tcp + "_" + scen
        run_dir = "tmp_" + unique_id
        run_cmd = (
            "python ../dceRunner.py " + self.config_file
            + " " + scen + " " + tcp
        )
        pbs_fi_name = unique_id + ".pbs"
        pbs_path = os.path.join(self.jobs_dir, pbs_fi_name)

        with open(pbs_path, "w") as pbs_file:
            pbs_file.write(self._NODE_SPECS_SIMPLE + "\n")
            pbs_file.write("#PBS -j oe\n")
            pbs_file.write("#PBS -S /bin/sh\n")
            pbs_file.write("#PBS -M " + self.email + "\n")
            pbs_file.write("#PBS -m abe\n")
            pbs_file.write("#PBS -N " + unique_id + "\n\n")
            pbs_file.write("cd $PBS_O_WORKDIR\n")
            pbs_file.write("cd " + self.work_dir + "\n")
            pbs_file.write("mkdir " + run_dir + "\n")
            pbs_file.write("cp " + self.config_file + " " + run_dir + "\n")
            pbs_file.write("cd " + run_dir + "\n")
            pbs_file.write(run_cmd + "\n")
            pbs_file.write("mv *.csv ../\n")
            pbs_file.write("cd ..\n")
            pbs_file.write("rm -rf " + run_dir + "\n")

        return pbs_fi_name
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_pbs.py -v
```

Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pcapprocessor/pbs/job_writer.py tests/test_pbs.py
git commit -m "feat: add PbsJobWriter class"
```

---

## Task 7: `pcapprocessor/pbs/dce_runner.py` — `DceRunner`

**Files:**
- Create: `pcapprocessor/pbs/dce_runner.py`

- [ ] **Step 1: Create `pcapprocessor/pbs/dce_runner.py`**

```python
from pcapprocessor.pbs.job_writer import PbsJobWriter
from pcapprocessor.runner import BfsRunner


class DceRunner:
    def __init__(self, config_file: str, scenario: str = None, jobs_dir: str = "initial-test"):
        self.config_file = config_file
        self.scenario = scenario
        self.jobs_dir = jobs_dir

    def run(self) -> None:
        if self.scenario:
            BfsRunner(self.config_file, self.scenario).run()
        else:
            PbsJobWriter(self.config_file, jobs_dir=self.jobs_dir).write()
```

- [ ] **Step 2: Commit**

```bash
git add pcapprocessor/pbs/dce_runner.py
git commit -m "feat: add DceRunner class"
```

---

## Task 8: Update `pcapprocessor.py` — `PcapProcessor`

**Files:**
- Modify: `pcapprocessor.py`

- [ ] **Step 1: Replace the contents of `pcapprocessor.py`**

```python
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

    if len(sys.argv) < 6:
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
```

- [ ] **Step 2: Commit**

```bash
git add pcapprocessor.py
git commit -m "feat: update PcapProcessor to chain TraceProcessor and MetricsWriter"
```

---

## Task 9: Update `pcapprocessor/__init__.py` and delete old files

**Files:**
- Modify: `pcapprocessor/__init__.py`
- Delete: `pcapprocessor/legacy/` (entire directory)
- Delete: `pcapprocessor/pbs/bfsRunner.py`
- Delete: `pcapprocessor/pbs/pbsWriter.py`
- Delete: `pcapprocessor/pbs/cfgPbsWriter.py`
- Delete: `pcapprocessor/pbs/dceRunner.py`
- Delete: `pcapprocessor/pbs/cfgWrapper.py`

- [ ] **Step 1: Update `pcapprocessor/__init__.py`**

```python
from pcapprocessor.stats import ConfidenceInterval, MetricStats, XScaleArray
from pcapprocessor.simulation import QueueSizeCalculator, WafCommandBuilder
from pcapprocessor.trace import TraceProcessor
from pcapprocessor.metrics import MetricsWriter
from pcapprocessor.runner import BfsRunner, SimulationRunner

__all__ = [
    "ConfidenceInterval",
    "MetricStats",
    "XScaleArray",
    "QueueSizeCalculator",
    "WafCommandBuilder",
    "TraceProcessor",
    "MetricsWriter",
    "BfsRunner",
    "SimulationRunner",
]
```

- [ ] **Step 2: Delete old files**

```bash
git rm -r pcapprocessor/legacy/
git rm pcapprocessor/pbs/bfsRunner.py \
       pcapprocessor/pbs/pbsWriter.py \
       pcapprocessor/pbs/cfgPbsWriter.py \
       pcapprocessor/pbs/dceRunner.py \
       pcapprocessor/pbs/cfgWrapper.py
```

- [ ] **Step 3: Run the full test suite to confirm nothing is broken**

```
pytest tests/ -v
```

Expected: all previously passing tests still PASS (placeholder + stats + simulation + metrics + pbs)

- [ ] **Step 4: Commit**

```bash
git add pcapprocessor/__init__.py
git commit -m "refactor: remove legacy/ and old pbs/ files, export new classes from __init__"
```

---

## Completion Check

Run the full suite one final time:

```
pytest tests/ -v --tb=short
```

Expected output summary: no failures. All new class modules importable. Old `legacy/` path no longer exists.
