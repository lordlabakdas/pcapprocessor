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
