#!/usr/bin/env python3
"""Step 43: small numerical tightness checks for sample-complexity scaling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from phase0_baselines import run_switching_lds
from static_hypergraph_k3 import recover_hyperweights, simulate_static_k3_regression, support_metrics_hyper


def parse_int_list(text: str) -> list[int]:
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def fit_loglog_slope(x: np.ndarray, y: np.ndarray, eps: float = 1e-4) -> float:
    y_safe = np.maximum(y, eps)
    coeff = np.polyfit(np.log(x), np.log(y_safe), deg=1)
    return float(coeff[0])


def run_switching_tightness(
    out_dir: Path,
    t_values: list[int],
    seeds: list[int],
    n: int,
    sparsity: float,
    sigma: float,
    obs_noise: float,
    support_threshold: float,
) -> dict:
    rows: list[dict] = []
    for t in t_values:
        for seed in seeds:
            run_dir = out_dir / f"switching_t_{t}" / f"seed_{seed}"
            m = run_switching_lds(
                n=n,
                t=t,
                edge_prob=sparsity,
                sigma=sigma,
                seed=seed,
                out_dir=run_dir,
                support_threshold=support_threshold,
                obs_noise_sigma=obs_noise,
                stability_bootstrap_runs=6,
                stability_subsample_frac=0.75,
                stability_freq_threshold=0.55,
            )
            rows.append(
                {
                    "t": t,
                    "seed": seed,
                    "support_f1_mean": float(m["support_f1_mean"]),
                    "regime_accuracy": float(m["regime_accuracy"]),
                }
            )

    summary: dict[str, dict[str, float]] = {}
    for t in t_values:
        group = [r for r in rows if r["t"] == t]
        summary[str(t)] = {
            "runs": float(len(group)),
            "support_f1_mean": float(np.mean([r["support_f1_mean"] for r in group])),
            "support_f1_std": float(np.std([r["support_f1_mean"] for r in group], ddof=0)),
            "regime_acc_mean": float(np.mean([r["regime_accuracy"] for r in group])),
            "regime_acc_std": float(np.std([r["regime_accuracy"] for r in group], ddof=0)),
        }

    ts = np.array(t_values, dtype=np.float64)
    f1 = np.array([summary[str(t)]["support_f1_mean"] for t in t_values], dtype=np.float64)
    err = 1.0 - f1
    slope = fit_loglog_slope(ts, err)

    return {
        "runs": rows,
        "summary": summary,
        "error_slope_loglog": slope,
        "error_values": err.tolist(),
    }


def run_k3_tightness(
    out_dir: Path,
    t_values: list[int],
    seeds: list[int],
    n: int,
    edge_prob: float,
    noise_sigma: float,
    support_threshold: float,
) -> dict:
    rows: list[dict] = []

    for t in t_values:
        for seed in seeds:
            _, phi, y, h_true, _ = simulate_static_k3_regression(
                n=n,
                t=t,
                edge_prob=edge_prob,
                noise_sigma=noise_sigma,
                seed=seed,
            )
            h_hat = recover_hyperweights(phi=phi, y=y, seed=seed + 701)
            m = support_metrics_hyper(h_true, h_hat, threshold=support_threshold)
            rows.append(
                {
                    "t": t,
                    "seed": seed,
                    "support_f1": float(m["f1"]),
                    "precision": float(m["precision"]),
                    "recall": float(m["recall"]),
                }
            )

    summary: dict[str, dict[str, float]] = {}
    for t in t_values:
        group = [r for r in rows if r["t"] == t]
        summary[str(t)] = {
            "runs": float(len(group)),
            "support_f1_mean": float(np.mean([r["support_f1"] for r in group])),
            "support_f1_std": float(np.std([r["support_f1"] for r in group], ddof=0)),
            "precision_mean": float(np.mean([r["precision"] for r in group])),
            "recall_mean": float(np.mean([r["recall"] for r in group])),
        }

    ts = np.array(t_values, dtype=np.float64)
    f1 = np.array([summary[str(t)]["support_f1_mean"] for t in t_values], dtype=np.float64)
    err = 1.0 - f1
    slope = fit_loglog_slope(ts, err)

    return {
        "runs": rows,
        "summary": summary,
        "error_slope_loglog": slope,
        "error_values": err.tolist(),
    }


def plot_curves(out_dir: Path, t_values: list[int], switching: dict, k3: dict) -> None:
    ts = np.array(t_values, dtype=np.float64)
    s_f1 = np.array([switching["summary"][str(t)]["support_f1_mean"] for t in t_values], dtype=np.float64)
    k_f1 = np.array([k3["summary"][str(t)]["support_f1_mean"] for t in t_values], dtype=np.float64)

    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    ax.plot(ts, s_f1, marker="o", label="Switching support F1")
    ax.plot(ts, k_f1, marker="s", label="k=3 support F1")
    ax.set_xlabel("T")
    ax.set_ylabel("Support F1")
    ax.set_ylim(0.0, 1.05)
    ax.grid(alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "step43_f1_vs_t.png", dpi=170)
    plt.close(fig)

    s_err = np.maximum(1.0 - s_f1, 1e-4)
    k_err = np.maximum(1.0 - k_f1, 1e-4)

    fig2, ax2 = plt.subplots(1, 1, figsize=(7, 4))
    ax2.loglog(ts, s_err, marker="o", label=f"Switching error (slope={switching['error_slope_loglog']:.3f})")
    ax2.loglog(ts, k_err, marker="s", label=f"k=3 error (slope={k3['error_slope_loglog']:.3f})")
    ax2.set_xlabel("T (log)")
    ax2.set_ylabel("1 - F1 (log)")
    ax2.grid(alpha=0.3, which="both")
    ax2.legend(loc="best")
    fig2.tight_layout()
    fig2.savefig(out_dir / "step43_loglog_error_vs_t.png", dpi=170)
    plt.close(fig2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase1_step43_tightness"))
    parser.add_argument("--t-values", type=str, default="600,900,1200,1600")
    parser.add_argument("--seed-start", type=int, default=101)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--switching-n", type=int, default=10)
    parser.add_argument("--k3-n", type=int, default=10)
    parser.add_argument("--sparsity", type=float, default=0.10)
    parser.add_argument("--sigma", type=float, default=0.5)
    parser.add_argument("--obs-noise", type=float, default=0.15)
    parser.add_argument("--k3-noise", type=float, default=0.25)
    parser.add_argument("--switching-threshold", type=float, default=0.05)
    parser.add_argument("--k3-threshold", type=float, default=0.08)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    t_values = parse_int_list(args.t_values)
    seeds = [args.seed_start + i for i in range(args.seeds)]

    switching = run_switching_tightness(
        out_dir=out_dir,
        t_values=t_values,
        seeds=seeds,
        n=args.switching_n,
        sparsity=args.sparsity,
        sigma=args.sigma,
        obs_noise=args.obs_noise,
        support_threshold=args.switching_threshold,
    )

    k3 = run_k3_tightness(
        out_dir=out_dir,
        t_values=t_values,
        seeds=seeds,
        n=args.k3_n,
        edge_prob=0.12,
        noise_sigma=args.k3_noise,
        support_threshold=args.k3_threshold,
    )

    plot_curves(out_dir=out_dir, t_values=t_values, switching=switching, k3=k3)

    report = {
        "config": {
            "t_values": t_values,
            "seeds": seeds,
            "switching_n": args.switching_n,
            "k3_n": args.k3_n,
            "sparsity": args.sparsity,
            "sigma": args.sigma,
            "obs_noise": args.obs_noise,
            "k3_noise": args.k3_noise,
            "switching_threshold": args.switching_threshold,
            "k3_threshold": args.k3_threshold,
        },
        "switching": switching,
        "k3": k3,
        "tightness_logic": {
            "target_reference_slope": -0.5,
            "switching_slope": switching["error_slope_loglog"],
            "k3_slope": k3["error_slope_loglog"],
            "switching_improves_with_t": bool(
                switching["summary"][str(t_values[-1])]["support_f1_mean"]
                >= switching["summary"][str(t_values[0])]["support_f1_mean"]
            ),
            "k3_improves_with_t": bool(
                k3["summary"][str(t_values[-1])]["support_f1_mean"]
                >= k3["summary"][str(t_values[0])]["support_f1_mean"]
            ),
        },
    }

    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print("Step 43 tightness check complete.")
    print(json.dumps(report["tightness_logic"], indent=2))


if __name__ == "__main__":
    main()
