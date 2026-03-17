#!/usr/bin/env python3
"""Robustness sweep for Step 15 switching LDS recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from phase0_baselines import run_switching_lds


def parse_float_list(text: str) -> list[float]:
    return [float(x.strip()) for x in text.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase0_switching_sweep"))
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--t", type=int, default=1400)
    parser.add_argument("--sparsity", type=float, default=0.1)
    parser.add_argument("--sigma", type=float, default=0.5)
    parser.add_argument("--support-threshold", type=float, default=0.05)
    parser.add_argument("--obs-noises", type=str, default="0.0,0.15,0.30")
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=31)
    parser.add_argument("--stability-bootstrap-runs", type=int, default=12)
    parser.add_argument("--stability-subsample-frac", type=float, default=0.75)
    parser.add_argument("--stability-freq-threshold", type=float, default=0.55)
    args = parser.parse_args()

    obs_noises = parse_float_list(args.obs_noises)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for obs_noise in obs_noises:
        for i in range(args.seeds):
            seed = args.seed_start + i
            run_dir = args.out_dir / f"obs_noise_{obs_noise:.2f}" / f"seed_{seed}"
            metrics = run_switching_lds(
                n=args.n,
                t=args.t,
                edge_prob=args.sparsity,
                sigma=args.sigma,
                seed=seed,
                out_dir=run_dir,
                support_threshold=args.support_threshold,
                obs_noise_sigma=obs_noise,
                stability_bootstrap_runs=args.stability_bootstrap_runs,
                stability_subsample_frac=args.stability_subsample_frac,
                stability_freq_threshold=args.stability_freq_threshold,
            )
            rows.append(
                {
                    "obs_noise": obs_noise,
                    "seed": seed,
                    "selected_method": metrics["selected_method"],
                    "regime_accuracy": metrics["regime_accuracy"],
                    "support_f1_mean": metrics["support_f1_mean"],
                    "hard_regime_accuracy": metrics["methods"]["hard_em"]["regime_accuracy"],
                    "hard_support_f1_mean": metrics["methods"]["hard_em"]["support_f1_mean"],
                    "hard_stab_support_f1_mean": metrics["methods"]["hard_em_stability"]["support_f1_mean"],
                    "soft_regime_accuracy": metrics["methods"]["soft_em_hmm"]["regime_accuracy"],
                    "soft_support_f1_mean": metrics["methods"]["soft_em_hmm"]["support_f1_mean"],
                    "soft_stab_support_f1_mean": metrics["methods"]["soft_em_hmm_stability"]["support_f1_mean"],
                    "oracle_support_f1_mean": metrics["methods"]["oracle_labels_ceiling"]["support_f1_mean"],
                }
            )

    by_obs_noise: dict[str, dict[str, float]] = {}
    for obs_noise in obs_noises:
        group = [r for r in rows if abs(r["obs_noise"] - obs_noise) < 1e-12]
        by_obs_noise[f"{obs_noise:.2f}"] = {
            "runs": float(len(group)),
            "regime_accuracy_mean": float(np.mean([r["regime_accuracy"] for r in group])),
            "regime_accuracy_std": float(np.std([r["regime_accuracy"] for r in group], ddof=1)),
            "support_f1_mean_mean": float(np.mean([r["support_f1_mean"] for r in group])),
            "support_f1_mean_std": float(np.std([r["support_f1_mean"] for r in group], ddof=1)),
            "hard_support_f1_mean": float(np.mean([r["hard_support_f1_mean"] for r in group])),
            "hard_stab_support_f1_mean": float(np.mean([r["hard_stab_support_f1_mean"] for r in group])),
            "soft_support_f1_mean": float(np.mean([r["soft_support_f1_mean"] for r in group])),
            "soft_stab_support_f1_mean": float(np.mean([r["soft_stab_support_f1_mean"] for r in group])),
            "oracle_support_f1_mean": float(np.mean([r["oracle_support_f1_mean"] for r in group])),
        }

    report = {
        "config": {
            "n": args.n,
            "t": args.t,
            "sparsity": args.sparsity,
            "sigma": args.sigma,
            "support_threshold": args.support_threshold,
            "obs_noises": obs_noises,
            "seeds": args.seeds,
            "seed_start": args.seed_start,
            "stability_bootstrap_runs": args.stability_bootstrap_runs,
            "stability_subsample_frac": args.stability_subsample_frac,
            "stability_freq_threshold": args.stability_freq_threshold,
        },
        "summary_by_obs_noise": by_obs_noise,
        "runs": rows,
    }
    (args.out_dir / "sweep_metrics.json").write_text(json.dumps(report, indent=2))

    # Plot aggregate trends.
    obs = np.array(obs_noises, dtype=np.float64)
    reg_means = np.array([by_obs_noise[f"{s:.2f}"]["regime_accuracy_mean"] for s in obs])
    f1_means = np.array([by_obs_noise[f"{s:.2f}"]["support_f1_mean_mean"] for s in obs])
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    ax.plot(obs, reg_means, marker="o", label="Regime accuracy")
    ax.plot(obs, f1_means, marker="s", label="Support F1 mean")
    ax.set_xlabel("Observation noise sigma")
    ax.set_ylabel("Metric")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(args.out_dir / "sweep_summary.png", dpi=170)
    plt.close(fig)

    print("Switching sweep complete.")
    print(json.dumps(report["summary_by_obs_noise"], indent=2))


if __name__ == "__main__":
    main()
