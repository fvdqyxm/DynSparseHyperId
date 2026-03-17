#!/usr/bin/env python3
"""Phase 3 Step 72: compare dynamic predictor vs real static baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
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


def _cv_ridge(X: np.ndarray, y: np.ndarray, alpha: float, folds: int) -> tuple[float, float]:
    pred = np.zeros_like(y, dtype=np.float64)
    for tr, te in _kfold_indices(X.shape[0], folds):
        model = Ridge(alpha=alpha)
        model.fit(X[tr], y[tr])
        pred[te] = model.predict(X[te])
    mse = float(np.mean((pred - y) ** 2))
    var_y = float(np.var(y))
    r2 = float(1.0 - mse / max(var_y, 1e-12))
    return mse, r2


def _cv_pca_ridge(
    X: np.ndarray,
    y: np.ndarray,
    alpha: float,
    folds: int,
    n_comp: int,
) -> tuple[float, float]:
    pred = np.zeros_like(y, dtype=np.float64)
    for tr, te in _kfold_indices(X.shape[0], folds):
        # Fit PCA on training fold only to avoid leakage.
        n_eff = max(1, min(n_comp, X.shape[1], tr.size - 1))
        pca = PCA(n_components=n_eff, random_state=0)
        Xt = pca.fit_transform(X[tr])
        Xv = pca.transform(X[te])
        model = Ridge(alpha=alpha)
        model.fit(Xt, y[tr])
        pred[te] = model.predict(Xv)
    mse = float(np.mean((pred - y) ** 2))
    var_y = float(np.var(y))
    r2 = float(1.0 - mse / max(var_y, 1e-12))
    return mse, r2


def _cv_intercept_only(y: np.ndarray, folds: int) -> tuple[float, float]:
    pred = np.zeros_like(y, dtype=np.float64)
    for tr, te in _kfold_indices(y.size, folds):
        pred[te] = float(np.mean(y[tr]))
    mse = float(np.mean((pred - y) ** 2))
    var_y = float(np.var(y))
    r2 = float(1.0 - mse / max(var_y, 1e-12))
    return mse, r2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step71-metrics", type=Path, default=Path("results/phase3_step71_prediction/metrics_summary.json"))
    parser.add_argument("--step70-metrics", type=Path, default=Path("results/phase3_step70_motifs/metrics_summary.json"))
    parser.add_argument("--step70-static-features", type=Path, default=Path("results/phase3_step70_motifs/static_features.npy"))
    parser.add_argument("--step70-craving", type=Path, default=Path("results/phase3_step70_motifs/subject_craving.npy"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase3_step72_baseline_compare"))
    parser.add_argument("--ridge-alpha", type=float, default=1.0)
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    step70_dir = args.step70_metrics.parent
    static_path = args.step70_static_features
    craving_path = args.step70_craving
    if not static_path.exists():
        alt = step70_dir / "static_features.npy"
        if alt.exists():
            static_path = alt
    if not craving_path.exists():
        alt = step70_dir / "subject_craving.npy"
        if alt.exists():
            craving_path = alt

    required = [args.step71_metrics, args.step70_metrics, static_path, craving_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        report = {
            "status": "blocked_missing_inputs",
            "issues": [f"Missing required inputs: {', '.join(missing)}"],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    m71 = json.loads(args.step71_metrics.read_text())
    m70 = json.loads(args.step70_metrics.read_text())
    if m71.get("status") != "ok" or m70.get("status") != "ok":
        report = {
            "status": "blocked_upstream_not_ready",
            "step70_status": m70.get("status"),
            "step71_status": m71.get("status"),
            "issues": ["Step70/71 must both be ready before baseline comparison."],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    X_static = np.load(static_path)
    y = np.load(craving_path)
    if X_static.ndim != 2 or y.ndim != 1 or X_static.shape[0] != y.shape[0]:
        report = {
            "status": "blocked_schema_mismatch",
            "issues": ["Static feature matrix and craving vector shapes are inconsistent."],
            "shape_static": list(X_static.shape),
            "shape_craving": list(y.shape),
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    if y.size < 5:
        report = {
            "status": "blocked_insufficient_samples",
            "issues": ["Need at least 5 subjects for baseline comparison CV."],
            "n_subjects": int(y.size),
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    folds = int(min(args.folds, y.size))
    dyn_mse = float(m71["cv_mse"])
    dyn_r2 = float(m71["cv_r2"])

    static_rows = []
    mse_ridge, r2_ridge = _cv_ridge(X_static, y, alpha=args.ridge_alpha, folds=folds)
    static_rows.append(
        {
            "name": "static_ridge",
            "cv_mse": mse_ridge,
            "cv_r2": r2_ridge,
            "n_features": int(X_static.shape[1]),
        }
    )

    pca_components = max(1, min(8, X_static.shape[1], y.size - 1))
    mse_pca, r2_pca = _cv_pca_ridge(
        X_static,
        y,
        alpha=args.ridge_alpha,
        folds=folds,
        n_comp=pca_components,
    )
    static_rows.append(
        {
            "name": "static_pca_ridge",
            "cv_mse": mse_pca,
            "cv_r2": r2_pca,
            "n_features": int(pca_components),
        }
    )

    mse_const, r2_const = _cv_intercept_only(y, folds=folds)
    static_rows.append(
        {
            "name": "intercept_only",
            "cv_mse": mse_const,
            "cv_r2": r2_const,
            "n_features": 1,
        }
    )

    best_static = min(static_rows, key=lambda r: float(r["cv_mse"]))
    rel_lift = float((best_static["cv_mse"] - dyn_mse) / max(best_static["cv_mse"], 1e-12))

    report = {
        "status": "ok",
        "note": "Static baseline now computed from real static feature models (no proxy).",
        "dynamic_model": {"cv_mse": dyn_mse, "cv_r2": dyn_r2},
        "static_baselines": static_rows,
        "best_static_baseline": best_static,
        "relative_mse_lift_vs_best_static": rel_lift,
        "n_subjects": int(y.size),
        "folds": folds,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"status": "ok", "relative_mse_lift_vs_best_static": rel_lift}, indent=2))


if __name__ == "__main__":
    main()
