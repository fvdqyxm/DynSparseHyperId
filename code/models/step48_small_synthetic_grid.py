#!/usr/bin/env python3
"""Step 48: small synthetic grid across k=2 and k=3 settings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from phase0_baselines import run_sparse_lds
from static_hypergraph_k3 import recover_hyperweights, simulate_static_k3_regression, support_metrics_hyper


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase1_step48_grid"))
    parser.add_argument("--seed-start", type=int, default=501)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--k2-n-values", type=str, default="20,35,50")
    parser.add_argument("--k3-n-values", type=str, default="20")
    parser.add_argument("--t-values", type=str, default="500,1000,2000")
    parser.add_argument("--sparsity", type=float, default=0.10)
    parser.add_argument("--sigma", type=float, default=0.5)
    parser.add_argument("--k3-noise", type=float, default=0.25)
    parser.add_argument("--k2-threshold", type=float, default=0.05)
    parser.add_argument("--k3-threshold", type=float, default=0.08)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    k2_n_values = [int(x.strip()) for x in args.k2_n_values.split(",") if x.strip()]
    k3_n_values = [int(x.strip()) for x in args.k3_n_values.split(",") if x.strip()]
    t_values = [int(x.strip()) for x in args.t_values.split(",") if x.strip()]
    seeds = [args.seed_start + i for i in range(args.seeds)]

    runs: list[dict] = []

    # k=2 (pairwise sparse LDS) grid.
    for n in k2_n_values:
        for t in t_values:
            for seed in seeds:
                run_dir = out_dir / "k2" / f"n_{n}" / f"t_{t}" / f"seed_{seed}"
                m = run_sparse_lds(
                    n=n,
                    t=t,
                    edge_prob=args.sparsity,
                    sigma=args.sigma,
                    seed=seed,
                    out_dir=run_dir,
                    support_threshold=args.k2_threshold,
                )
                runs.append(
                    {
                        "k": 2,
                        "n": n,
                        "t": t,
                        "seed": seed,
                        "support_f1": float(m["support_metrics"]["f1"]),
                    }
                )

    # k=3 (static hypergraph surrogate) grid.
    for n in k3_n_values:
        for t in t_values:
            for seed in seeds:
                _, phi, y, h_true, _ = simulate_static_k3_regression(
                    n=n,
                    t=t,
                    edge_prob=0.12,
                    noise_sigma=args.k3_noise,
                    seed=seed,
                )
                h_hat = recover_hyperweights(phi=phi, y=y, seed=seed + 701)
                m = support_metrics_hyper(h_true, h_hat, threshold=args.k3_threshold)
                runs.append(
                    {
                        "k": 3,
                        "n": n,
                        "t": t,
                        "seed": seed,
                        "support_f1": float(m["f1"]),
                    }
                )

    summary: dict[str, dict[str, float]] = {}
    for k in [2, 3]:
        for n in (k2_n_values if k == 2 else k3_n_values):
            for t in t_values:
                key = f"k{k}_n{n}_t{t}"
                group = [r for r in runs if r["k"] == k and r["n"] == n and r["t"] == t]
                if not group:
                    continue
                summary[key] = {
                    "runs": float(len(group)),
                    "support_f1_mean": float(np.mean([r["support_f1"] for r in group])),
                    "support_f1_std": float(np.std([r["support_f1"] for r in group], ddof=0)),
                }

    report = {
        "config": {
            "k2_n_values": k2_n_values,
            "k3_n_values": k3_n_values,
            "t_values": t_values,
            "seeds": seeds,
            "sparsity": args.sparsity,
            "sigma": args.sigma,
            "k3_noise": args.k3_noise,
        },
        "summary": summary,
        "runs": runs,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    # Plot k=2 curves across N.
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    for n in k2_n_values:
        y = [summary[f"k2_n{n}_t{t}"]["support_f1_mean"] for t in t_values]
        ax.plot(t_values, y, marker="o", label=f"k=2, N={n}")
    ax.set_xlabel("T")
    ax.set_ylabel("Support F1")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "k2_grid_f1.png", dpi=170)
    plt.close(fig)

    fig2, ax2 = plt.subplots(1, 1, figsize=(7, 4))
    for n in k3_n_values:
        y = [summary[f"k3_n{n}_t{t}"]["support_f1_mean"] for t in t_values]
        ax2.plot(t_values, y, marker="s", label=f"k=3, N={n}")
    ax2.set_xlabel("T")
    ax2.set_ylabel("Support F1")
    ax2.set_ylim(0, 1.05)
    ax2.grid(alpha=0.25)
    ax2.legend(loc="best")
    fig2.tight_layout()
    fig2.savefig(out_dir / "k3_grid_f1.png", dpi=170)
    plt.close(fig2)

    print("Step 48 small synthetic grid complete.")
    print(json.dumps({"num_runs": len(runs), "summary_keys": len(summary)}, indent=2))


if __name__ == "__main__":
    main()
