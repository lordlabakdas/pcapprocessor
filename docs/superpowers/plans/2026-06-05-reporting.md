# Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `Reporter` class to `pcapprocessor` that reads metric CSVs and generates one PNG/SVG figure per requested metric, with protocols overlaid and confidence interval error bars.

**Architecture:** `Reporter` follows the existing stateful-class pattern. `_load_csv` reads one tab-separated CSV into column arrays. `_plot_metric` draws one figure for all protocols and saves it. `plot()` orchestrates both. A `__main__` block wires up the CLI.

**Tech Stack:** Python 3.10+, matplotlib, seaborn (both already in venv/requirements). No new dependencies.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `pcapprocessor/report.py` | Create | `Reporter` class + `__main__` CLI |
| `tests/test_report.py` | Create | Unit tests (headless Agg backend) |
| `pcapprocessor/__init__.py` | Modify | Export `Reporter` |

---

### Task 1: `_load_csv` — read one CSV into column arrays

**Files:**
- Create: `pcapprocessor/report.py`
- Create: `tests/test_report.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_report.py
import csv
import os

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pytest

from pcapprocessor.report import Reporter


def _write_csv(path, headers, rows):
    """Write tab-separated rows to path."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(headers)
        writer.writerows(rows)


def test_load_csv_returns_column_arrays(tmp_path):
    csv_path = tmp_path / "tcp0.csv"
    _write_csv(csv_path,
               ["x-scale", "avg_throughput", "confInt_throughput"],
               [[1.0, 10.5, 0.4], [2.0, 20.1, 0.6]])
    r = Reporter(csvs=[str(csv_path)], metrics=["throughput"],
                 output_dir=str(tmp_path / "plots"))
    data = r._load_csv(str(csv_path))
    assert list(data.keys()) == ["x-scale", "avg_throughput", "confInt_throughput"]
    np.testing.assert_array_almost_equal(data["avg_throughput"], [10.5, 20.1])


def test_load_csv_raises_for_missing_file(tmp_path):
    r = Reporter(csvs=[], metrics=[], output_dir=str(tmp_path / "plots"))
    with pytest.raises(FileNotFoundError):
        r._load_csv(str(tmp_path / "nonexistent.csv"))
```

- [ ] **Step 2: Run to confirm it fails**

```bash
pytest tests/test_report.py::test_load_csv_returns_column_arrays tests/test_report.py::test_load_csv_raises_for_missing_file -v
```

Expected: `ERROR` — `ModuleNotFoundError: No module named 'pcapprocessor.report'`

- [ ] **Step 3: Create `pcapprocessor/report.py` with `Reporter.__init__` and `_load_csv`**

```python
# pcapprocessor/report.py
import csv
import os

import numpy as np


class Reporter:
    def __init__(
        self,
        csvs: list,
        metrics: list,
        output_dir: str = "plots",
        fmt: str = "png",
    ):
        self.csvs = csvs
        self.metrics = metrics
        self.output_dir = output_dir
        self.fmt = fmt

    def plot(self) -> list:
        raise NotImplementedError

    def _load_csv(self, path: str) -> dict:
        with open(path, newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            headers = next(reader)
            rows = list(reader)
        data = np.array(rows, dtype=float)
        return {headers[i]: data[:, i] for i in range(len(headers))}

    def _plot_metric(self, metric: str, protocol_data: dict) -> str:
        raise NotImplementedError
```

Note: `open()` raises `FileNotFoundError` natively — no explicit check needed.

- [ ] **Step 4: Run tests — expect both to pass**

```bash
pytest tests/test_report.py::test_load_csv_returns_column_arrays tests/test_report.py::test_load_csv_raises_for_missing_file -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add pcapprocessor/report.py tests/test_report.py
git commit -m "feat: add Reporter._load_csv with tab-separated CSV parsing"
```

---

### Task 2: `_plot_metric` — draw one figure for all protocols

**Files:**
- Modify: `pcapprocessor/report.py`
- Modify: `tests/test_report.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_report.py` (after the existing `_write_csv` helper and existing tests):

