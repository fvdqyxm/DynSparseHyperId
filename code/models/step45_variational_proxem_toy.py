#!/usr/bin/env python3
"""Step 45: toy variational proximal-EM for switching sparse high-order dynamics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from phase0_baselines import forward_backward_hmm, sample_markov_chain
from static_hypergraph_k3 import build_pair_features, enumerate_pairs


def simulate_switching_k3(
    n: int,
    t: int,
    k: int,
    seed: int,
    sigma: float,
    edge_prob_pair: float,
    edge_prob_triplet: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    pairs = enumerate_pairs(n)
    p = len(pairs)

    w_true: list[np.ndarray] = []
    for _ in range(k):
        a = (rng.random((n, n)) < edge_prob_pair) * rng.uniform(-0.25, 0.25, size=(n, n))
        np.fill_diagonal(a, rng.uniform(0.05, 0.20, size=n))
        h = (rng.random((n, p)) < edge_prob_triplet) * rng.uniform(-0.12, 0.12, size=(n, p))
        w_true.append(np.hstack([a, h]))

    # Ensure nontrivial regime separation in toy data.
    if k == 2:
        for _ in range(200):
            diff_support = float(
                np.mean((np.abs(w_true[0]) > 1e-6) != (np.abs(w_true[1]) > 1e-6))
            )
            fro_ratio = float(
                np.linalg.norm(w_true[0] - w_true[1]) / max(np.linalg.norm(w_true[0]), 1e-12)
            )
            if diff_support >= 0.12 and fro_ratio >= 0.65:
                break
            a = (rng.random((n, n)) < edge_prob_pair) * rng.uniform(-0.25, 0.25, size=(n, n))
            np.fill_diagonal(a, rng.uniform(0.05, 0.20, size=n))
            h = (rng.random((n, p)) < edge_prob_triplet) * rng.uniform(-0.12, 0.12, size=(n, p))
            w_true[1] = np.hstack([a, h])

    transition = np.array([[0.96, 0.04], [0.04, 0.96]], dtype=np.float64)
    init = np.array([0.5, 0.5], dtype=np.float64)
    z = sample_markov_chain(t=t, transition=transition, init_probs=init, rng=rng)

    y = np.zeros((t, n), dtype=np.float64)
    y[0] = rng.normal(scale=0.6, size=n)
    for i in range(1, t):
        feat = np.hstack([y[i - 1], np.array([y[i - 1, a] * y[i - 1, b] for a, b in pairs])])
        pred = feat @ w_true[z[i]].T
        y[i] = pred + rng.normal(scale=sigma, size=n)

    x_prev = y[:-1]
    x_next = y[1:]
    phi = build_pair_features(x_prev, pairs)
    feats = np.hstack([x_prev, phi])
    return feats, x_next, z[1:], transition


def compute_log_emission_features(feats: np.ndarray, x_next: np.ndarray, w_list: list[np.ndarray], sigma2: float) -> np.ndarray:
    m = feats.shape[0]
    n = x_next.shape[1]
    k = len(w_list)
    sigma2 = max(sigma2, 1e-6)
    const = -0.5 * n * np.log(2.0 * np.pi * sigma2)
    out = np.zeros((m, k), dtype=np.float64)
    for r in range(k):
        residual = x_next - feats @ w_list[r].T
        out[:, r] = const - 0.5 * np.sum(residual**2, axis=1) / sigma2
    return out


def weighted_ridge(feats: np.ndarray, x_next: np.ndarray, weights: np.ndarray, ridge: float) -> np.ndarray:
    d = feats.shape[1]
    sw = np.sqrt(np.clip(weights, 1e-8, None))
    xw = feats * sw[:, None]
    yw = x_next * sw[:, None]
    xtx = xw.T @ xw + ridge * np.eye(d)
    xty = xw.T @ yw
    beta = np.linalg.solve(xtx, xty)
    return beta.T


def prox_group_l2_rows(h: np.ndarray, lam: float) -> np.ndarray:
    out = h.copy()
    for j in range(h.shape[1]):
        v = out[:, j]
        norm = float(np.linalg.norm(v))
        if norm <= lam:
            out[:, j] = 0.0
        else:
            out[:, j] = (1.0 - lam / norm) * v
    return out


def objective_value(
    feats: np.ndarray,
    x_next: np.ndarray,
    gamma: np.ndarray,
    w_list: list[np.ndarray],
    sigma2: float,
    lambda_group: float,
    n: int,
) -> float:
    k = len(w_list)
    mse = 0.0
    for r in range(k):
        residual = x_next - feats @ w_list[r].T
        mse += float(np.sum(gamma[:, r][:, None] * (residual**2)))

    penalty = 0.0
    for r in range(k):
        h = w_list[r][:, n:]
        penalty += float(np.sum(np.linalg.norm(h, axis=0)))

    return 0.5 * mse / max(sigma2, 1e-6) + lambda_group * penalty


def run_toy_proxem(
    n: int,
    t: int,
    k: int,
    seed: int,
    sigma: float,
    em_iters: int,
    ridge: float,
    lambda_group: float,
    restarts: int,
) -> dict:
    feats, x_next, z_true, transition_true = simulate_switching_k3(
        n=n,
        t=t,
        k=k,
        seed=seed,
        sigma=sigma,
        edge_prob_pair=0.12,
        edge_prob_triplet=0.10,
    )

    d = feats.shape[1]
    best: dict | None = None

    for restart in range(restarts):
        rng = np.random.default_rng(seed + 77 + 1001 * restart)
        w_list = [rng.normal(scale=0.05, size=(n, d)) for _ in range(k)]
        transition = np.array([[0.90, 0.10], [0.10, 0.90]], dtype=np.float64)
        init = np.array([0.5, 0.5], dtype=np.float64)
        sigma2 = sigma**2

        obj_hist: list[float] = []
        ll_hist: list[float] = []

        for _ in range(em_iters):
            log_emission = compute_log_emission_features(feats, x_next, w_list, sigma2)
            gamma, xi_sum, ll = forward_backward_hmm(log_emission, transition, init)

            init = gamma[0] + 1e-6
            init /= init.sum()
            transition = xi_sum + 1e-3
            transition /= transition.sum(axis=1, keepdims=True)

            new_w_list: list[np.ndarray] = []
            for r in range(k):
                w_r = weighted_ridge(feats, x_next, gamma[:, r], ridge=ridge)
                a_r = w_r[:, :n]
                h_r = w_r[:, n:]
                h_r = prox_group_l2_rows(h_r, lam=lambda_group)
                new_w_list.append(np.hstack([a_r, h_r]))

            w_list = new_w_list

            weighted_sq = 0.0
            for r in range(k):
                residual = x_next - feats @ w_list[r].T
                weighted_sq += float(np.sum(gamma[:, r][:, None] * (residual**2)))
            sigma2 = max(weighted_sq / (x_next.shape[0] * n), 1e-6)

            obj = objective_value(
                feats=feats,
                x_next=x_next,
                gamma=gamma,
                w_list=w_list,
                sigma2=sigma2,
                lambda_group=lambda_group,
                n=n,
            )
            obj_hist.append(float(obj))
            ll_hist.append(float(ll))

        log_emission = compute_log_emission_features(feats, x_next, w_list, sigma2)
        gamma, _, _ = forward_backward_hmm(log_emission, transition, init)
        z_hat = np.argmax(gamma, axis=1).astype(np.int64)

        acc0 = float(np.mean(z_hat == z_true))
        acc1 = float(np.mean((1 - z_hat) == z_true))
        regime_acc = max(acc0, acc1)

        ll_monotone_steps = int(np.sum(np.diff(ll_hist) >= -1e-8))
        ll_monotone_frac = float(ll_monotone_steps / max(len(ll_hist) - 1, 1))

        candidate = {
            "objective_history": obj_hist,
            "loglik_history": ll_hist,
            "loglik_monotone_fraction": ll_monotone_frac,
            "final_regime_accuracy": regime_acc,
            "sigma2_final": float(sigma2),
            "transition_est": transition.tolist(),
            "restart": restart,
        }
        if best is None or candidate["loglik_history"][-1] > best["loglik_history"][-1]:
            best = candidate

    assert best is not None
    return {
        "config": {
            "n": n,
            "t": t,
            "k": k,
            "seed": seed,
            "sigma": sigma,
            "em_iters": em_iters,
            "ridge": ridge,
            "lambda_group": lambda_group,
            "restarts": restarts,
        },
        "objective_history": best["objective_history"],
        "loglik_history": best["loglik_history"],
        "loglik_monotone_fraction": best["loglik_monotone_fraction"],
        "final_regime_accuracy": best["final_regime_accuracy"],
        "sigma2_final": best["sigma2_final"],
        "best_restart": best["restart"],
        "transition_true": transition_true.tolist(),
        "transition_est": best["transition_est"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase1_step45_proxem"))
    parser.add_argument("--n", type=int, default=8)
    parser.add_argument("--t", type=int, default=1200)
    parser.add_argument("--k", type=int, default=2)
    parser.add_argument("--seed", type=int, default=301)
    parser.add_argument("--sigma", type=float, default=0.4)
    parser.add_argument("--em-iters", type=int, default=18)
    parser.add_argument("--ridge", type=float, default=1e-2)
    parser.add_argument("--lambda-group", type=float, default=0.06)
    parser.add_argument("--restarts", type=int, default=4)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    report = run_toy_proxem(
        n=args.n,
        t=args.t,
        k=args.k,
        seed=args.seed,
        sigma=args.sigma,
        em_iters=args.em_iters,
        ridge=args.ridge,
        lambda_group=args.lambda_group,
        restarts=args.restarts,
    )

    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    x = np.arange(1, len(report["objective_history"]) + 1)
    fig, ax1 = plt.subplots(1, 1, figsize=(7, 4))
    ax1.plot(x, report["objective_history"], marker="o", label="Penalized surrogate")
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Objective")
    ax1.grid(alpha=0.3)
    ax1.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "objective_history.png", dpi=170)
    plt.close(fig)

    fig2, ax2 = plt.subplots(1, 1, figsize=(7, 4))
    ax2.plot(x, report["loglik_history"], marker="s", color="tab:orange", label="Expected log-likelihood")
    ax2.set_xlabel("Iteration")
    ax2.set_ylabel("Log-likelihood")
    ax2.grid(alpha=0.3)
    ax2.legend(loc="best")
    fig2.tight_layout()
    fig2.savefig(out_dir / "loglik_history.png", dpi=170)
    plt.close(fig2)

    print("Step 45 toy variational prox-EM complete.")
    print(
        json.dumps(
            {
                "loglik_monotone_fraction": report["loglik_monotone_fraction"],
                "final_regime_accuracy": report["final_regime_accuracy"],
                "best_restart": report["best_restart"],
                "sigma2_final": report["sigma2_final"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
