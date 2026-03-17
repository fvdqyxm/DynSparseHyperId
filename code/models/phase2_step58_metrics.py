#!/usr/bin/env python3
"""Step 58: aggregate multi-seed metrics and add switching-regime diagnostics."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from phase0_baselines import run_switching_lds


def _mean_std_ci(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return {
            "runs": 0.0,
            "mean": float("nan"),
            "std": float("nan"),
            "ci95_low": float("nan"),
            "ci95_high": float("nan"),
        }
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=0))
    half = 1.96 * std / np.sqrt(arr.size)
    return {
        "runs": float(arr.size),
        "mean": mean,
        "std": std,
        "ci95_low": float(mean - half),
        "ci95_high": float(mean + half),
    }


def _group_key(run: dict[str, Any]) -> str:
    return f"k{run['k']}_n{run['n']}_t{run['t']}_sigma{run['sigma']:.2f}"


def aggregate_structural(structural: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for run in structural["runs"]:
        key = _group_key(run)
        grouped[key]["support_f1"].append(float(run["support_f1"]))
        grouped[key]["precision"].append(float(run["precision"]))
        grouped[key]["recall"].append(float(run["recall"]))
        if "state_mse" in run:
            grouped[key]["state_mse"].append(float(run["state_mse"]))

    summary: dict[str, Any] = {}
    for key, metrics in grouped.items():
        entry: dict[str, Any] = {}
        for metric_name, vals in metrics.items():
            entry[metric_name] = _mean_std_ci(vals)
        summary[key] = entry
    return summary


def run_switching_metrics(
    out_dir: Path,
    seeds: list[int],
    t_values: list[int],
    obs_noises: list[float],
    stability_bootstrap_runs: int,
) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for t in t_values:
        for obs_noise in obs_noises:
            for seed in seeds:
                run_dir = out_dir / f"t_{t}" / f"obs_{obs_noise:.2f}" / f"seed_{seed}"
                m = run_switching_lds(
                    n=10,
                    t=t,
                    edge_prob=0.1,
                    sigma=0.5,
                    seed=seed,
                    out_dir=run_dir,
                    support_threshold=0.05,
                    obs_noise_sigma=obs_noise,
                    stability_bootstrap_runs=stability_bootstrap_runs,
                )
                runs.append(
                    {
                        "t": t,
                        "obs_noise": obs_noise,
                        "seed": seed,
                        "regime_accuracy": float(m["regime_accuracy"]),
                        "support_f1_mean": float(m["support_f1_mean"]),
                        "state_estimation_mse": float(m["state_estimation_mse"]),
                    }
                )

    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for run in runs:
        key = f"t{run['t']}_obs{run['obs_noise']:.2f}"
        grouped[key]["regime_accuracy"].append(float(run["regime_accuracy"]))
        grouped[key]["support_f1_mean"].append(float(run["support_f1_mean"]))
        grouped[key]["state_estimation_mse"].append(float(run["state_estimation_mse"]))

    summary: dict[str, Any] = {}
    for key, metrics in grouped.items():
        summary[key] = {m: _mean_std_ci(vals) for m, vals in metrics.items()}

    return {"runs": runs, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--structural-metrics",
        type=Path,
        default=Path("results/phase2_step57_multiseed/metrics_summary.json"),
    )
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step58_metrics"))
    parser.add_argument("--switching-seeds", type=int, default=3)
    parser.add_argument("--switching-seed-start", type=int, default=1501)
    parser.add_argument("--switching-t-values", type=str, default="600,1200,2000")
    parser.add_argument("--switching-obs-noises", type=str, default="0.15,0.30")
    parser.add_argument("--switching-stability-bootstrap-runs", type=int, default=6)
    args = parser.parse_args()

    structural = json.loads(args.structural_metrics.read_text())
    structural_summary = aggregate_structural(structural)

    seeds = [args.switching_seed_start + i for i in range(args.switching_seeds)]
    t_values = [int(x.strip()) for x in args.switching_t_values.split(",") if x.strip()]
    obs_noises = [float(x.strip()) for x in args.switching_obs_noises.split(",") if x.strip()]

    switching_dir = args.out_dir / "switching_runs"
    switching = run_switching_metrics(
        out_dir=switching_dir,
        seeds=seeds,
        t_values=t_values,
        obs_noises=obs_noises,
        stability_bootstrap_runs=args.switching_stability_bootstrap_runs,
    )

    report = {
        "config": {
            "structural_metrics": str(args.structural_metrics),
            "switching_seeds": seeds,
            "switching_t_values": t_values,
            "switching_obs_noises": obs_noises,
            "switching_stability_bootstrap_runs": args.switching_stability_bootstrap_runs,
        },
        "structural": {
            "num_runs": int(len(structural["runs"])),
            "summary_by_cell": structural_summary,
        },
        "switching": switching,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"structural_runs": len(structural["runs"]), "switching_runs": len(switching["runs"])}, indent=2))


if __name__ == "__main__":
    main()