```python
def _make_protocol_data(tmp_path, name="tcp0",
                        x=(1.0, 2.0), avg=(10.0, 20.0), ci=(0.5, 0.8)):
    csv_path = tmp_path / f"{name}.csv"
    _write_csv(csv_path,
               ["x-scale", "avg_throughput", "confInt_throughput"],
               [[x[0], avg[0], ci[0]], [x[1], avg[1], ci[1]]])
    r = Reporter(csvs=[str(csv_path)], metrics=["throughput"],
                 output_dir=str(tmp_path / "plots"))
    return str(csv_path), {name: r._load_csv(str(csv_path))}


def test_plot_metric_creates_file(tmp_path):
    _, protocol_data = _make_protocol_data(tmp_path)
    out = str(tmp_path / "plots")
    os.makedirs(out, exist_ok=True)
    r = Reporter(csvs=[], metrics=[], output_dir=out)
    path = r._plot_metric("throughput", protocol_data)
    assert os.path.exists(path)
    assert path.endswith(".png")


def test_plot_metric_raises_for_unknown_metric(tmp_path):
    _, protocol_data = _make_protocol_data(tmp_path)
    out = str(tmp_path / "plots")
    os.makedirs(out, exist_ok=True)
    r = Reporter(csvs=[], metrics=[], output_dir=out)
    with pytest.raises(ValueError, match="delay"):
        r._plot_metric("delay", protocol_data)


def test_plot_metric_filename_uses_metric_name(tmp_path):
    _, protocol_data = _make_protocol_data(tmp_path)
    out = str(tmp_path / "plots")
    os.makedirs(out, exist_ok=True)
    r = Reporter(csvs=[], metrics=[], output_dir=out, fmt="svg")
    path = r._plot_metric("throughput", protocol_data)
    assert path == os.path.join(out, "throughput.svg")
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_report.py::test_plot_metric_creates_file tests/test_report.py::test_plot_metric_raises_for_unknown_metric tests/test_report.py::test_plot_metric_filename_uses_metric_name -v
```

Expected: `FAILED` — `NotImplementedError`

- [ ] **Step 3: Implement `_plot_metric` in `pcapprocessor/report.py`**

Replace the `_plot_metric` stub:

```python
    def _plot_metric(self, metric: str, protocol_data: dict) -> str:
        import matplotlib.pyplot as plt
        import seaborn as sns

        avg_col = f"avg_{metric}"
        ci_col = f"confInt_{metric}"

        for proto, cols in protocol_data.items():
            if avg_col not in cols or ci_col not in cols:
                available = [k[4:] for k in cols if k.startswith("avg_")]
                raise ValueError(
                    f"unknown metric {metric!r} for protocol {proto!r}. "
                    f"Available: {available}"
                )

        sns.set_theme(style="whitegrid")
        palette = sns.color_palette()
        fig, ax = plt.subplots()

        for idx, (proto, cols) in enumerate(protocol_data.items()):
            ax.errorbar(
                cols["x-scale"],
                cols[avg_col],
                yerr=cols[ci_col] / 2,
                label=proto,
                capsize=4,
                color=palette[idx % len(palette)],
                marker="o",
            )

        ax.set_xlabel("x-scale")
        ax.set_ylabel(metric)
        ax.set_title(metric)
        ax.legend()

        out_path = os.path.join(self.output_dir, f"{metric}.{self.fmt}")
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        return out_path
```

- [ ] **Step 4: Run all tests so far — expect 5 to pass**

```bash
pytest tests/test_report.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add pcapprocessor/report.py tests/test_report.py
git commit -m "feat: implement Reporter._plot_metric with seaborn styling and CI error bars"
```

---

### Task 3: `plot()`, CLI, and `__init__.py` export

**Files:**
- Modify: `pcapprocessor/report.py`
- Modify: `pcapprocessor/__init__.py`
- Modify: `tests/test_report.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_report.py`:

```python
def test_plot_creates_one_file_per_metric(tmp_path):
    for name in ("tcp0.csv", "udp0.csv"):
        _write_csv(
            tmp_path / name,
            ["x-scale", "avg_throughput", "confInt_throughput",
             "avg_delay", "confInt_delay"],
            [[1.0, 10.0, 0.5, 5.0, 0.1], [2.0, 20.0, 0.8, 4.5, 0.2]],
        )
    out = str(tmp_path / "plots")
    r = Reporter(
        csvs=[str(tmp_path / "tcp0.csv"), str(tmp_path / "udp0.csv")],
        metrics=["throughput", "delay"],
        output_dir=out,
    )
    paths = r.plot()
    assert len(paths) == 2
    assert all(os.path.exists(p) for p in paths)
    assert any("throughput" in p for p in paths)
    assert any("delay" in p for p in paths)


def test_plot_creates_output_dir(tmp_path):
    _write_csv(
        tmp_path / "tcp0.csv",
        ["x-scale", "avg_throughput", "confInt_throughput"],
        [[1.0, 10.0, 0.5]],
    )
    out = str(tmp_path / "new_dir" / "plots")
    r = Reporter(csvs=[str(tmp_path / "tcp0.csv")],
                 metrics=["throughput"], output_dir=out)
    r.plot()
    assert os.path.isdir(out)


def test_reporter_importable_from_package():
    from pcapprocessor import Reporter as R
    assert R is not None


def test_cli_exits_zero_on_success(tmp_path):
    import subprocess
    import sys
    _write_csv(
        tmp_path / "tcp0.csv",
        ["x-scale", "avg_throughput", "confInt_throughput"],
        [[10.0, 100.0, 5.0], [20.0, 200.0, 8.0]],
    )
    result = subprocess.run(
        [sys.executable, "-m", "pcapprocessor.report",
         "--csvs", str(tmp_path / "tcp0.csv"),
         "--metrics", "throughput",
         "--output", str(tmp_path / "plots")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "throughput.png" in result.stdout


def test_cli_exits_nonzero_on_missing_metric(tmp_path):
    import subprocess
    import sys
    _write_csv(
        tmp_path / "tcp0.csv",
        ["x-scale", "avg_throughput", "confInt_throughput"],
        [[10.0, 100.0, 5.0]],
    )
    result = subprocess.run(
        [sys.executable, "-m", "pcapprocessor.report",
         "--csvs", str(tmp_path / "tcp0.csv"),
         "--metrics", "nonexistent",
         "--output", str(tmp_path / "plots")],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "Error" in result.stderr
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_report.py::test_plot_creates_one_file_per_metric tests/test_report.py::test_plot_creates_output_dir tests/test_report.py::test_reporter_importable_from_package tests/test_report.py::test_cli_exits_zero_on_success tests/test_report.py::test_cli_exits_nonzero_on_missing_metric -v
```

