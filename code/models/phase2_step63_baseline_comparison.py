#!/usr/bin/env python3
"""Step 63: baseline comparison (pairwise, static hypergraph, SINDy-like)."""

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


def _train_val_split(x: np.ndarray, y: np.ndarray, frac: float = 0.8) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = x.shape[0]
    split = max(int(frac * n), 2)
    return x[:split], y[:split], x[split:], y[split:]


def _ridge_map(x: np.ndarray, y: np.ndarray, ridge: float = 1e-4) -> np.ndarray:
    xtx = x.T @ x + ridge * np.eye(x.shape[1])
    xty = x.T @ y
    coef = np.linalg.solve(xtx, xty)
    return coef.T


def _sindy_stlsq(phi: np.ndarray, y: np.ndarray, threshold: float = 0.03, iters: int = 4) -> np.ndarray:
    # Multi-target STLSQ baseline.
    coef = np.linalg.lstsq(phi, y, rcond=None)[0].T  # targets x features
    for _ in range(iters):
        small = np.abs(coef) < threshold
        coef[small] = 0.0
        for target in range(y.shape[1]):
            active = np.where(np.abs(coef[target]) > 0)[0]
            if active.size == 0:
                continue
            beta = np.linalg.lstsq(phi[:, active], y[:, target], rcond=None)[0]
            coef[target, :] = 0.0
            coef[target, active] = beta
    return coef


def compare_on_korder(seed: int, k: int) -> dict:
    x, phi, y, h_true, _ = simulate_static_korder_regression(
        n=20,
        t=1600,
        k=k,
        edge_prob=0.1,
        noise_sigma=0.35,
        seed=seed + 23 * k,
        max_features=1000,
    )
    x_tr, y_tr, x_te, y_te = _train_val_split(x, y)
    phi_tr, _, phi_te, _ = _train_val_split(phi, y)

    h_sparse = recover_hyperweights_korder(
        phi=phi_tr,
        y=y_tr,
        seed=seed + 211 * k,
        cv_complexity_limit=50_000,
        alpha_scale=0.35,
    )
    h_sindy = _sindy_stlsq(phi_tr, y_tr, threshold=0.03, iters=5)
    b_pair = _ridge_map(x_tr, y_tr, ridge=1e-3)

    pred_sparse = phi_te @ h_sparse.T
    pred_sindy = phi_te @ h_sindy.T
    pred_pair = x_te @ b_pair.T

    mse_sparse = float(np.mean((pred_sparse - y_te) ** 2))
    mse_sindy = float(np.mean((pred_sindy - y_te) ** 2))
    mse_pair = float(np.mean((pred_pair - y_te) ** 2))

    m_sparse = support_metrics_hyper(h_true, h_sparse, threshold=0.08)
    m_sindy = support_metrics_hyper(h_true, h_sindy, threshold=0.08)

    return {
        "k_true": k,
        "sparse_hyper_val_mse": mse_sparse,
        "sindy_val_mse": mse_sindy,
        "pairwise_only_val_mse": mse_pair,
        "sparse_hyper_support_f1": float(m_sparse["f1"]),
        "sindy_support_f1": float(m_sindy["f1"]),
        "mse_gain_pair_minus_sparse": float(mse_pair - mse_sparse),
        "mse_gain_sindy_minus_sparse": float(mse_sindy - mse_sparse),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step63_baselines"))
    parser.add_argument("--seed", type=int, default=1901)
    args = parser.parse_args()

    # Pairwise baseline benchmark (separate k=2 dynamics benchmark).
    pairwise = run_sparse_lds(
        n=30,
        t=1200,
        edge_prob=0.1,
        sigma=0.5,
        seed=args.seed,
        out_dir=args.out_dir / "pairwise_sparse_lds",
        support_threshold=0.05,
        cv_complexity_limit=50_000,
        alpha_scale=0.35,
    )

    k3 = compare_on_korder(seed=args.seed + 100, k=3)
    k4 = compare_on_korder(seed=args.seed + 200, k=4)

    report = {
        "seed": args.seed,
        "pairwise_sparse_lds": pairwise,
        "highorder_baseline_comparison": {
            "k3": k3,
            "k4": k4,
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"k3_mse_gain_pair_minus_sparse": k3["mse_gain_pair_minus_sparse"], "k4_mse_gain_pair_minus_sparse": k4["mse_gain_pair_minus_sparse"]}, indent=2))


if __name__ == "__main__":
    main()
