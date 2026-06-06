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
        return np.array(list(map(float, self.xscale)))


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
