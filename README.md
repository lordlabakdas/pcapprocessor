# pcapprocessor ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/lordlabakdas/pcapprocessor/python-app.yml) ![GitHub](https://img.shields.io/github/license/lordlabakdas/pcapprocessor?color=green) [![PyPI version](https://badge.fury.io/py/pcapprocessor.svg)](https://badge.fury.io/py/pcapprocessor) [![CodeSee](https://github.com/lordlabakdas/pcapprocessor/actions/workflows/codesee-arch-diagram.yml/badge.svg)](https://github.com/lordlabakdas/pcapprocessor/actions/workflows/codesee-arch-diagram.yml)

A toolkit for running ns-3 network simulations, extracting TCP metrics from pcap traces, and generating publication-quality figures. It automates the full pipeline: simulation → pcap analysis → metric aggregation → CSV output → plots.

---

## Table of Contents

- [Installation](#installation)
- [Overview](#overview)
- [Pipeline](#pipeline)
- [Configuration File](#configuration-file)
- [Available Metrics](#available-metrics)
- [API Reference](#api-reference)
  - [BfsRunner](#bfsrunner)
  - [PcapProcessor](#pcapprocessor)
  - [TraceProcessor](#traceprocessor)
  - [MetricsWriter](#metricswriter)
  - [Reporter](#reporter)
  - [Supporting Classes](#supporting-classes)
- [CLI Usage](#cli-usage)
- [Development](#development)
- [Contributors](#contributors)

---

## Installation

```bash
pip install pcapprocessor
```

Requires Python 3.10+. Wireshark/tshark must be installed for pcap parsing (used by pyshark under the hood).

---

## Overview

`pcapprocessor` was built for ns-3 simulation studies. Given a config file describing the simulation parameters, it:

1. Runs multiple simulation replications via the ns-3 WAF build system.
2. Parses each pcap output with pyshark to extract per-flow TCP metrics.
3. Aggregates metrics across runs (mean, std dev, 95% confidence intervals).
4. Writes results to tab-separated CSV files — one per protocol/flow.
5. Generates matplotlib figures from those CSVs with confidence interval error bars.

---

## Pipeline

```
Config file (.ini)
      │
      ▼
  BfsRunner.run()
      │
      ├─► WafCommandBuilder  ──► ns-3 simulation (WAF)
      │                               │
      │                         pcap + ascii trace files
      │                               │
      ├─► SimulationRunner            │
      │       └─► TraceProcessor ─────┘
      │               (pyshark: TCP metrics per flow)
      │
      ├─► MetricStats + ConfidenceInterval
      │       (mean / std / CI across runs)
      │
      └─► MetricsWriter
              (writes results/tcp0.csv, results/udp0.csv, …)

results/*.csv
      │
      ▼
  Reporter.plot()
      (one PNG/SVG figure per metric, all protocols overlaid)
```

---

## Configuration File

`BfsRunner` reads a standard `.ini` file. Each section is a scenario name.

```ini
[bottleneckDelay]
# x-axis sweep values (comma-separated)
bottleneckDelay = 10,20,30,40,50

# fixed parameters
bottleneckSpeed = 10Mbps
bdpQsz          = 1.0
runs            = 5
transProt       = tcp,udp
pcapFile        = results/flow
csvName         = results/metrics
qSizeFileName   = queue*.tr
outputFactor    = Mb

# WAF command template — %(x)s, %(runNo)s, %(queue_size)s, %(qMonitoring)s are substituted
cmd = ./waf --run "scratch/sim --delay=%(x)s --qs=%(queue_size)s --run=%(runNo)s --qm=%(qMonitoring)s"
```

### Scenario keys

| Key | Description |
|---|---|
| `<scenario>` | Comma-separated x-axis sweep values (key name must match the section name) |
| `bottleneckSpeed` | Link speed (e.g. `10Mbps`) |
| `bottleneckDelay` | Link delay (e.g. `10ms`) |
| `bdpQsz` | BDP queue-size multiplier |
| `runs` | Number of simulation replications |
| `transProt` | Comma-separated protocol names (used to match pcap filenames) |
| `pcapFile` | Base pcap filename prefix |
| `csvName` | Output CSV filename prefix |
| `qSizeFileName` | Glob pattern for the ASCII queue-size trace file |
| `outputFactor` | Unit for throughput output (`Mb`, `Kb`, `Gb`, etc.) |
| `cmd` | WAF command template |

---

## Available Metrics

`MetricsWriter` writes these columns to every CSV (prefix `avg_`, `std_`, `confInt_` for each):

| Short name | Description |
|---|---|
| `throughput` | TCP goodput in the configured unit |
| `delay` | One-way delay (half of avg round-trip time) in ms |
| `goodput` | Bits transferred per second |
| `cum_goodput` | Cumulative goodput |
| `utilization` | Link utilization % |
| `tx_packets` | Total transmitted packets |
| `overhead` | Packet overhead bytes (TCP header × tx_packets) |
| `retxPackets` | Retransmitted packets |
| `queue_mean` | Mean queue occupancy |
| `queue_variance` | Queue occupancy variance |
| `queue_percentage` | Queue fill % relative to buffer size |
| `flow_cmp_time` | Total flow completion time in ms |

Use any short name with `Reporter` (e.g. `--metrics throughput delay utilization`).

---

## API Reference

### BfsRunner

Runs the full simulation-to-CSV pipeline for a given scenario.

```python
from pcapprocessor import BfsRunner

runner = BfsRunner(config_file="sim.ini", scenario="bottleneckDelay")
runner.run()
# Writes results/metrics_tcp0.csv, results/metrics_udp0.csv, …
```

**Constructor:**

| Parameter | Type | Description |
|---|---|---|
| `config_file` | `str` | Path to the `.ini` configuration file |
| `scenario` | `str` | Section name in the config file |

---

### PcapProcessor

Processes a single pcap file and optionally writes its metrics to CSV.

```python
from configparser import ConfigParser
from pcapprocessor import PcapProcessor

cfg = ConfigParser()
cfg.read("sim.ini")

proc = PcapProcessor(
    pcap_file_path="results/flow-tcp0-0.pcap",
    unit="Mb",
    config=cfg,
    scenario="bottleneckDelay",
    ascii_trace_file="queue0.tr",
    buf_size=25000,
)

# Returns a list of 12 raw metric values
metrics = proc.process()

# Or process and write directly to CSV
from pcapprocessor import XScaleArray
x_array = XScaleArray(["10", "20", "30"]).to_array()
proc.process_and_write(x_array, pcap_file="results/flow-tcp0-0.pcap")
```

**`process()` return value** — a list of 12 values in order:

```
[tx_packets, overhead_bytes, throughput, delay_ms, goodput,
 unique_bytes, retx_packets, utilization, queue_mean,
 queue_variance, queue_percentage, flow_completion_ms]
```

---

### TraceProcessor

Low-level pcap parser. Identifies the dominant TCP flow and extracts metrics.

```python
from configparser import ConfigParser
from pcapprocessor import TraceProcessor

cfg = ConfigParser()
cfg.read("sim.ini")

metrics = TraceProcessor(
    pcap_file="results/flow-tcp0-0.pcap",
    unit="Mb",
    config=cfg,
    scenario="bottleneckDelay",
    ascii_trace_file="queue0.tr",
    buf_size=25000,
).process()
```

---

### MetricsWriter

Writes aggregated metrics to a tab-separated CSV file.

```python
from pcapprocessor import MetricsWriter, XScaleArray
import numpy as np

x_array = XScaleArray(["10", "20", "30"]).to_array()
metrics = np.zeros((3, 36))  # shape: (len(xscale), num_metrics * 3)

MetricsWriter(
    metrics=metrics,
    x_array=x_array,
    scenario="bottleneckDelay",
    config=cfg,
    pcap_file="results/flow-tcp0-0.pcap",
).write()
# Writes: results/metrics_tcp0.csv
```

CSV format — tab-separated, first row is column headers:

```
x-scale	avg_tx_packets	std_tx_packets	confInt_tx_packets	avg_overhead	…
10.0    482.0           12.3            1.8                  15424.0        …
20.0    961.0           18.7            2.6                  30752.0        …
```

---

### Reporter

Reads metric CSVs and generates one figure per metric with all protocols overlaid.

```python
from pcapprocessor import Reporter

Reporter(
    csvs=["results/metrics_tcp0.csv", "results/metrics_udp0.csv"],
    metrics=["throughput", "delay", "utilization"],
    output_dir="plots",
    fmt="png",          # or "svg"
).plot()
# Writes: plots/throughput.png, plots/delay.png, plots/utilization.png
# Returns the list of written file paths
```

**Constructor:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `csvs` | `list[str]` | — | Paths to CSV files; one per protocol. The filename stem becomes the legend label (e.g. `metrics_tcp0.csv` → `"metrics_tcp0"`). |
| `metrics` | `list[str]` | — | Short metric names to plot (see [Available Metrics](#available-metrics)) |
| `output_dir` | `str` | `"plots"` | Output directory (created if it doesn't exist) |
| `fmt` | `str` | `"png"` | Output format: `"png"` or `"svg"` |

**Figure style:** seaborn `whitegrid`, one line per protocol, error bars show `confInt / 2` (half-width 95% CI), `capsize=4`.

---

### Supporting Classes

#### ConfidenceInterval

Calculates a 95% Student's t confidence interval for a dataset.

```python
from pcapprocessor import ConfidenceInterval
import numpy as np

ci = ConfidenceInterval(np.array([10.2, 10.5, 9.8, 10.1, 10.3])).calculate()
# Returns the full CI width (2 × t × SEM)
```

#### MetricStats

Computes mean, std dev, and CI across simulation runs for all metrics.

```python
from pcapprocessor import MetricStats
import numpy as np

# run_stats shape: (num_runs, num_metrics)
stats = MetricStats(run_stats=run_stats, num_metrics=12, runs=5).calculate()
# Returns shape (3, num_metrics): row 0 = mean, row 1 = std, row 2 = CI
```

#### XScaleArray

Parses x-axis sweep values into a numpy array.

```python
from pcapprocessor import XScaleArray

x = XScaleArray(["10", "20", "30", "40"]).to_array()
# np.array([10., 20., 30., 40.])
```

#### QueueSizeCalculator

Computes BDP-based queue size from config parameters.

```python
from pcapprocessor import QueueSizeCalculator

qs = QueueSizeCalculator(scenario="bottleneckDelay", x="20", config=cfg).calculate()
# Returns queue size as a string (used directly in WAF command)
```

#### WafCommandBuilder

Builds a WAF run command by substituting scenario parameters.

```python
from pcapprocessor import WafCommandBuilder

cmd, queue_size = WafCommandBuilder(
    run_no="1", x="20", scenario="bottleneckDelay", config=cfg
).build()
```

---

## CLI Usage

### Run a simulation sweep

```bash
python pcapprocessor.py <pcap_file> <unit> <config_file> <scenario> <ascii_trace_file> <buf_size>

# Example
python pcapprocessor.py results/flow-tcp0-0.pcap Mb sim.ini bottleneckDelay queue0.tr 25000
```

### Generate figures from existing CSVs

```bash
python -m pcapprocessor.report \
  --csvs results/metrics_tcp0.csv results/metrics_udp0.csv \
  --metrics throughput delay utilization \
  --output plots/ \
  --format png
```

| Flag | Required | Default | Description |
|---|---|---|---|
| `--csvs` | yes | — | One or more CSV file paths (one per protocol) |
| `--metrics` | yes | — | Metric short names to plot |
| `--output` | no | `plots` | Output directory |
| `--format` | no | `png` | `png` or `svg` |

Prints each written file path to stdout. Exits with code 1 and an error message on stderr if a metric is not found in the CSV or a file is missing.

---

## Development

```bash
git clone https://github.com/lordlabakdas/pcapprocessor.git
cd pcapprocessor
pip install -r requirements.txt
pytest --cov=pcapprocessor --cov-report=term-missing
```

Code style is enforced with `ruff`, `black`, and `isort` via `pre-commit`:

```bash
pre-commit install
```

CI runs on every push/PR to `main` and requires 90% test coverage.

---

## Contributors

- Siddharth Gangadhar
- Santosh Gondi
- Truc Anh Ngoc Nguyen
