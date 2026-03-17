#!/usr/bin/env python3
"""Phase 3 Step 69: derive sliding-window inputs from atlas time series."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def _load_timeseries(path: Path) -> np.ndarray:
    data = np.genfromtxt(path, delimiter="\t", names=True)
    if data.dtype.names is None:
        arr = np.genfromtxt(path, delimiter="\t")
        if arr.ndim == 1:
            arr = arr[:, None]
        return np.asarray(arr, dtype=np.float64)
    cols = [np.asarray(data[name], dtype=np.float64) for name in data.dtype.names]
    return np.stack(cols, axis=1)


def _window_indices(t: int, window: int, step: int) -> list[tuple[int, int]]:
    if t < window:
        return []
    out = []
    start = 0
    while start + window <= t:
        out.append((start, start + window))
        start += step
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("results/phase3_step68_intake/subject_manifest.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase3_step69_windows"))
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--step", type=int, default=10)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.manifest.exists():
        report = {
            "status": "blocked_missing_manifest",
            "manifest": str(args.manifest),
            "issues": [f"Manifest not found: {args.manifest}"],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    rows = []
    with args.manifest.open(newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    subject_reports = []
    made = 0
    for row in rows:
        sid = row["subject_id"]
        ts_path = row.get("atlas_timeseries_path", "")
        if not ts_path:
            subject_reports.append({"subject_id": sid, "status": "missing_timeseries"})
            continue
        p = Path(ts_path)
        if not p.exists():
            subject_reports.append({"subject_id": sid, "status": "timeseries_path_not_found", "path": ts_path})
            continue

        ts = _load_timeseries(p)
        wins = _window_indices(t=ts.shape[0], window=args.window, step=args.step)
        if not wins:
            subject_reports.append({"subject_id": sid, "status": "too_short", "t": int(ts.shape[0])})
            continue

        features = []
        for a, b in wins:
            w = ts[a:b]
            mean_vec = np.mean(w, axis=0)
            cov = np.cov(w, rowvar=False)
            cov_flat = cov[np.triu_indices(cov.shape[0])]
            features.append(np.concatenate([mean_vec, cov_flat]))
        feat_arr = np.stack(features, axis=0)

        np.savez_compressed(out_dir / f"{sid}_windows.npz", features=feat_arr, windows=np.asarray(wins, dtype=np.int64))
        subject_reports.append({"subject_id": sid, "status": "ok", "n_windows": int(len(wins)), "feature_dim": int(feat_arr.shape[1])})
        made += 1

    status = "ready_for_step70" if made > 0 else "blocked_no_window_outputs"
    report = {
        "status": status,
        "manifest": str(args.manifest),
        "window": args.window,
        "step": args.step,
        "n_subjects_total": len(rows),
        "n_subjects_with_window_outputs": made,
        "subject_reports": subject_reports,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"status": status, "n_subjects_with_window_outputs": made}, indent=2))


if __name__ == "__main__":
    main()
