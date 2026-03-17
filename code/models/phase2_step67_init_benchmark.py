#!/usr/bin/env python3
"""Step 67 extension: benchmark switching initialization strategies directly."""

from __future__ import annotations

import argparse
import json
from itertools import permutations
from pathlib import Path

import numpy as np

from phase0_baselines import _init_labels_strategy, make_sparse_stable_A, sample_markov_chain, simulate_switching_lds


def make_transition(k: int, stay_prob: float, rng: np.random.Generator) -> np.ndarray:
    base = np.full((k, k), (1.0 - stay_prob) / (k - 1), dtype=np.float64)
    np.fill_diagonal(base, stay_prob)
    out = base + rng.uniform(0.0, 0.01, size=(k, k))
    out /= out.sum(axis=1, keepdims=True)
    return out


def build_regimes(
    *,
    n: int,
    k: int,
    edge_prob: float,
    support_threshold: float,
    rng: np.random.Generator,
) -> list[np.ndarray]:
    mats: list[np.ndarray] = []
    while len(mats) < k:
        cand = make_sparse_stable_A(
            n=n,
            edge_prob=edge_prob,
            rng=rng,
            scale=0.35,
            target_radius=0.85,
        )
        if not mats:
            mats.append(cand)
            continue
        if all(
            float(np.mean((np.abs(prev) > support_threshold) != (np.abs(cand) > support_threshold))) >= 0.18
            for prev in mats
        ):
            mats.append(cand)
    return mats


def best_label_accuracy(y_true: np.ndarray, y_pred: np.ndarray, k: int) -> float:
    best = 0.0
    for perm in permutations(range(k)):
        mapping = {est: true for est, true in enumerate(perm)}
        mapped = np.array([mapping[x] for x in y_pred], dtype=np.int64)
        best = max(best, float(np.mean(mapped == y_true)))
    return best


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step67_init_benchmark"))
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--t", type=int, default=1200)
    parser.add_argument("--sigma", type=float, default=0.1)
    parser.add_argument("--obs-noise", type=float, default=0.2)
    parser.add_argument("--edge-prob", type=float, default=0.12)
    parser.add_argument("--support-threshold", type=float, default=0.05)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=6101)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    strategies = [
        "kmeans_full",
        "kmeans_delta",
        "residual_split",
        "window_ar_cluster",
        "local_ar_gmm",
        "local_ar_gmm_sticky",
        "residual_gmm_sticky",
        "random_blocks",
        "random",
    ]

    rows: list[dict] = []
    for offset in range(args.seeds):
        seed = args.seed_start + offset
        rng = np.random.default_rng(seed)
        regimes = build_regimes(
            n=args.n,
            k=args.k,
            edge_prob=args.edge_prob,
            support_threshold=args.support_threshold,
            rng=rng,
        )
        trans = make_transition(args.k, stay_prob=0.94, rng=rng)
        z = sample_markov_chain(
            t=args.t,
            transition=trans,
            init_probs=np.full(args.k, 1.0 / args.k, dtype=np.float64),
            rng=rng,
        )
        x = simulate_switching_lds(a_list=regimes, z=z, sigma=args.sigma, rng=rng)
        x_obs = x + rng.normal(scale=args.obs_noise, size=x.shape)
        x_prev = x_obs[:-1]
        x_next = x_obs[1:]
        z_target = z[1:]

        for strat in strategies:
            labels = _init_labels_strategy(
                x_prev=x_prev,
                x_next=x_next,
                k=args.k,
                strategy=strat,
                seed=seed + 91,
            )
            acc = best_label_accuracy(y_true=z_target, y_pred=labels, k=args.k)
            rows.append(
                {
                    "seed": seed,
                    "strategy": strat,
                    "regime_accuracy": acc,
                }
            )

    summary: dict[str, dict] = {}
    for strat in strategies:
        vals = [r["regime_accuracy"] for r in rows if r["strategy"] == strat]
        mean_val = float(np.mean(vals))
        std_val = float(np.std(vals, ddof=0))
        summary[strat] = {
            "runs": len(vals),
            "regime_accuracy_mean": mean_val,
            "regime_accuracy_std": std_val,
            "robust_score_mean_minus_half_std": float(mean_val - 0.5 * std_val),
        }

    best_strat = max(summary.items(), key=lambda kv: kv[1]["regime_accuracy_mean"])[0]
    best_robust = max(summary.items(), key=lambda kv: kv[1]["robust_score_mean_minus_half_std"])[0]
    report = {
        "config": {
            "n": args.n,
            "k": args.k,
            "t": args.t,
            "sigma": args.sigma,
            "obs_noise": args.obs_noise,
            "seeds": [args.seed_start + i for i in range(args.seeds)],
            "strategies": strategies,
        },
        "runs": rows,
        "summary": summary,
        "best_strategy_by_mean_accuracy": best_strat,
        "best_strategy_by_robust_score": best_robust,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    print("Step 67 init benchmark complete.")
    print(json.dumps({"best_strategy_mean": best_strat, "best_strategy_robust": best_robust, "num_runs": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
