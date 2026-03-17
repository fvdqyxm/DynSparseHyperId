#!/usr/bin/env python3
"""Step 49: plot recovery curves as F1 vs T/N from Step 48 grid outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid-metrics", type=Path, default=Path("results/phase1_step48_grid/metrics_summary.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase1_step49_curves"))
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    report = json.loads(args.grid_metrics.read_text())
    runs = report["runs"]

    pts_by_k: dict[int, list[tuple[float, float]]] = {2: [], 3: []}
    for r in runs:
        ratio = float(r["t"]) / float(r["n"])
        pts_by_k[int(r["k"])].append((ratio, float(r["support_f1"])))

    summary = {}
    for k, pts in pts_by_k.items():
        ratios = sorted(set(p[0] for p in pts))
        curve = []
        for rr in ratios:
            vals = [p[1] for p in pts if abs(p[0] - rr) < 1e-12]
            curve.append((rr, float(np.mean(vals)), float(np.std(vals, ddof=0))))
        summary[f"k{k}"] = [
            {"t_over_n": rr, "f1_mean": mean, "f1_std": std}
            for rr, mean, std in curve
        ]

    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    markers = {2: "o", 3: "s"}
    for k in [2, 3]:
        if not summary.get(f"k{k}"):
            continue
        xs = np.array([x["t_over_n"] for x in summary[f"k{k}"]], dtype=np.float64)
        ys = np.array([x["f1_mean"] for x in summary[f"k{k}"]], dtype=np.float64)
        ax.plot(xs, ys, marker=markers[k], label=f"k={k}")
    ax.set_xlabel("T / N")
    ax.set_ylabel("Support F1")
    ax.set_ylim(0.0, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "f1_vs_t_over_n.png", dpi=170)
    plt.close(fig)

    out_report = {
        "source_grid": str(args.grid_metrics),
        "curve_summary": summary,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(out_report, indent=2))

    print("Step 49 recovery curves complete.")
    print(json.dumps({"keys": list(summary.keys())}, indent=2))


if __name__ == "__main__":
    main()
