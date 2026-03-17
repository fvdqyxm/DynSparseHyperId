#!/usr/bin/env python3
"""Step 56 supplement: switching-LDS grid with explicit K sweep (K=3..5)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from phase0_baselines import (
    evaluate_switching_solution,
    make_sparse_stable_A,
    recover_switching_lds_soft,
    sample_markov_chain,
    simulate_switching_lds,
)


def parse_int_list(text: str) -> list[int]:
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def parse_float_list(text: str) -> list[float]:
    return [float(x.strip()) for x in text.split(",") if x.strip()]


def build_separated_regime_mats(
    *,
    n: int,
    k: int,
    edge_prob: float,
    threshold: float,
    rng: np.random.Generator,
    min_support_diff: float,
    min_fro_ratio: float,
) -> list[np.ndarray]:
    mats: list[np.ndarray] = []
    attempts = 0
    while len(mats) < k:
        attempts += 1
        if attempts > 8000:
            raise RuntimeError("Failed to build separated regime matrices under constraints.")
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
        ok = True
        for prev in mats:
            supp_diff = float(
                np.mean((np.abs(prev) > threshold) != (np.abs(cand) > threshold))
            )
            fro_ratio = float(np.linalg.norm(prev - cand) / max(np.linalg.norm(prev), 1e-12))
            if supp_diff < min_support_diff or fro_ratio < min_fro_ratio:
                ok = False
                break
        if ok:
            mats.append(cand)
    return mats


def make_transition(k: int, stay_prob: float, rng: np.random.Generator) -> np.ndarray:
    if k < 2:
        raise ValueError("k must be >=2")
    stay_prob = float(np.clip(stay_prob, 0.6, 0.995))
    base = np.full((k, k), (1.0 - stay_prob) / (k - 1), dtype=np.float64)
    np.fill_diagonal(base, stay_prob)
    # Small stochastic row perturbation to avoid an overly symmetric chain.
    jitter = rng.uniform(0.0, 0.01, size=(k, k))
    out = base + jitter
    out /= out.sum(axis=1, keepdims=True)
    return out


def run_one(
    *,
    n: int,
    t: int,
    k: int,
    sigma: float,
    obs_noise_sigma: float,
    edge_prob: float,
    support_threshold: float,
    seed: int,
    em_iterations: int,
    restarts: int,
) -> dict:
    rng = np.random.default_rng(seed)
    a_true = build_separated_regime_mats(
        n=n,
        k=k,
        edge_prob=edge_prob,
        threshold=support_threshold,
        rng=rng,
        min_support_diff=0.15,
        min_fro_ratio=0.60,
    )
    transition_true = make_transition(k=k, stay_prob=0.93, rng=rng)
    init = np.full(k, 1.0 / k, dtype=np.float64)
    z = sample_markov_chain(t=t, transition=transition_true, init_probs=init, rng=rng)
    x_clean = simulate_switching_lds(a_list=a_true, z=z, sigma=sigma, rng=rng)
    x_obs = x_clean + rng.normal(scale=obs_noise_sigma, size=x_clean.shape)

    a_hat, z_hat, transition_hat, sigma2_hat, loglik, init_strategy = recover_switching_lds_soft(
        x=x_obs,
        k=k,
        seed=seed + 101,
        em_iterations=em_iterations,
        restarts=restarts,
        ridge_lambda=1e-2,
        lasso_alpha=0.03,
        sticky_kappa=2.0,
        temp_start=2.2,
    )
    eval_soft = evaluate_switching_solution(
        a_true=a_true,
        a_hat=a_hat,
        z_true_transitions=z[1:],
        z_hat_transitions=z_hat,
        support_threshold=support_threshold,
    )
    return {
        "n": n,
        "t": t,
        "k": k,
        "sigma": sigma,
        "obs_noise_sigma": obs_noise_sigma,
        "seed": seed,
        "init_strategy": init_strategy,
        "regime_accuracy": float(eval_soft["acc"]),
        "support_f1_mean": float(eval_soft["mean_f1"]),
        "support_f1_per_regime": [float(v) for v in eval_soft["f1s"]],
        "sigma2_hat": float(sigma2_hat),
        "loglik": float(loglik),
        "status": "ok",
    }


def summarize(runs: list[dict]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    groups: dict[str, list[dict]] = {}
    for r in runs:
        key = f"k{r['k']}_t{r['t']}_obs{r['obs_noise_sigma']:.2f}"
        groups.setdefault(key, []).append(r)
    for key, vals in groups.items():
        acc = [v["regime_accuracy"] for v in vals]
        f1 = [v["support_f1_mean"] for v in vals]
        out[key] = {
            "runs": float(len(vals)),
            "regime_accuracy_mean": float(np.mean(acc)),
            "regime_accuracy_std": float(np.std(acc, ddof=0)),
            "support_f1_mean": float(np.mean(f1)),
            "support_f1_std": float(np.std(f1, ddof=0)),
            "gate_acc_ge_0p75_fraction": float(np.mean(np.array(acc) >= 0.75)),
            "gate_f1_ge_0p75_fraction": float(np.mean(np.array(f1) >= 0.75)),
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/phase2_step56_switching_k_grid"),
    )
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--k-values", type=str, default="3,4,5")
    parser.add_argument("--t-values", type=str, default="500,2000,5000")
    parser.add_argument("--sigma-values", type=str, default="0.1")
    parser.add_argument("--obs-noise-values", type=str, default="0.1,1.0")
    parser.add_argument("--edge-prob", type=float, default=0.12)
    parser.add_argument("--support-threshold", type=float, default=0.05)
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--seed-start", type=int, default=2401)
    parser.add_argument("--em-iterations", type=int, default=18)
    parser.add_argument("--restarts", type=int, default=4)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    k_values = parse_int_list(args.k_values)
    t_values = parse_int_list(args.t_values)
    sigma_values = parse_float_list(args.sigma_values)
    obs_noise_values = parse_float_list(args.obs_noise_values)
    seeds = [args.seed_start + i for i in range(args.seeds)]

    requested = []
    for k in k_values:
        for t in t_values:
            for sigma in sigma_values:
                for obs_noise in obs_noise_values:
                    for seed in seeds:
                        requested.append((k, t, sigma, obs_noise, seed))

    runs: list[dict] = []
    failures: list[dict] = []
    for k, t, sigma, obs_noise, seed in requested:
        try:
            r = run_one(
                n=args.n,
                t=t,
                k=k,
                sigma=sigma,
                obs_noise_sigma=obs_noise,
                edge_prob=args.edge_prob,
                support_threshold=args.support_threshold,
                seed=seed,
                em_iterations=args.em_iterations,
                restarts=args.restarts,
            )
            runs.append(r)
        except Exception as exc:  # pragma: no cover - defensive batch resilience
            failures.append(
                {
                    "k": k,
                    "t": t,
                    "sigma": sigma,
                    "obs_noise_sigma": obs_noise,
                    "seed": seed,
                    "status": "error",
                    "error": repr(exc),
                }
            )

    summary = summarize(runs)
    report = {
        "config": {
            "n": args.n,
            "k_values": k_values,
            "t_values": t_values,
            "sigma_values": sigma_values,
            "obs_noise_values": obs_noise_values,
            "edge_prob": args.edge_prob,
            "support_threshold": args.support_threshold,
            "seeds": seeds,
            "em_iterations": args.em_iterations,
            "restarts": args.restarts,
        },
        "requested_total": len(requested),
        "executed": len(runs),
        "failed": len(failures),
        "runs": runs,
        "summary": summary,
        "failures": failures,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    print("Step 56 switching-K grid complete.")
    print(json.dumps({"requested_total": len(requested), "executed": len(runs), "failed": len(failures)}, indent=2))


if __name__ == "__main__":
    main()
