# Reporting Design

**Date:** 2026-06-05
**Scope:** Static figure generation from pcapprocessor metric CSVs

---

## Goal

Generate publication-quality PNG or SVG figures from the tab-separated CSV files produced by `MetricsWriter`. One figure per metric, all protocols overlaid on the same axes, confidence interval error bars.

---

## Architecture

One new file: `pcapprocessor/report.py`. Follows the existing stateful-class pattern (inputs in `__init__`, work in a named method).

```
pcapprocessor/
└── report.py        ← Reporter class + CLI entry point
tests/
└── test_report.py   ← unit tests
```

No new dependencies. Uses `matplotlib` and `seaborn`, both already present in the venv.

---

## Class Design

```python
class Reporter:
    def __init__(
        self,
        csvs: list[str],
        metrics: list[str],
        output_dir: str = "plots",
        fmt: str = "png",
    ): ...

    def plot(self) -> list[str]:
        """Generate one figure per metric. Returns list of written file paths."""

    def _load_csv(self, path: str) -> dict:
        """Read one tab-separated CSV. Returns dict of column_name → np.ndarray."""

    def _plot_metric(self, metric: str, protocol_data: dict[str, dict]) -> str:
        """Draw one figure (all protocols overlaid), save, return output path."""
```

### `plot()`

1. Creates `output_dir` if it does not exist.
2. Calls `_load_csv` for each path in `self.csvs`.
3. Derives protocol name from the CSV filename stem (e.g. `results/tcp0.csv` → `"tcp0"`).
4. For each metric in `self.metrics`, calls `_plot_metric` and collects the returned path.
5. Returns the list of written paths.

### `_load_csv(path)`

- Reads the tab-separated file with `numpy.genfromtxt` (or `csv` module) using the first row as column headers.
- Returns `{column_name: np.ndarray}`.
- Raises `FileNotFoundError` if the path does not exist.

### `_plot_metric(metric, protocol_data)`

`protocol_data` is `{protocol_name: column_dict}` for all loaded CSVs.

- Validates that `avg_{metric}` and `confInt_{metric}` exist in every protocol's column dict. Raises `ValueError` if not, naming the missing metric and the CSV it came from.
- Calls `seaborn.set_theme(style="whitegrid")`.
- Plots one line per protocol: x = `x-scale` column, y = `avg_{metric}`, `yerr = confInt_{metric} / 2` (half-width, since `confInt` stores the full CI width from `2 × t × SEM`).
- Labels: x-axis = `"x-scale"`, y-axis = metric name, legend = protocol names.
- Saves to `{output_dir}/{metric}.{fmt}` with `bbox_inches="tight"`.
- Closes the figure after saving to free memory.
- Returns the saved path.

---

## CLI

Runnable as a module:

```bash
python -m pcapprocessor.report \
  --csvs results/tcp0.csv results/udp0.csv \
  --metrics throughput utilization delay \
  --output plots/ \
  --format png
```

| Flag | Required | Default | Description |
|---|---|---|---|
| `--csvs` | yes | — | One or more CSV paths |
| `--metrics` | yes | — | Metric short names (`throughput`, `delay`, …) |
| `--output` | no | `./plots` | Output directory (created if missing) |
| `--format` | no | `png` | `png` or `svg` |

On success: prints each written path to stdout.
On error: exits with code 1 and a descriptive message (unknown metric, missing column, missing file).

---

## Metric Name Resolution

User-facing short names map to CSV columns as follows:

| Short name | avg column | confInt column |
|---|---|---|
| `throughput` | `avg_throughput` | `confInt_throughput` |
| `delay` | `avg_delay` | `confInt_delay` |
| `utilization` | `avg_utilization` | `confInt_utilization` |
| *(any metric)* | `avg_{metric}` | `confInt_{metric}` |

Valid short names are any string that appears between `avg_` and the end of a column header. The reporter does not hardcode the list — it validates against actual column names present in the CSV.

---

## Figure Style

- `seaborn.set_theme(style="whitegrid")`
- One line per protocol, colours from seaborn's default palette
- Error bars: `plt.errorbar` with `yerr=confInt/2`, `capsize=4`
- Legend shows protocol names
- Title: metric short name
- Output: `{output_dir}/{metric}.{fmt}`, `bbox_inches="tight"`

---

## Testing

`tests/test_report.py` covers:

- `_load_csv` returns correct column arrays from a temp CSV
- `_load_csv` raises `FileNotFoundError` for missing file
- `_plot_metric` raises `ValueError` for unknown metric name
- `plot()` creates the output directory and writes one file per metric
- `plot()` returns the correct list of paths
- CLI (`__main__`) exits non-zero on missing `--csvs` / `--metrics`

Figures are generated with `matplotlib.use("Agg")` (non-interactive backend) so tests run headlessly without a display.

---

## Out of Scope

- Interactive dashboards
- Automatic metric selection (user always specifies `--metrics`)
- Multi-scenario comparison across different config runs
- PDF or PowerPoint export
