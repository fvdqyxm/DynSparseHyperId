#!/usr/bin/env python3
"""Phase 2 Step 53: proximal-gradient group-lasso module and smoke test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def prox_group_l2_columns(w: np.ndarray, lam: float) -> np.ndarray:
    """Apply group-l2 shrinkage to each column (group) of w."""
    out = w.copy()
    for j in range(out.shape[1]):
        v = out[:, j]
        norm = float(np.linalg.norm(v))
        if norm <= lam:
            out[:, j] = 0.0
        else:
            out[:, j] = (1.0 - lam / norm) * v
    return out


def objective_quadratic_group(w: np.ndarray, b: np.ndarray, alpha: float) -> float:
    resid = w - b
    smooth = 0.5 * float(np.sum(resid * resid))
    nonsmooth = alpha * float(np.sum(np.linalg.norm(w, axis=0)))
    return smooth + nonsmooth


def run_smoke(
    out_dir: Path,
    seed: int,
    rows: int,
    cols: int,
    alpha: float,
    step_size: float,
    iterations: int,
) -> dict:
    rng = np.random.default_rng(seed)
    b = rng.normal(size=(rows, cols))
    w = rng.normal(scale=0.5, size=(rows, cols))

    history = []
    for _ in range(iterations):
        grad = w - b
        w_half = w - step_size * grad
        w = prox_group_l2_columns(w_half, lam=step_size * alpha)
        history.append(objective_quadratic_group(w, b, alpha))

    diffs = np.diff(np.array(history, dtype=np.float64))
    monotone_frac = float(np.mean(diffs <= 1e-10)) if diffs.size > 0 else 1.0

    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "seed": seed,
        "rows": rows,
        "cols": cols,
        "alpha": alpha,
        "step_size": step_size,
        "iterations": iterations,
        "initial_objective": float(history[0]),
        "final_objective": float(history[-1]),
        "objective_monotone_fraction": monotone_frac,
        "sparsity_fraction_final": float(np.mean(np.linalg.norm(w, axis=0) < 1e-9)),
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step53_proximal"))
    parser.add_argument("--seed", type=int, default=703)
    parser.add_argument("--rows", type=int, default=16)
    parser.add_argument("--cols", type=int, default=30)
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--step-size", type=float, default=0.9)
    parser.add_argument("--iterations", type=int, default=40)
    args = parser.parse_args()

    report = run_smoke(
        out_dir=args.out_dir,
        seed=args.seed,
        rows=args.rows,
        cols=args.cols,
        alpha=args.alpha,
        step_size=args.step_size,
        iterations=args.iterations,
    )
    print("Step 53 proximal group-lasso smoke check complete.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
