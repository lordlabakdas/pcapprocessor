# Class-Level Refactor Design

**Date:** 2026-06-05  
**Scope:** Full codebase — legacy pipeline, PBS pipeline, root entry point

---

## Goal

Replace all procedural functions with simple stateful classes (Option A: inputs in `__init__`, work in a named method). Reorganize the file layout to reflect responsibility rather than the old `legacy/` / `pbs/` split.

---

## New File Layout

```
pcapprocessor/
├── pcapprocessor.py              ← PcapProcessor (root entry point)
├── pcapprocessor/
│   ├── __init__.py
│   ├── stats.py                  ← ConfidenceInterval, XScaleArray
│   ├── simulation.py             ← QueueSizeCalculator, WafCommandBuilder
│   ├── trace.py                  ← TraceProcessor
│   ├── metrics.py                ← MetricsWriter
│   ├── runner.py                 ← SimulationRunner, BfsRunner
│   └── pbs/
│       ├── __init__.py
│       ├── job_writer.py         ← PbsJobWriter
│       └── dce_runner.py         ← DceRunner
└── tests/
    └── test_placeholder.py
```

The `legacy/` and `pbs/` directories are removed. Their contents are redistributed into the new module files above.

---

## Class Designs

### `pcapprocessor/stats.py`

```python
class ConfidenceInterval:
    def __init__(self, data: np.ndarray): ...
    def calculate(self) -> float: ...
    # was: ConfInt(data) in legacy/confInt.py

class XScaleArray:
    def __init__(self, xscale: list): ...
    def to_array(self) -> np.ndarray: ...
    # was: xscaleArray(xscale) in legacy/xscaleArray.py

class MetricStats:
    def __init__(self, run_stats: np.ndarray, num_metrics: int, runs: int): ...
    def calculate(self) -> np.ndarray: ...
    # was: metricStats() in deleted metrics_calculator/metricStats.py
    # called by BfsRunner — must be restored here
```

### `pcapprocessor/simulation.py`

```python
class QueueSizeCalculator:
    def __init__(self, scenario: str, x: str, config): ...
    def calculate(self) -> str: ...
    # was: calcQsz(scenario, x, config) in legacy/calcQsz.py

class WafCommandBuilder:
    def __init__(self, run_no: str, x: str, scenario: str, config): ...
    def build(self) -> tuple[str, int]: ...
    # was: wafCmd(runNo, x, scenario, config) in legacy/wafCmd.py
    # internally delegates to QueueSizeCalculator
```

### `pcapprocessor/trace.py`

```python
class TraceProcessor:
    def __init__(self, pcap_file: str, unit: str, config, scenario: str,
                 ascii_trace_file: str, buf_size: int): ...
    def process(self) -> list: ...
    # was: pp_trace(...) in legacy/pp_trace.py
```

### `pcapprocessor/metrics.py`

```python
class MetricsWriter:
    def __init__(self, metrics, x_array, scenario: str, config, pcap_file: str): ...
    def write(self) -> None: ...
    # was: csvWriter(...) in legacy/csvWriter.py
```

### `pcapprocessor/runner.py`

```python
class SimulationRunner:
    def __init__(self, x: str, num_metrics: int, scenario: str, config): ...
    def run(self) -> tuple[np.ndarray, list]: ...
    # was: cmdRunner(x, numMetrics, scenario, config) in legacy/cmdRunner.py
    # internally uses WafCommandBuilder and TraceProcessor

class BfsRunner:
    def __init__(self, config_file: str, scenario: str): ...
    def run(self) -> None: ...
    # was: bfsRunner(configFile, scenario) in legacy/../pbs/bfsRunner.py
    # internally uses XScaleArray, SimulationRunner, ConfidenceInterval, MetricsWriter
```

### `pcapprocessor/pbs/job_writer.py`

```python
class PbsJobWriter:
    def __init__(self, config_file: str, jobs_dir: str,
                 email: str = "", work_dir: str = ""): ...
    def write(self) -> None: ...
    # merges pbsWriter + cfgPbsWriter

    @classmethod
    def from_config(cls, config_file: str, jobs_dir: str) -> "PbsJobWriter": ...
    # factory for the cfg-driven variant (cfgPbsWriter style)
```

### `pcapprocessor/pbs/dce_runner.py`

```python
class DceRunner:
    def __init__(self, config_file: str, scenario: str): ...
    def run(self) -> None: ...
    # merges dceRunner + cfgWrapper
    # internally uses PbsJobWriter and BfsRunner
```

---

## Root Entry Point — `pcapprocessor.py`

`PcapProcessor` is expanded to accept all parameters needed to chain `TraceProcessor` → `MetricsWriter`. The previous `pyshark.FileCapture` / `PacketCollator` usage is removed — `TraceProcessor` uses `tcptrace` directly on the pcap file.

```python
class PcapProcessor:
    def __init__(
        self,
        pcap_file_path: str,
        unit: str,
        config,
        scenario: str,
        ascii_trace_file: str,
        buf_size: int,
    ): ...

    def process(self) -> list:
        # delegates to TraceProcessor
        return TraceProcessor(...).process()

    def process_and_write(self, x_array, pcap_file: str) -> None:
        # chains TraceProcessor → MetricsWriter
        metrics = self.process()
        MetricsWriter(metrics, x_array, self.scenario, self.config, pcap_file).write()
```

---

## What Is Deleted

| Old path | Reason |
|---|---|
| `pcapprocessor/legacy/` | Contents redistributed into `stats.py`, `simulation.py`, `trace.py`, `metrics.py`, `runner.py` |
| `pcapprocessor/metrics_calculator/` | `metricStats` restored as `MetricStats` class in `stats.py` |
| `pcapprocessor/pbs/bfsRunner.py` | Moved into `runner.py` as `BfsRunner` |
| `pcapprocessor/pbs/dceRunner.py` | Merged into `pbs/dce_runner.py` as `DceRunner` |
| `pcapprocessor/pbs/cfgWrapper.py` | Merged into `pbs/dce_runner.py` as `DceRunner` |
| `pcapprocessor/pbs/pbsWriter.py` | Merged into `pbs/job_writer.py` as `PbsJobWriter` |
| `pcapprocessor/pbs/cfgPbsWriter.py` | Merged into `pbs/job_writer.py` as `PbsJobWriter` |

---

## Out of Scope

- No new functionality is added
- No test coverage is added beyond what already exists (placeholder only)
- No changes to `requirements.txt`
- The `data/` directory and `.github/` workflows are untouched
