#!/usr/bin/env python3
"""Phase 2 Step 54: temporal KL regularization term module."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def gaussian_kl_diag(mu_p: np.ndarray, logvar_p: np.ndarray, mu_q: np.ndarray, logvar_q: np.ndarray) -> float:
    """KL(N_p || N_q) for diagonal Gaussians."""
    var_p = np.exp(logvar_p)
    var_q = np.exp(logvar_q)
    term = logvar_q - logvar_p + (var_p + (mu_p - mu_q) ** 2) / np.maximum(var_q, 1e-12) - 1.0
    return 0.5 * float(np.sum(term))


def temporal_kl_penalty(
    mus: list[np.ndarray],
    logvars: list[np.ndarray],
    beta: float,
) -> float:
    if len(mus) != len(logvars):
        raise ValueError("mus/logvars length mismatch")
    if len(mus) < 2:
        return 0.0
    total = 0.0
    for t in range(1, len(mus)):
        total += gaussian_kl_diag(mus[t], logvars[t], mus[t - 1], logvars[t - 1])
    return beta * total


def run_smoke(
    out_dir: Path,
    seed: int,
    time_steps: int,
    dim: int,
    beta: float,
) -> dict:
    rng = np.random.default_rng(seed)
    mus = [rng.normal(scale=0.3, size=(dim,)) for _ in range(time_steps)]
    logvars = [rng.normal(loc=-0.5, scale=0.2, size=(dim,)) for _ in range(time_steps)]

    penalty = temporal_kl_penalty(mus=mus, logvars=logvars, beta=beta)
    # sanity: zero when identical consecutive states.
    mus_same = [mus[0].copy() for _ in range(time_steps)]
    logvars_same = [logvars[0].copy() for _ in range(time_steps)]
    penalty_same = temporal_kl_penalty(mus=mus_same, logvars=logvars_same, beta=beta)

    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "seed": seed,
        "time_steps": time_steps,
        "dim": dim,
        "beta": beta,
        "penalty_random": float(penalty),
        "penalty_identical": float(penalty_same),
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step54_temporal_kl"))
    parser.add_argument("--seed", type=int, default=704)
    parser.add_argument("--time-steps", type=int, default=20)
    parser.add_argument("--dim", type=int, default=32)
    parser.add_argument("--beta", type=float, default=0.1)
    args = parser.parse_args()

    report = run_smoke(
        out_dir=args.out_dir,
        seed=args.seed,
        time_steps=args.time_steps,
        dim=args.dim,
        beta=args.beta,
    )
    print("Step 54 temporal KL smoke check complete.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
