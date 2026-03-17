#!/usr/bin/env python3
"""Step 44: robustness sweep under heavy-tailed observation noise."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from phase0_baselines import run_switching_lds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase1_step44_noise_robustness"))
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--t", type=int, default=1400)
    parser.add_argument("--sparsity", type=float, default=0.10)
    parser.add_argument("--sigma", type=float, default=0.5)
    parser.add_argument("--obs-noise", type=float, default=0.15)
    parser.add_argument("--seed-start", type=int, default=201)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--support-threshold", type=float, default=0.05)
    parser.add_argument("--student-df", type=float, default=3.0)
    parser.add_argument("--outlier-prob", type=float, default=0.02)
    parser.add_argument("--outlier-scale", type=float, default=6.0)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    models = ["gaussian", "student_t", "contaminated"]
    seed_values = [args.seed_start + i for i in range(args.seeds)]

    rows: list[dict] = []
    for model in models:
        for seed in seed_values:
            run_dir = out_dir / model / f"seed_{seed}"
            m = run_switching_lds(
                n=args.n,
                t=args.t,
                edge_prob=args.sparsity,
                sigma=args.sigma,
                seed=seed,
                out_dir=run_dir,
                support_threshold=args.support_threshold,
                obs_noise_sigma=args.obs_noise,
                obs_noise_model=model,
                obs_noise_df=args.student_df,
                outlier_prob=args.outlier_prob,
                outlier_scale=args.outlier_scale,
                stability_bootstrap_runs=8,
                stability_subsample_frac=0.75,
                stability_freq_threshold=0.55,
            )
            rows.append(
                {
                    "model": model,
                    "seed": seed,
                    "support_f1_mean": float(m["support_f1_mean"]),
                    "regime_accuracy": float(m["regime_accuracy"]),
                }
            )

    summary: dict[str, dict[str, float]] = {}
    for model in models:
        group = [r for r in rows if r["model"] == model]
        summary[model] = {
            "runs": float(len(group)),
            "support_f1_mean": float(np.mean([r["support_f1_mean"] for r in group])),
            "support_f1_std": float(np.std([r["support_f1_mean"] for r in group], ddof=0)),
            "regime_acc_mean": float(np.mean([r["regime_accuracy"] for r in group])),
            "regime_acc_std": float(np.std([r["regime_accuracy"] for r in group], ddof=0)),
        }

    base_f1 = summary["gaussian"]["support_f1_mean"]
    base_acc = summary["gaussian"]["regime_acc_mean"]
    degradation = {
        model: {
            "support_f1_drop_vs_gaussian": float(base_f1 - stats["support_f1_mean"]),
            "regime_acc_drop_vs_gaussian": float(base_acc - stats["regime_acc_mean"]),
        }
        for model, stats in summary.items()
    }

    report = {
        "config": {
            "n": args.n,
            "t": args.t,
            "sparsity": args.sparsity,
            "sigma": args.sigma,
            "obs_noise": args.obs_noise,
            "seeds": seed_values,
            "student_df": args.student_df,
            "outlier_prob": args.outlier_prob,
            "outlier_scale": args.outlier_scale,
        },
        "summary_by_noise_model": summary,
        "degradation_vs_gaussian": degradation,
        "runs": rows,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    x = np.arange(len(models), dtype=np.float64)
    f1 = np.array([summary[m]["support_f1_mean"] for m in models], dtype=np.float64)
    acc = np.array([summary[m]["regime_acc_mean"] for m in models], dtype=np.float64)

    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    ax.bar(x - 0.18, f1, width=0.36, label="Support F1")
    ax.bar(x + 0.18, acc, width=0.36, label="Regime accuracy")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Metric")
    ax.set_title("Step 44 Robustness Across Noise Models")
    ax.grid(alpha=0.25, axis="y")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "noise_model_robustness.png", dpi=170)
    plt.close(fig)

    print("Step 44 noise robustness sweep complete.")
    print(json.dumps({"summary": summary, "degradation_vs_gaussian": degradation}, indent=2))


if __name__ == "__main__":
    main()
