#!/usr/bin/env python3
"""Phase 3 Step 70: infer dynamic motifs and correlate with craving instability."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _load_labels(path: Path) -> dict[str, float]:
    raw = np.genfromtxt(path, delimiter=",", names=True, dtype=None, encoding="utf-8")
    if raw.dtype.names is None:
        return {}
    names = list(raw.dtype.names)
    sid_col = None
    for c in names:
        if c.lower() in {"subject_id", "sub", "participant_id"}:
            sid_col = c
            break
    if sid_col is None:
        return {}

    label_map: dict[str, float] = {}
    # Direct variance column if present.
    var_cols = [c for c in names if c.lower() in {"craving_var", "craving_variance"}]
    if var_cols:
        vc = var_cols[0]
        for row in raw:
            sid = str(row[sid_col])
            try:
                label_map[sid] = float(row[vc])
            except Exception:
                continue
        return label_map

    # Fallback: variance over repeated craving columns.
    cr_cols = [c for c in names if c.lower().startswith("craving_")]
    if not cr_cols:
        return {}
    for row in raw:
        sid = str(row[sid_col])
        vals = []
        for c in cr_cols:
            try:
                vals.append(float(row[c]))
            except Exception:
                pass
        if len(vals) >= 2:
            label_map[sid] = float(np.var(vals))
    return label_map


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 3 or y.size < 3:
        return float("nan")
    x0 = x - np.mean(x)
    y0 = y - np.mean(y)
    den = np.sqrt(np.sum(x0 * x0) * np.sum(y0 * y0))
    if den <= 1e-12:
        return float("nan")
    return float(np.sum(x0 * y0) / den)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows-dir", type=Path, default=Path("results/phase3_step69_windows"))
    parser.add_argument("--labels", type=Path, default=Path("data/real/marijuana_323/phenotypes/craving_labels.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase3_step70_motifs"))
    parser.add_argument("--n-motifs", type=int, default=6)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    win_files = sorted(args.windows_dir.glob("sub-*_windows.npz"))
    if not win_files:
        report = {
            "status": "blocked_missing_window_files",
            "windows_dir": str(args.windows_dir),
            "issues": [f"No window files found under {args.windows_dir}"],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    if not args.labels.exists():
        report = {
            "status": "blocked_missing_labels",
            "labels": str(args.labels),
            "issues": [f"Label file missing: {args.labels}"],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    label_map = _load_labels(args.labels)
    if not label_map:
        report = {
            "status": "blocked_label_schema_unrecognized",
            "labels": str(args.labels),
            "issues": ["Could not parse subject-wise craving instability labels from provided CSV."],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    subj_rows = []
    X = []
    y = []
    kept_subject_ids: list[str] = []
    for wf in win_files:
        sid = wf.name.replace("_windows.npz", "")
        if sid not in label_map:
            continue
        payload = np.load(wf)
        feats = payload["features"]  # [n_windows, d]
        if feats.ndim != 2 or feats.shape[0] < 2:
            continue

        mean_feat = np.mean(feats, axis=0)
        # Instability proxy: average stepwise change magnitude in latent-window features.
        instab = float(np.mean(np.linalg.norm(np.diff(feats, axis=0), axis=1)))
        X.append(np.concatenate([mean_feat[: min(100, mean_feat.size)], np.array([instab])]))
        y.append(label_map[sid])
        kept_subject_ids.append(sid)
        subj_rows.append({"subject_id": sid, "n_windows": int(feats.shape[0]), "instability": instab, "craving_var": float(label_map[sid])})

    if len(X) < 5:
        report = {
            "status": "blocked_insufficient_subject_overlap",
            "n_subjects_overlap": len(X),
            "issues": ["Need at least 5 subjects with both window features and craving labels."],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    X_arr = np.asarray(X, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    # Motif inference proxy: PCA-style top components from covariance eigenspectrum.
    X_center = X_arr - np.mean(X_arr, axis=0, keepdims=True)
    cov = (X_center.T @ X_center) / max(X_center.shape[0] - 1, 1)
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    n_m = min(args.n_motifs, eigvecs.shape[1])
    motifs = eigvecs[:, :n_m]
    motif_scores = X_center @ motifs

    # Destabilization vs craving variance.
    instability = np.array([r["instability"] for r in subj_rows], dtype=np.float64)
    corr = _pearson(instability, y_arr)

    np.save(out_dir / "motif_basis.npy", motifs)
    np.save(out_dir / "motif_scores.npy", motif_scores)
    np.save(out_dir / "subject_craving.npy", y_arr)
    np.save(out_dir / "subject_ids.npy", np.asarray(kept_subject_ids, dtype=object))
    # Store explicit feature matrices for downstream static-vs-dynamic baseline comparisons.
    np.save(out_dir / "dynamic_features.npy", X_arr)  # includes instability feature in last column
    np.save(out_dir / "static_features.npy", X_arr[:, :-1])  # excludes instability term

    report = {
        "status": "ok",
        "n_subjects": int(len(subj_rows)),
        "n_motifs": int(n_m),
        "instability_craving_pearson": corr,
        "subject_rows": subj_rows,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"status": "ok", "n_subjects": len(subj_rows), "corr": corr}, indent=2))


if __name__ == "__main__":
    main()
