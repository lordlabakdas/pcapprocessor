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
