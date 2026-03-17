#!/usr/bin/env python3
"""Phase 2 Step 56: scalable synthetic-grid runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from phase0_baselines import run_sparse_lds
from static_hypergraph_korder import (
    recover_hyperweights_korder,
    simulate_static_korder_regression,
    support_metrics_hyper,
)


def parse_int_list(text: str) -> list[int]:
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def parse_float_list(text: str) -> list[float]:
    return [float(x.strip()) for x in text.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step56_large_grid"))
    parser.add_argument("--n-values", type=str, default="20,50,100")
    parser.add_argument("--k-values", type=str, default="2,3,4")
    parser.add_argument("--t-values", type=str, default="500,2000")
    parser.add_argument("--sigma-values", type=str, default="0.2,0.5,1.0")
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--seed-start", type=int, default=801)
    parser.add_argument("--max-runs", type=int, default=0)
    parser.add_argument("--max-features-khigh", type=int, default=2500)
    parser.add_argument("--max-targets-khigh", type=int, default=24)
    parser.add_argument("--cv-complexity-limit-k2", type=int, default=200_000)
    parser.add_argument("--alpha-scale-k2", type=float, default=0.35)
    parser.add_argument("--cv-complexity-limit", type=int, default=2_000_000)
    parser.add_argument("--alpha-scale-khigh", type=float, default=0.35)
    parser.add_argument("--support-threshold-k2", type=float, default=0.05)
    parser.add_argument("--support-threshold-k3", type=float, default=0.08)
    parser.add_argument("--support-threshold-k4", type=float, default=0.08)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    n_values = parse_int_list(args.n_values)
    k_values = parse_int_list(args.k_values)
    t_values = parse_int_list(args.t_values)
    sigma_values = parse_float_list(args.sigma_values)
    seeds = [args.seed_start + i for i in range(args.seeds)]

    requested = []
    for n in n_values:
        for k in k_values:
            for t in t_values:
                for sigma in sigma_values:
                    for seed in seeds:
                        requested.append((n, k, t, sigma, seed))

    runs = []
    skipped = []
    if args.max_runs > 0:
        limit = min(args.max_runs, len(requested))
    else:
        limit = len(requested)

    for n, k, t, sigma, seed in requested[:limit]:
        if k == 2:
            run_dir = out_dir / f"k{k}" / f"n_{n}" / f"t_{t}" / f"sigma_{sigma:.2f}" / f"seed_{seed}"
            n_train_samples = max(int(0.8 * t) - 1, 1)
            use_cv_k2 = (n_train_samples * n) <= args.cv_complexity_limit_k2
            m = run_sparse_lds(
                n=n,
                t=t,
                edge_prob=max(np.log(max(n, 2)) / max(n, 2), 0.02),
                sigma=sigma,
                seed=seed,
                out_dir=run_dir,
                support_threshold=args.support_threshold_k2,
                cv_complexity_limit=args.cv_complexity_limit_k2,
                alpha_scale=args.alpha_scale_k2,
            )
            runs.append(
                {
                    "n": n,
                    "k": k,
                    "t": t,
                    "sigma": sigma,
                    "seed": seed,
                    "support_f1": float(m["support_metrics"]["f1"]),
                    "precision": float(m["support_metrics"]["precision"]),
                    "recall": float(m["support_metrics"]["recall"]),
                    "state_mse": float(m["validation_one_step_mse"]),
                    "solver": "lasso_cv" if use_cv_k2 else "lasso_scaled",
                    "status": "ok",
                }
            )
        elif k >= 3:
            _, phi, y, h_true, combos = simulate_static_korder_regression(
                n=n,
                t=t,
                k=k,
                edge_prob=max(np.log(max(n, 2)) / max(n, 2), 0.02),
                noise_sigma=sigma,
                seed=seed,
                max_features=args.max_features_khigh,
            )
            if args.max_targets_khigh > 0 and y.shape[1] > args.max_targets_khigh:
                rng = np.random.default_rng(seed + 404)
                target_idx = np.sort(
                    rng.choice(y.shape[1], size=args.max_targets_khigh, replace=False)
                )
                y_eval = y[:, target_idx]
                h_true_eval = h_true[target_idx]
            else:
                target_idx = np.arange(y.shape[1], dtype=np.int64)
                y_eval = y
                h_true_eval = h_true

            use_cv = (phi.shape[0] * phi.shape[1]) <= args.cv_complexity_limit
            h_hat = recover_hyperweights_korder(
                phi=phi,
                y=y_eval,
                seed=seed + 701,
                cv_complexity_limit=args.cv_complexity_limit,
                alpha_scale=args.alpha_scale_khigh,
            )
            threshold = args.support_threshold_k3 if k == 3 else args.support_threshold_k4
            met = support_metrics_hyper(h_true_eval, h_hat, threshold=threshold)
            runs.append(
                {
                    "n": n,
                    "k": k,
                    "t": t,
                    "sigma": sigma,
                    "seed": seed,
                    "num_features": int(len(combos)),
                    "evaluated_targets": int(target_idx.size),
                    "solver": "lasso_cv" if use_cv else "lasso_scaled",
                    "support_f1": float(met["f1"]),
                    "precision": float(met["precision"]),
                    "recall": float(met["recall"]),
                    "status": "ok",
                }
            )
        else:
            skipped.append(
                {
                    "n": n,
                    "k": k,
                    "t": t,
                    "sigma": sigma,
                    "seed": seed,
                    "reason": "unsupported interaction order (k<2)",
                }
            )

    report = {
        "config": {
            "n_values": n_values,
            "k_values": k_values,
            "t_values": t_values,
            "sigma_values": sigma_values,
            "seeds": seeds,
            "max_runs": args.max_runs,
            "max_features_khigh": args.max_features_khigh,
            "max_targets_khigh": args.max_targets_khigh,
            "cv_complexity_limit_k2": args.cv_complexity_limit_k2,
            "alpha_scale_k2": args.alpha_scale_k2,
            "cv_complexity_limit": args.cv_complexity_limit,
            "alpha_scale_khigh": args.alpha_scale_khigh,
        },
        "requested_total": len(requested),
        "executed": len(runs),
        "skipped": len(skipped),
        "runs": runs,
        "skipped_runs": skipped,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    print("Step 56 large-grid runner complete.")
    print(json.dumps({"requested_total": len(requested), "executed": len(runs), "skipped": len(skipped)}, indent=2))


if __name__ == "__main__":
    main()
