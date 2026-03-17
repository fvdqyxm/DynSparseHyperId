#!/usr/bin/env python3
"""Phase 0 Step 20: static k=3 toy hypergraph reconstruction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
from numpy.typing import NDArray
from sklearn.linear_model import Lasso, LassoCV

# Force headless-safe backend.
matplotlib.use("Agg")
import matplotlib.pyplot as plt


Array = NDArray[np.float64]


def enumerate_pairs(n: int) -> list[tuple[int, int]]:
    return [(j, k) for j in range(n) for k in range(j + 1, n)]


def sample_sparse_hyperweights(
    n: int,
    pairs: list[tuple[int, int]],
    edge_prob: float,
    rng: np.random.Generator,
    min_abs: float = 0.05,
    max_abs: float = 0.25,
) -> Array:
    p = len(pairs)
    h = np.zeros((n, p), dtype=np.float64)
    for target in range(n):
        mask = rng.random(p) < edge_prob
        signs = rng.choice(np.array([-1.0, 1.0]), size=p)
        mags = rng.uniform(min_abs, max_abs, size=p)
        h[target] = mask * signs * mags
    return h


def build_pair_features(x: Array, pairs: list[tuple[int, int]]) -> Array:
    phi = np.empty((x.shape[0], len(pairs)), dtype=np.float64)
    for idx, (j, k) in enumerate(pairs):
        phi[:, idx] = x[:, j] * x[:, k]
    return phi


def simulate_static_k3_regression(
    n: int,
    t: int,
    edge_prob: float,
    noise_sigma: float,
    seed: int,
) -> tuple[Array, Array, Array, Array, list[tuple[int, int]]]:
    rng = np.random.default_rng(seed)
    pairs = enumerate_pairs(n)
    h_true = sample_sparse_hyperweights(n=n, pairs=pairs, edge_prob=edge_prob, rng=rng)

    x = rng.normal(loc=0.0, scale=1.0, size=(t, n))
    phi = build_pair_features(x, pairs)
    y = phi @ h_true.T + rng.normal(scale=noise_sigma, size=(t, n))
    return x, phi, y, h_true, pairs


def recover_hyperweights(phi: Array, y: Array, seed: int) -> Array:
    n = y.shape[1]
    p = phi.shape[1]
    h_hat = np.zeros((n, p), dtype=np.float64)

    for target in range(n):
        reg = LassoCV(
            cv=5,
            fit_intercept=False,
            random_state=seed + target,
            max_iter=20000,
            alphas=100,
        )
        reg.fit(phi, y[:, target])

        mse_mean = np.mean(reg.mse_path_, axis=1)
        mse_std = np.std(reg.mse_path_, axis=1, ddof=1) / np.sqrt(reg.mse_path_.shape[1])
        idx_min = int(np.argmin(mse_mean))
        mse_1se = mse_mean[idx_min] + mse_std[idx_min]
        candidate = np.where(mse_mean <= mse_1se)[0]
        idx_1se = int(np.min(candidate))
        alpha_1se = float(reg.alphas_[idx_1se])
        alpha_min = float(reg.alpha_)
        alpha_mid = float(np.sqrt(alpha_min * alpha_1se))

        sparse = Lasso(alpha=alpha_mid, fit_intercept=False, max_iter=20000)
        sparse.fit(phi, y[:, target])
        h_hat[target] = sparse.coef_

    return h_hat


def support_metrics_hyper(true_h: Array, est_h: Array, threshold: float) -> dict[str, float | int]:
    true_mask = np.abs(true_h) > 1e-9
    pred_mask = np.abs(est_h) >= threshold

    tp = int(np.sum(true_mask & pred_mask))
    fp = int(np.sum(~true_mask & pred_mask))
    fn = int(np.sum(true_mask & ~pred_mask))
    tn = int(np.sum(~true_mask & ~pred_mask))

    precision = float(tp / (tp + fp + 1e-12))
    recall = float(tp / (tp + fn + 1e-12))
    f1 = float(2.0 * precision * recall / (precision + recall + 1e-12))

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def noise_sweep(
    n: int,
    t: int,
    edge_prob: float,
    threshold: float,
    seed_start: int,
    seeds: int,
    noise_levels: list[float],
) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for noise in noise_levels:
        f1s: list[float] = []
        precisions: list[float] = []
        recalls: list[float] = []
        for offset in range(seeds):
            seed = seed_start + offset
            _, phi, y, h_true, _ = simulate_static_k3_regression(
                n=n,
                t=t,
                edge_prob=edge_prob,
                noise_sigma=noise,
                seed=seed,
            )
            h_hat = recover_hyperweights(phi=phi, y=y, seed=seed + 500)
            m = support_metrics_hyper(h_true, h_hat, threshold=threshold)
            f1s.append(float(m["f1"]))
            precisions.append(float(m["precision"]))
            recalls.append(float(m["recall"]))

        key = f"{noise:.2f}"
        summary[key] = {
            "runs": float(seeds),
            "f1_mean": float(np.mean(f1s)),
            "f1_std": float(np.std(f1s, ddof=0)),
            "precision_mean": float(np.mean(precisions)),
            "recall_mean": float(np.mean(recalls)),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase0_hypergraph_k3"))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--t", type=int, default=700)
    parser.add_argument("--edge-prob", type=float, default=0.12)
    parser.add_argument("--noise-sigma", type=float, default=0.25)
    parser.add_argument("--support-threshold", type=float, default=0.08)
    parser.add_argument("--sweep-noises", type=str, default="0.15,0.25,0.35,0.50")
    parser.add_argument("--sweep-seeds", type=int, default=3)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    x, phi, y, h_true, pairs = simulate_static_k3_regression(
        n=args.n,
        t=args.t,
        edge_prob=args.edge_prob,
        noise_sigma=args.noise_sigma,
        seed=args.seed,
    )

    h_hat = recover_hyperweights(phi=phi, y=y, seed=args.seed + 300)
    metrics = support_metrics_hyper(true_h=h_true, est_h=h_hat, threshold=args.support_threshold)

    noise_levels = [float(v.strip()) for v in args.sweep_noises.split(",") if v.strip()]
    sweep = noise_sweep(
        n=args.n,
        t=args.t,
        edge_prob=args.edge_prob,
        threshold=args.support_threshold,
        seed_start=args.seed + 1000,
        seeds=args.sweep_seeds,
        noise_levels=noise_levels,
    )

    np.save(args.out_dir / "X_inputs.npy", x)
    np.save(args.out_dir / "Y_targets.npy", y)
    np.save(args.out_dir / "H_true.npy", h_true)
    np.save(args.out_dir / "H_hat.npy", h_hat)
    (args.out_dir / "pair_index.json").write_text(json.dumps(pairs))

    report = {
        "seed": args.seed,
        "n": args.n,
        "t": args.t,
        "edge_prob": args.edge_prob,
        "noise_sigma": args.noise_sigma,
        "support_threshold": args.support_threshold,
        "single_run_support": metrics,
        "noise_sweep": sweep,
    }
    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    vmax = max(np.max(np.abs(h_true)), np.max(np.abs(h_hat)))
    axes[0].imshow(h_true, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    axes[0].set_title("True k=3 Weights (target x pair)")
    axes[0].set_xlabel("Pair Feature")
    axes[0].set_ylabel("Target Node")
    axes[1].imshow(h_hat, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    axes[1].set_title("Recovered k=3 Weights")
    axes[1].set_xlabel("Pair Feature")
    axes[1].set_ylabel("Target Node")
    fig.tight_layout()
    fig.savefig(args.out_dir / "hyperweight_recovery_heatmap.png", dpi=160)
    plt.close(fig)

    xs = [float(k) for k in sweep.keys()]
    ys = [float(sweep[f"{xv:.2f}"]["f1_mean"]) for xv in xs]
    fig2, ax2 = plt.subplots(1, 1, figsize=(6, 4))
    ax2.plot(xs, ys, marker="o")
    ax2.set_xlabel("Noise Sigma")
    ax2.set_ylabel("Support F1 Mean")
    ax2.set_title("k=3 Hypergraph Recovery vs Noise")
    ax2.grid(alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(args.out_dir / "noise_sweep_f1.png", dpi=160)
    plt.close(fig2)

    print("Static k=3 hypergraph reconstruction complete.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
