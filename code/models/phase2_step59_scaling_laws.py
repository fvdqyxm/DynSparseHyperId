#!/usr/bin/env python3
"""Step 59: compute and plot scaling-law slopes from Step-58 metrics."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


STRUCT_RE = re.compile(r"^k(?P<k>\d+)_n(?P<n>\d+)_t(?P<t>\d+)_sigma(?P<sigma>\d+\.\d+)$")
SWITCH_RE = re.compile(r"^t(?P<t>\d+)_obs(?P<obs>\d+\.\d+)$")


def _fit_loglog_slope(xs: list[float], ys: list[float]) -> float:
    x = np.asarray(xs, dtype=np.float64)
    y = np.asarray(ys, dtype=np.float64)
    if x.size < 2 or np.any(x <= 0) or np.any(y <= 0):
        return float("nan")
    return float(np.polyfit(np.log(x), np.log(y), 1)[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("results/phase2_step58_metrics/metrics_summary.json"),
    )
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step59_scaling"))
    parser.add_argument("--error-floor", type=float, default=1e-6)
    args = parser.parse_args()

    payload = json.loads(args.metrics.read_text())
    structural = payload["structural"]["summary_by_cell"]
    switching = payload["switching"]["summary"]

    structural_groups: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"t": [], "err": []})
    for key, vals in structural.items():
        m = STRUCT_RE.match(key)
        if m is None:
            continue
        gkey = f"k{m.group('k')}_n{m.group('n')}_sigma{m.group('sigma')}"
        t = float(int(m.group("t")))
        f1 = float(vals["support_f1"]["mean"])
        err = max(1.0 - f1, args.error_floor)
        structural_groups[gkey]["t"].append(t)
        structural_groups[gkey]["err"].append(err)

    structural_slopes: dict[str, float] = {}
    for gkey, dat in structural_groups.items():
        order = np.argsort(dat["t"])
        ts = [dat["t"][i] for i in order]
        errs = [dat["err"][i] for i in order]
        structural_slopes[gkey] = _fit_loglog_slope(ts, errs)

    switching_groups: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"t": [], "reg_err": [], "mse": []}
    )
    for key, vals in switching.items():
        m = SWITCH_RE.match(key)
        if m is None:
            continue
        gkey = f"obs{m.group('obs')}"
        t = float(int(m.group("t")))
        reg_acc = float(vals["regime_accuracy"]["mean"])
        mse = float(vals["state_estimation_mse"]["mean"])
        switching_groups[gkey]["t"].append(t)
        switching_groups[gkey]["reg_err"].append(max(1.0 - reg_acc, args.error_floor))
        switching_groups[gkey]["mse"].append(max(mse, args.error_floor))

    switching_slopes: dict[str, dict[str, float]] = {}
    for gkey, dat in switching_groups.items():
        order = np.argsort(dat["t"])
        ts = [dat["t"][i] for i in order]
        reg_err = [dat["reg_err"][i] for i in order]
        mse = [dat["mse"][i] for i in order]
        switching_slopes[gkey] = {
            "regime_error_slope_loglog": _fit_loglog_slope(ts, reg_err),
            "state_mse_slope_loglog": _fit_loglog_slope(ts, mse),
        }

    args.out_dir.mkdir(parents=True, exist_ok=True)

    fig1, ax1 = plt.subplots(1, 1, figsize=(8, 4.5))
    for gkey, dat in sorted(structural_groups.items()):
        order = np.argsort(dat["t"])
        ts = np.array([dat["t"][i] for i in order], dtype=np.float64)
        errs = np.array([dat["err"][i] for i in order], dtype=np.float64)
        ax1.plot(ts, errs, marker="o", label=gkey)
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlabel("T (log)")
    ax1.set_ylabel("Support Error = 1 - F1 (log)")
    ax1.set_title("Step 59 Structural Scaling Laws")
    ax1.grid(alpha=0.25)
    ax1.legend(loc="best", fontsize=7)
    fig1.tight_layout()
    fig1.savefig(args.out_dir / "structural_scaling_loglog.png", dpi=170)
    plt.close(fig1)

    fig2, ax2 = plt.subplots(1, 1, figsize=(7, 4.2))
    for gkey, dat in sorted(switching_groups.items()):
        order = np.argsort(dat["t"])
        ts = np.array([dat["t"][i] for i in order], dtype=np.float64)
        errs = np.array([dat["reg_err"][i] for i in order], dtype=np.float64)
        ax2.plot(ts, errs, marker="s", label=f"{gkey} regime error")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("T (log)")
    ax2.set_ylabel("Regime Error = 1 - Accuracy (log)")
    ax2.set_title("Step 59 Switching Scaling Laws")
    ax2.grid(alpha=0.25)
    ax2.legend(loc="best", fontsize=8)
    fig2.tight_layout()
    fig2.savefig(args.out_dir / "switching_regime_scaling_loglog.png", dpi=170)
    plt.close(fig2)

    report = {
        "source_metrics": str(args.metrics),
        "structural_slopes_loglog": structural_slopes,
        "switching_slopes_loglog": switching_slopes,
    }
    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"structural_groups": len(structural_groups), "switching_groups": len(switching_groups)}, indent=2))


if __name__ == "__main__":
    main()
