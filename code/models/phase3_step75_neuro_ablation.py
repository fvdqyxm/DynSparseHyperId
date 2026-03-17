#!/usr/bin/env python3
"""Phase 3 Step 75: high-order vs pairwise ablation in neuroscience feature space."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge


def _kfold(n: int, k: int) -> list[tuple[np.ndarray, np.ndarray]]:
    idx = np.arange(n)
    folds = np.array_split(idx, k)
    out = []
    for i in range(k):
        te = folds[i]
        tr = np.concatenate([folds[j] for j in range(k) if j != i])
        out.append((tr, te))
    return out


def _cv_mse(X: np.ndarray, y: np.ndarray, alpha: float = 1.0, folds: int = 5) -> float:
    pred = np.zeros_like(y)
    for tr, te in _kfold(X.shape[0], folds):
        m = Ridge(alpha=alpha)
        m.fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    return float(np.mean((pred - y) ** 2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step70-metrics", type=Path, default=Path("results/phase3_step70_motifs/metrics_summary.json"))
    parser.add_argument("--step70-scores", type=Path, default=Path("results/phase3_step70_motifs/motif_scores.npy"))
    parser.add_argument("--step70-craving", type=Path, default=Path("results/phase3_step70_motifs/subject_craving.npy"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase3_step75_ablation"))
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.step70_metrics.exists() or not args.step70_scores.exists() or not args.step70_craving.exists():
        report = {
            "status": "blocked_missing_step70_artifacts",
            "issues": ["Need Step70 outputs before Step75 ablation."],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    m70 = json.loads(args.step70_metrics.read_text())
    if m70.get("status") != "ok":
        report = {
            "status": "blocked_step70_not_ready",
            "step70_status": m70.get("status"),
            "issues": ["Step70 not ready."],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    X_high = np.load(args.step70_scores)
    y = np.load(args.step70_craving)
    if X_high.shape[0] < 5:
        report = {
            "status": "blocked_insufficient_subjects",
            "n_subjects": int(X_high.shape[0]),
            "issues": ["Need at least 5 subjects for cross-validated ablation."],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    # Pairwise proxy from high-order features: keep only first two principal coordinates if available.
    k_pair = min(2, X_high.shape[1])
    X_pair = X_high[:, :k_pair]

    mse_high = _cv_mse(X_high, y, alpha=1.0, folds=min(5, X_high.shape[0]))
    mse_pair = _cv_mse(X_pair, y, alpha=1.0, folds=min(5, X_pair.shape[0]))
    rel_gain = float((mse_pair - mse_high) / max(mse_pair, 1e-12))

    report = {
        "status": "ok",
        "n_subjects": int(X_high.shape[0]),
        "mse_highorder_features": mse_high,
        "mse_pairwise_proxy_features": mse_pair,
        "relative_mse_lift_pair_minus_high": rel_gain,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"status": "ok", "relative_mse_lift_pair_minus_high": rel_gain}, indent=2))


if __name__ == "__main__":
    main()
