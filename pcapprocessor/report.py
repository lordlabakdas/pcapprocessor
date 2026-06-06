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
