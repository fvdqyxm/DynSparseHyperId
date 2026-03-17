#!/usr/bin/env python3
"""Step 67 extension: baseline vs upgraded multi-regime recovery comparison."""

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
    support_req = float(min_support_diff)
    fro_req = float(min_fro_ratio)
    while len(mats) < k:
        attempts += 1
        if attempts in {1500, 3000, 5000}:
            # Relax constraints gradually to avoid dead loops in sparse settings.
            support_req *= 0.90
            fro_req *= 0.90
        if attempts > 7000:
            raise RuntimeError(
                f"Failed to sample separated regime matrices (support_req={support_req:.3f}, fro_req={fro_req:.3f})."
            )
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
            if supp_diff < support_req or fro_ratio < fro_req:
                ok = False
                break
        if ok:
            mats.append(cand)
    return mats


def make_transition(k: int, stay_prob: float, rng: np.random.Generator) -> np.ndarray:
    base = np.full((k, k), (1.0 - stay_prob) / (k - 1), dtype=np.float64)
    np.fill_diagonal(base, stay_prob)
    jitter = rng.uniform(0.0, 0.005, size=(k, k))
    out = base + jitter
    out /= out.sum(axis=1, keepdims=True)
    return out


def run_once(
    *,
    n: int,
    t: int,
    k: int,
    sigma: float,
    obs_noise_sigma: float,
    edge_prob: float,
    support_threshold: float,
    min_support_diff: float,
    min_fro_ratio: float,
    seed: int,
    upgraded: bool,
    baseline_em_iterations: int,
    baseline_restarts: int,
    upgraded_em_iterations: int,
    upgraded_restarts: int,
    upgraded_bootstrap_runs: int,
    upgraded_use_stability_refit: bool,
    baseline_selection_mode: str,
    upgraded_selection_mode: str,
    baseline_alpha_scales: list[float],
    upgraded_alpha_scales: list[float],
    min_support_nnz: int,
) -> dict:
    rng = np.random.default_rng(seed)
    a_true = build_separated_regime_mats(
        n=n,
        k=k,
        edge_prob=edge_prob,
        threshold=support_threshold,
        rng=rng,
        min_support_diff=min_support_diff,
        min_fro_ratio=min_fro_ratio,
    )
    trans_true = make_transition(k=k, stay_prob=0.94, rng=rng)
    init = np.full(k, 1.0 / k, dtype=np.float64)
    z = sample_markov_chain(t=t, transition=trans_true, init_probs=init, rng=rng)
    x = simulate_switching_lds(a_list=a_true, z=z, sigma=sigma, rng=rng)
    x_obs = x + rng.normal(scale=obs_noise_sigma, size=x.shape)

    if upgraded:
        init_strats = [
            "local_ar_gmm_sticky",
            "residual_gmm_sticky",
            "local_ar_gmm",
            "window_ar_cluster",
            "residual_split",
            "kmeans_delta",
            "kmeans_full",
            "random_blocks",
            "random",
        ]
        em_iterations = upgraded_em_iterations
        restarts = upgraded_restarts
        sticky_kappa = 4.0
        temp_start = 3.0
        use_stability_refit = upgraded_use_stability_refit
        selection_mode = upgraded_selection_mode
        alpha_scales = upgraded_alpha_scales
    else:
        init_strats = [
            "kmeans_full",
            "kmeans_delta",
            "residual_split",
            "window_ar_cluster",
            "random_blocks",
            "random",
        ]
        em_iterations = baseline_em_iterations
        restarts = baseline_restarts
        sticky_kappa = 2.0
        temp_start = 2.2
        use_stability_refit = False
        selection_mode = baseline_selection_mode
        alpha_scales = baseline_alpha_scales

    a_hat, z_hat, trans_hat, sigma2_hat, ll, init_strategy = recover_switching_lds_soft(
        x=x_obs,
        k=k,
        seed=seed + 111,
        em_iterations=em_iterations,
        restarts=restarts,
        ridge_lambda=1e-2,
        lasso_alpha=0.03,
        sticky_kappa=sticky_kappa,
        temp_start=temp_start,
        init_strategies=init_strats,
        sparse_cv_complexity_limit=1,
        sparse_alpha_scale=0.35,
        sparse_alpha_scales=alpha_scales,
        use_stability_refit=use_stability_refit,
        support_threshold=support_threshold,
        stability_bootstrap_runs=upgraded_bootstrap_runs,
        stability_subsample_frac=0.7,
        stability_freq_threshold=0.55,
        selection_mode=selection_mode,
        selection_penalty=1.0,
        selection_gamma=0.5,
        min_support_nnz=min_support_nnz,
    )
    ev = evaluate_switching_solution(
        a_true=a_true,
        a_hat=a_hat,
        z_true_transitions=z[1:],
        z_hat_transitions=z_hat,
        support_threshold=support_threshold,
    )
    support_nnz = 0
    for mat in a_hat:
        mask = np.abs(mat) > support_threshold
        np.fill_diagonal(mask, False)
        support_nnz += int(np.sum(mask))
    return {
        "seed": seed,
        "upgraded": upgraded,
        "init_strategy": init_strategy,
        "regime_accuracy": float(ev["acc"]),
        "support_f1_mean": float(ev["mean_f1"]),
        "support_f1_per_regime": [float(v) for v in ev["f1s"]],
        "sigma2_hat": float(sigma2_hat),
        "loglik": float(ll),
        "transition_l1": float(np.mean(np.abs(trans_hat - trans_true))),
        "selection_mode": selection_mode,
        "support_nnz": int(support_nnz),
    }


