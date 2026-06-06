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
        import matplotlib.pyplot as plt
        import seaborn as sns

        # Validate that metric columns exist for all protocols
        for protocol_name, cols in protocol_data.items():
            if f"avg_{metric}" not in cols or f"confInt_{metric}" not in cols:
                raise ValueError(f"unknown metric {metric!r} for protocol {protocol_name}")

        # Set seaborn theme
        sns.set_theme(style="whitegrid")

        # Create figure
        fig, ax = plt.subplots()

        # Get color palette
        palette = sns.color_palette()

        # Plot each protocol
        for idx, (proto, cols) in enumerate(protocol_data.items()):
            ax.errorbar(
                cols["x-scale"],
                cols[f"avg_{metric}"],
                yerr=cols[f"confInt_{metric}"] / 2,
                label=proto,
                capsize=4,
                color=palette[idx % len(palette)],
                marker="o"
            )

        # Set labels
        ax.set_xlabel("x-scale")
        ax.set_ylabel(metric)
        ax.set_title(metric)
        ax.legend()

        # Save figure
        out_path = os.path.join(self.output_dir, f"{metric}.{self.fmt}")
        fig.savefig(out_path, bbox_inches="tight")

        # Close figure
        plt.close(fig)

        # Return path
        return out_path
