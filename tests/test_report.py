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