def parse_scale_list(raw: str) -> list[float]:
    vals = [float(x.strip()) for x in raw.split(",") if x.strip()]
    return [v for v in vals if v > 0]


def summarize(runs: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for diff in sorted(set(r["difficulty"] for r in runs)):
        d_runs = [r for r in runs if r["difficulty"] == diff]
        for mode in ["baseline", "upgraded"]:
            m_runs = [r for r in d_runs if r["mode"] == mode]
            if not m_runs:
                continue
            key = f"{diff}_{mode}"
            out[key] = {
                "runs": len(m_runs),
                "regime_accuracy_mean": float(np.mean([x["regime_accuracy"] for x in m_runs])),
                "support_f1_mean": float(np.mean([x["support_f1_mean"] for x in m_runs])),
                "transition_l1_mean": float(np.mean([x["transition_l1"] for x in m_runs])),
                "support_nnz_mean": float(np.mean([x["support_nnz"] for x in m_runs])),
            }

        b = out.get(f"{diff}_baseline")
        u = out.get(f"{diff}_upgraded")
        if b is not None and u is not None:
            out[f"{diff}_delta"] = {
                "regime_accuracy_delta": float(u["regime_accuracy_mean"] - b["regime_accuracy_mean"]),
                "support_f1_delta": float(u["support_f1_mean"] - b["support_f1_mean"]),
                "transition_l1_delta": float(u["transition_l1_mean"] - b["transition_l1_mean"]),
                "support_nnz_delta": float(u["support_nnz_mean"] - b["support_nnz_mean"]),
            }
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step67_multiregime_upgrade"))
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--t", type=int, default=2000)
    parser.add_argument("--sigma", type=float, default=0.1)
    parser.add_argument("--obs-noise", type=float, default=0.2)
    parser.add_argument("--edge-prob", type=float, default=0.12)
    parser.add_argument("--support-threshold", type=float, default=0.05)
    parser.add_argument("--seeds", type=int, default=4)
    parser.add_argument("--seed-start", type=int, default=3301)
    parser.add_argument("--baseline-em-iterations", type=int, default=12)
    parser.add_argument("--baseline-restarts", type=int, default=4)
    parser.add_argument("--upgraded-em-iterations", type=int, default=24)
    parser.add_argument("--upgraded-restarts", type=int, default=10)
    parser.add_argument("--upgraded-bootstrap-runs", type=int, default=8)
    parser.add_argument("--upgraded-use-stability-refit", type=int, default=1)
    parser.add_argument("--baseline-selection-mode", type=str, default="loglik")
    parser.add_argument("--upgraded-selection-mode", type=str, default="loglik")
    parser.add_argument("--baseline-alpha-scales", type=str, default="0.35")
    parser.add_argument("--upgraded-alpha-scales", type=str, default="0.30,0.45,0.60")
    parser.add_argument("--min-support-nnz", type=int, default=1)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_alpha_scales = parse_scale_list(args.baseline_alpha_scales)
    upgraded_alpha_scales = parse_scale_list(args.upgraded_alpha_scales)
    if not baseline_alpha_scales:
        raise ValueError("baseline-alpha-scales must contain at least one positive value")
    if not upgraded_alpha_scales:
        raise ValueError("upgraded-alpha-scales must contain at least one positive value")

    difficulties = {
        "easy": {"min_support_diff": 0.24, "min_fro_ratio": 0.90},
        "medium": {"min_support_diff": 0.18, "min_fro_ratio": 0.75},
        "hard": {"min_support_diff": 0.15, "min_fro_ratio": 0.60},
    }

    runs: list[dict] = []
    for offset in range(args.seeds):
        seed = args.seed_start + offset
        for diff_name, params in difficulties.items():
            base = run_once(
                n=args.n,
                t=args.t,
                k=args.k,
                sigma=args.sigma,
                obs_noise_sigma=args.obs_noise,
                edge_prob=args.edge_prob,
                support_threshold=args.support_threshold,
                min_support_diff=params["min_support_diff"],
                min_fro_ratio=params["min_fro_ratio"],
                seed=seed,
                upgraded=False,
                baseline_em_iterations=args.baseline_em_iterations,
                baseline_restarts=args.baseline_restarts,
                upgraded_em_iterations=args.upgraded_em_iterations,
                upgraded_restarts=args.upgraded_restarts,
                upgraded_bootstrap_runs=args.upgraded_bootstrap_runs,
                upgraded_use_stability_refit=bool(args.upgraded_use_stability_refit),
                baseline_selection_mode=args.baseline_selection_mode,
                upgraded_selection_mode=args.upgraded_selection_mode,
                baseline_alpha_scales=baseline_alpha_scales,
                upgraded_alpha_scales=upgraded_alpha_scales,
                min_support_nnz=args.min_support_nnz,
            )
            base["difficulty"] = diff_name
            base["mode"] = "baseline"
            runs.append(base)

            up = run_once(
                n=args.n,
                t=args.t,
                k=args.k,
                sigma=args.sigma,
                obs_noise_sigma=args.obs_noise,
                edge_prob=args.edge_prob,
                support_threshold=args.support_threshold,
                min_support_diff=params["min_support_diff"],
                min_fro_ratio=params["min_fro_ratio"],
                seed=seed,
                upgraded=True,
                baseline_em_iterations=args.baseline_em_iterations,
                baseline_restarts=args.baseline_restarts,
                upgraded_em_iterations=args.upgraded_em_iterations,
                upgraded_restarts=args.upgraded_restarts,
                upgraded_bootstrap_runs=args.upgraded_bootstrap_runs,
                upgraded_use_stability_refit=bool(args.upgraded_use_stability_refit),
                baseline_selection_mode=args.baseline_selection_mode,
                upgraded_selection_mode=args.upgraded_selection_mode,
                baseline_alpha_scales=baseline_alpha_scales,
                upgraded_alpha_scales=upgraded_alpha_scales,
                min_support_nnz=args.min_support_nnz,
            )
            up["difficulty"] = diff_name
            up["mode"] = "upgraded"
            runs.append(up)

    summary = summarize(runs)
    report = {
        "config": {
            "n": args.n,
            "k": args.k,
            "t": args.t,
            "sigma": args.sigma,
            "obs_noise": args.obs_noise,
            "edge_prob": args.edge_prob,
            "support_threshold": args.support_threshold,
            "seeds": [args.seed_start + i for i in range(args.seeds)],
            "difficulties": difficulties,
            "baseline_selection_mode": args.baseline_selection_mode,
            "upgraded_selection_mode": args.upgraded_selection_mode,
            "baseline_alpha_scales": baseline_alpha_scales,
            "upgraded_alpha_scales": upgraded_alpha_scales,
            "min_support_nnz": args.min_support_nnz,
        },
        "runs": runs,
        "summary": summary,
        "logic_note": (
            "Positive delta indicates upgraded method improved baseline on that metric; "
            "negative delta indicates no improvement."
        ),
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    print("Step 67 multi-regime upgrade comparison complete.")
    print(json.dumps({"num_runs": len(runs), "num_summary_rows": len(summary)}, indent=2))


if __name__ == "__main__":
    main()
