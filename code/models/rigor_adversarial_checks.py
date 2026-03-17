#!/usr/bin/env python3
"""Adversarial rigor checks to detect leakage/overclaiming artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from phase0_baselines import (
    evaluate_switching_solution,
    fit_sparse_As_from_labels,
    make_sparse_stable_A,
    recover_switching_lds_oracle,
    sample_markov_chain,
    simulate_switching_lds,
)
from static_hypergraph_k3 import (
    recover_hyperweights,
    simulate_static_k3_regression,
    support_metrics_hyper,
)


def run_k3_checks(seed: int) -> dict:
    n = 10
    t = 700
    edge_prob = 0.12
    noise_sigma = 0.25
    threshold = 0.08

    x, phi, y, h_true, _ = simulate_static_k3_regression(
        n=n,
        t=t,
        edge_prob=edge_prob,
        noise_sigma=noise_sigma,
        seed=seed,
    )

    # Baseline
    h_hat = recover_hyperweights(phi=phi, y=y, seed=seed + 300)
    baseline = support_metrics_hyper(true_h=h_true, est_h=h_hat, threshold=threshold)

    # Permutation control: break feature-target alignment.
    rng = np.random.default_rng(seed + 11)
    perm = rng.permutation(t)
    y_perm = y[perm]
    h_hat_perm = recover_hyperweights(phi=phi, y=y_perm, seed=seed + 301)
    perm_metrics = support_metrics_hyper(true_h=h_true, est_h=h_hat_perm, threshold=threshold)

    # Null control: zero true hyperedges.
    h_zero = np.zeros_like(h_true)
    rng_null = np.random.default_rng(seed + 23)
    y_null = rng_null.normal(scale=noise_sigma, size=y.shape)
    h_hat_null = recover_hyperweights(phi=phi, y=y_null, seed=seed + 302)
    null_metrics = support_metrics_hyper(true_h=h_zero, est_h=h_hat_null, threshold=threshold)
    null_fpr = float(null_metrics["fp"] / (null_metrics["fp"] + null_metrics["tn"] + 1e-12))

    # Reproducibility check.
    h_hat_rep = recover_hyperweights(phi=phi, y=y, seed=seed + 300)
    max_abs_delta = float(np.max(np.abs(h_hat - h_hat_rep)))

    checks = {
        "baseline_f1": float(baseline["f1"]),
        "permutation_f1": float(perm_metrics["f1"]),
        "null_fpr": null_fpr,
        "reproducibility_max_abs_delta": max_abs_delta,
    }
    verdicts = {
        "baseline_reasonable": checks["baseline_f1"] >= 0.75,
        "permutation_collapses": checks["permutation_f1"] <= 0.35,
        "null_fpr_bounded": checks["null_fpr"] <= 0.10,
        "deterministic_repeat": checks["reproducibility_max_abs_delta"] <= 1e-12,
    }

    return {
        "config": {
            "n": n,
            "t": t,
            "edge_prob": edge_prob,
            "noise_sigma": noise_sigma,
            "support_threshold": threshold,
        },
        "baseline": baseline,
        "permutation_control": perm_metrics,
        "null_control": {**null_metrics, "fpr": null_fpr},
        "checks": checks,
        "verdicts": verdicts,
    }


def run_switching_random_label_control(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n = 10
    t = 1400
    k = 2
    edge_prob = 0.1
    sigma = 0.5
    obs_noise_sigma = 0.15
    support_threshold = 0.05

    a0 = make_sparse_stable_A(
        n=n,
        edge_prob=edge_prob,
        rng=rng,
        scale=0.35,
        target_radius=0.85,
    )
    a1 = make_sparse_stable_A(
        n=n,
        edge_prob=edge_prob,
        rng=rng,
        scale=0.35,
        target_radius=0.85,
    )
    for _ in range(100):
        support_diff = float(
            np.mean((np.abs(a0) > support_threshold) != (np.abs(a1) > support_threshold))
        )
        fro_ratio = float(np.linalg.norm(a0 - a1) / max(np.linalg.norm(a0), 1e-12))
        if support_diff >= 0.18 and fro_ratio >= 0.70:
            break
        a1 = make_sparse_stable_A(
            n=n,
            edge_prob=edge_prob,
            rng=rng,
            scale=0.35,
            target_radius=0.85,
        )

    transition_true = np.array([[0.97, 0.03], [0.03, 0.97]], dtype=np.float64)
    init_true = np.array([0.5, 0.5], dtype=np.float64)
    burn_in = 200

    z_full = sample_markov_chain(t=t + burn_in, transition=transition_true, init_probs=init_true, rng=rng)
    x_full = simulate_switching_lds(a_list=[a0, a1], z=z_full, sigma=sigma, rng=rng)
    z_true = z_full[burn_in:]
    x = x_full[burn_in:]
    y = x + rng.normal(scale=obs_noise_sigma, size=x.shape)

    z_true_transitions = z_true[1:]
    x_prev = y[:-1]
    x_next = y[1:]

    # Oracle ceiling (uses true regime labels).
    oracle_a, oracle_labels, _, _ = recover_switching_lds_oracle(x=y, z_true=z_true, k=k, lasso_alpha=0.01)
    oracle_eval = evaluate_switching_solution(
        a_true=[a0, a1],
        a_hat=oracle_a,
        z_true_transitions=z_true_transitions,
        z_hat_transitions=oracle_labels,
        support_threshold=support_threshold,
    )

    # Random-label control.
    rng_rand = np.random.default_rng(seed + 191)
    random_labels = rng_rand.integers(low=0, high=k, size=z_true_transitions.shape[0], dtype=np.int64)
    random_a = fit_sparse_As_from_labels(
        x_prev=x_prev,
        x_next=x_next,
        labels=random_labels,
        k=k,
        lasso_alpha=0.01,
        seed=seed + 700,
    )
    random_eval = evaluate_switching_solution(
        a_true=[a0, a1],
        a_hat=random_a,
        z_true_transitions=z_true_transitions,
        z_hat_transitions=random_labels,
        support_threshold=support_threshold,
    )

    f1_gap = float(oracle_eval["mean_f1"] - random_eval["mean_f1"])
    acc_gap = float(oracle_eval["acc"] - random_eval["acc"])

    checks = {
        "oracle_f1": float(oracle_eval["mean_f1"]),
        "random_label_f1": float(random_eval["mean_f1"]),
        "oracle_regime_acc": float(oracle_eval["acc"]),
        "random_label_regime_acc": float(random_eval["acc"]),
        "f1_gap": f1_gap,
        "acc_gap": acc_gap,
    }
    verdicts = {
        "oracle_beats_random_f1": f1_gap >= 0.20,
        "oracle_beats_random_acc": acc_gap >= 0.20,
    }

    return {
        "config": {
            "n": n,
            "t": t,
            "k": k,
            "edge_prob": edge_prob,
            "sigma": sigma,
            "obs_noise_sigma": obs_noise_sigma,
            "support_threshold": support_threshold,
        },
        "checks": checks,
        "verdicts": verdicts,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--out-dir", type=Path, default=Path("results/rigor_checks"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    k3 = run_k3_checks(seed=args.seed)
    switching = run_switching_random_label_control(seed=args.seed + 100)

    all_verdicts = {
        **{f"k3_{k}": v for k, v in k3["verdicts"].items()},
        **{f"switching_{k}": v for k, v in switching["verdicts"].items()},
    }
    all_passed = bool(all(all_verdicts.values()))

    report = {
        "seed": args.seed,
        "k3": k3,
        "switching_random_label_control": switching,
        "guardrails": all_verdicts,
        "all_passed": all_passed,
    }

    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print("Rigor adversarial checks complete.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
