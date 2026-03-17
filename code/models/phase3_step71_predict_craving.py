#!/usr/bin/env python3
"""Phase 3 Step 71: predict craving instability from motif/dwell features."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge


def _kfold_indices(n: int, k: int) -> list[tuple[np.ndarray, np.ndarray]]:
    idx = np.arange(n, dtype=np.int64)
    folds = np.array_split(idx, k)
    out = []
    for i in range(k):
        test = folds[i]
        train = np.concatenate([folds[j] for j in range(k) if j != i])
        out.append((train, test))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step70-metrics", type=Path, default=Path("results/phase3_step70_motifs/metrics_summary.json"))
    parser.add_argument("--step70-scores", type=Path, default=Path("results/phase3_step70_motifs/motif_scores.npy"))
    parser.add_argument("--step70-craving", type=Path, default=Path("results/phase3_step70_motifs/subject_craving.npy"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase3_step71_prediction"))
    parser.add_argument("--ridge-alpha", type=float, default=1.0)
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.step70_metrics.exists() or not args.step70_scores.exists() or not args.step70_craving.exists():
        report = {
            "status": "blocked_missing_step70_artifacts",
            "issues": [
                f"Missing one or more Step70 artifacts: {args.step70_metrics}, {args.step70_scores}, {args.step70_craving}"
            ],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    m70 = json.loads(args.step70_metrics.read_text())
    if m70.get("status") != "ok":
        report = {
            "status": "blocked_step70_not_ready",
            "step70_status": m70.get("status", "unknown"),
            "issues": ["Step70 did not complete in ready state."],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    X = np.load(args.step70_scores)
    y = np.load(args.step70_craving)
    if X.shape[0] != y.shape[0] or X.shape[0] < args.folds:
        report = {
            "status": "blocked_insufficient_samples",
            "n_samples": int(X.shape[0]),
            "issues": ["Need enough subject samples for cross-validation."],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    preds = np.zeros_like(y, dtype=np.float64)
    fold_rows = []
    for i, (tr, te) in enumerate(_kfold_indices(X.shape[0], args.folds)):
        model = Ridge(alpha=args.ridge_alpha)
        model.fit(X[tr], y[tr])
        yp = model.predict(X[te])
        preds[te] = yp
        mse = float(np.mean((yp - y[te]) ** 2))
        fold_rows.append({"fold": i, "n_train": int(tr.size), "n_test": int(te.size), "mse": mse})

    mse_cv = float(np.mean((preds - y) ** 2))
    var_y = float(np.var(y))
    r2_cv = float(1.0 - mse_cv / max(var_y, 1e-12))
    mae_cv = float(np.mean(np.abs(preds - y)))

    report = {
        "status": "ok",
        "n_subjects": int(X.shape[0]),
        "folds": int(args.folds),
        "ridge_alpha": float(args.ridge_alpha),
        "cv_mse": mse_cv,
        "cv_mae": mae_cv,
        "cv_r2": r2_cv,
        "fold_rows": fold_rows,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    np.save(out_dir / "y_pred.npy", preds)
    print(json.dumps({"status": "ok", "cv_r2": r2_cv, "cv_mse": mse_cv}, indent=2))


if __name__ == "__main__":
    main()
