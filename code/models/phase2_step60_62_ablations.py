#!/usr/bin/env python3
"""Steps 60-62: sparsity, regime, and high-order ablations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from phase0_baselines import (
    evaluate_switching_solution,
    fit_A_ridge,
    make_sparse_stable_A,
    recover_switching_lds_hard,
    sample_markov_chain,
    simulate_switching_lds,
)
from static_hypergraph_korder import (
    recover_hyperweights_korder,
    simulate_static_korder_regression,
    support_metrics_hyper,
)


def _train_val_split(x: np.ndarray, y: np.ndarray, frac: float = 0.8) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = x.shape[0]
    split = max(int(frac * n), 2)
    return x[:split], y[:split], x[split:], y[split:]


def _dense_fit(phi: np.ndarray, y: np.ndarray, ridge: float = 1e-6) -> np.ndarray:
    xtx = phi.T @ phi + ridge * np.eye(phi.shape[1])
    xty = phi.T @ y
    coef = np.linalg.solve(xtx, xty)
    return coef.T


def run_sparsity_ablation(seed: int) -> dict:
    rows = []
    for k in (3, 4):
        _, phi, y, h_true, _ = simulate_static_korder_regression(
            n=20,
            t=1400,
            k=k,
            edge_prob=0.10,
            noise_sigma=0.35,
            seed=seed + 17 * k,
            max_features=1000,
        )
        phi_tr, y_tr, phi_te, y_te = _train_val_split(phi, y, frac=0.8)

        h_sparse = recover_hyperweights_korder(
            phi=phi_tr,
            y=y_tr,
            seed=seed + 100 * k,
            cv_complexity_limit=50_000,
            alpha_scale=0.35,
        )
        h_dense = _dense_fit(phi_tr, y_tr)

        m_sparse = support_metrics_hyper(h_true, h_sparse, threshold=0.08)
        m_dense = support_metrics_hyper(h_true, h_dense, threshold=0.08)

        pred_sparse = phi_te @ h_sparse.T
        pred_dense = phi_te @ h_dense.T
        mse_sparse = float(np.mean((pred_sparse - y_te) ** 2))
        mse_dense = float(np.mean((pred_dense - y_te) ** 2))

        rows.append(
            {
                "k": k,
                "sparse_support_f1": float(m_sparse["f1"]),
                "dense_support_f1": float(m_dense["f1"]),
                "sparse_val_mse": mse_sparse,
                "dense_val_mse": mse_dense,
                "mse_gain_dense_minus_sparse": float(mse_dense - mse_sparse),
            }
        )
    return {"rows": rows}


def run_regime_ablation(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n = 10
    t = 1400
    k = 2
    edge_prob = 0.1
    sigma = 0.5

    a0 = make_sparse_stable_A(n=n, edge_prob=edge_prob, rng=rng, scale=0.35, target_radius=0.85)
    a1 = make_sparse_stable_A(n=n, edge_prob=edge_prob, rng=rng, scale=0.35, target_radius=0.85)
    transition = np.array([[0.97, 0.03], [0.03, 0.97]], dtype=np.float64)
    init = np.array([0.5, 0.5], dtype=np.float64)

    burn_in = 200
    z_full = sample_markov_chain(t=t + burn_in, transition=transition, init_probs=init, rng=rng)
    x_full = simulate_switching_lds(a_list=[a0, a1], z=z_full, sigma=sigma, rng=rng)
    z_true = z_full[burn_in:]
    x = x_full[burn_in:]

    obs_noise = 0.15
    y = x + rng.normal(scale=obs_noise, size=x.shape)
    x_prev = y[:-1]
    x_next = y[1:]
    z_true_transitions = z_true[1:]

    # Regime-aware baseline.
    a_switch, z_hat, _, _, _ = recover_switching_lds_hard(
        x=y,
        k=k,
        seed=seed + 77,
        em_iterations=14,
        lasso_alpha=0.01,
    )
    ev = evaluate_switching_solution(
        a_true=[a0, a1],
        a_hat=a_switch,
        z_true_transitions=z_true_transitions,
        z_hat_transitions=z_hat,
        support_threshold=0.05,
    )
    perm = ev["perm"]
    a_switch_mapped = [a_switch[perm.index(r)] for r in range(k)]
    z_mapped = ev["mapped_labels"]
    pred_switch = np.zeros_like(x_next)
    for i in range(x_prev.shape[0]):
        pred_switch[i] = x_prev[i] @ a_switch_mapped[z_mapped[i]].T
    mse_switch = float(np.mean((x_next - pred_switch) ** 2))

    # Single-regime ablation.
    a_single = fit_A_ridge(x_prev=x_prev, x_next=x_next, ridge_lambda=1e-2)
    pred_single = x_prev @ a_single.T
    mse_single = float(np.mean((x_next - pred_single) ** 2))
    majority = max(np.mean(z_true_transitions == 0), np.mean(z_true_transitions == 1))

    return {
        "switching_regime_accuracy": float(ev["acc"]),
        "single_regime_accuracy_proxy": float(majority),
        "switching_state_mse": mse_switch,
        "single_state_mse": mse_single,
        "state_mse_gain_single_minus_switching": float(mse_single - mse_switch),
        "switching_support_f1_mean": float(ev["mean_f1"]),
    }


def run_highorder_ablation(seed: int) -> dict:
    rows = []
    for k in (3, 4):
        x, phi, y, _, _ = simulate_static_korder_regression(
            n=20,
            t=1400,
            k=k,
            edge_prob=0.1,
            noise_sigma=0.35,
            seed=seed + 31 * k,
            max_features=1000,
        )
        phi_tr, y_tr, phi_te, y_te = _train_val_split(phi, y, frac=0.8)
        x_tr, _, x_te, _ = _train_val_split(x, y, frac=0.8)

        h_hat = recover_hyperweights_korder(
            phi=phi_tr,
            y=y_tr,
            seed=seed + 211 * k,
            cv_complexity_limit=50_000,
            alpha_scale=0.35,
        )
        # Pairwise-only baseline: linear mapping y_t from x_t (no higher-order terms).
        b_pair = _dense_fit(x_tr, y_tr)

        pred_high = phi_te @ h_hat.T
        pred_pair = x_te @ b_pair.T
        mse_high = float(np.mean((pred_high - y_te) ** 2))
        mse_pair = float(np.mean((pred_pair - y_te) ** 2))

        rows.append(
            {
                "k_true": k,
                "highorder_val_mse": mse_high,
                "pairwise_only_val_mse": mse_pair,
                "mse_gain_pair_minus_highorder": float(mse_pair - mse_high),
            }
        )
    return {"rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step60_62_ablations"))
    parser.add_argument("--seed", type=int, default=1701)
    args = parser.parse_args()

    sparsity = run_sparsity_ablation(seed=args.seed)
    regime = run_regime_ablation(seed=args.seed + 100)
    highorder = run_highorder_ablation(seed=args.seed + 200)

    report = {
        "seed": args.seed,
        "step60_sparsity_ablation": sparsity,
        "step61_regime_ablation": regime,
        "step62_highorder_ablation": highorder,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"step60_rows": len(sparsity["rows"]), "step62_rows": len(highorder["rows"])}, indent=2))


if __name__ == "__main__":
    main()