Expected: `FAILED` — `NotImplementedError` (plot), `ImportError` (Reporter not in package)

- [ ] **Step 3: Implement `plot()` in `pcapprocessor/report.py`**

Replace the `plot` stub:

```python
    def plot(self) -> list:
        os.makedirs(self.output_dir, exist_ok=True)
        protocol_data = {
            os.path.splitext(os.path.basename(path))[0]: self._load_csv(path)
            for path in self.csvs
        }
        return [self._plot_metric(metric, protocol_data) for metric in self.metrics]
```

- [ ] **Step 4: Add `__main__` CLI block to the bottom of `pcapprocessor/report.py`**

```python
if __name__ == "__main__":
    import argparse
    import sys

    def _main() -> int:
        parser = argparse.ArgumentParser(
            description="Generate metric figures from pcapprocessor CSV output."
        )
        parser.add_argument("--csvs", nargs="+", required=True,
                            help="Paths to metric CSV files (one per protocol)")
        parser.add_argument("--metrics", nargs="+", required=True,
                            help="Metric short names to plot (e.g. throughput delay)")
        parser.add_argument("--output", default="plots",
                            help="Output directory (default: plots)")
        parser.add_argument("--format", choices=["png", "svg"], default="png",
                            dest="fmt", help="Output format (default: png)")
        args = parser.parse_args()

        try:
            paths = Reporter(
                csvs=args.csvs,
                metrics=args.metrics,
                output_dir=args.output,
                fmt=args.fmt,
            ).plot()
            for p in paths:
                print(p)
            return 0
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    sys.exit(_main())
```

- [ ] **Step 5: Export `Reporter` from `pcapprocessor/__init__.py`**

Current content of `pcapprocessor/__init__.py`:
```python
from pcapprocessor.processor import PcapProcessor
from pcapprocessor.stats import ConfidenceInterval, MetricStats, XScaleArray
from pcapprocessor.simulation import QueueSizeCalculator, WafCommandBuilder
from pcapprocessor.trace import TraceProcessor
from pcapprocessor.metrics import MetricsWriter
from pcapprocessor.runner import BfsRunner, SimulationRunner

__all__ = [
    "PcapProcessor",
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

Replace with:
```python
from pcapprocessor.processor import PcapProcessor
from pcapprocessor.stats import ConfidenceInterval, MetricStats, XScaleArray
from pcapprocessor.simulation import QueueSizeCalculator, WafCommandBuilder
from pcapprocessor.trace import TraceProcessor
from pcapprocessor.metrics import MetricsWriter
from pcapprocessor.runner import BfsRunner, SimulationRunner
from pcapprocessor.report import Reporter

__all__ = [
    "PcapProcessor",
    "ConfidenceInterval",
    "MetricStats",
    "XScaleArray",
    "QueueSizeCalculator",
    "WafCommandBuilder",
    "TraceProcessor",
    "MetricsWriter",
    "BfsRunner",
    "SimulationRunner",
    "Reporter",
]
```

- [ ] **Step 6: Run the full test suite**

```bash
pytest tests/test_report.py -v
```

Expected: `10 passed`

- [ ] **Step 7: Smoke-test the CLI end-to-end**

```bash
printf "x-scale\tavg_throughput\tconfInt_throughput\tavg_delay\tconfInt_delay\n10\t5.2\t0.3\t12.1\t0.5\n20\t9.8\t0.4\t10.3\t0.4\n30\t14.1\t0.6\t9.7\t0.3\n" > /tmp/tcp0.csv

python -m pcapprocessor.report \
  --csvs /tmp/tcp0.csv \
  --metrics throughput delay \
  --output /tmp/report_out \
  --format png

ls -lh /tmp/report_out/
```

Expected: two files — `throughput.png` and `delay.png` — both non-empty.

- [ ] **Step 8: Run the full project test suite to check for regressions**

```bash
pytest --cov=pcapprocessor --cov-report=term-missing -q
```

Expected: all tests pass, coverage ≥ 90%.

- [ ] **Step 9: Commit**

```bash
git add pcapprocessor/report.py pcapprocessor/__init__.py tests/test_report.py
git commit -m "feat: add Reporter.plot(), CLI entry point, and package export"
```
