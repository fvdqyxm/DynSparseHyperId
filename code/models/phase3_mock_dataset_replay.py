#!/usr/bin/env python3
"""Generate a mock rs-fMRI dataset and replay Phase 3 steps 68-76 end-to-end.

This script is a plumbing/reliability check only. It does not replace real-data analyses.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np


def _write_tsv(path: Path, header: list[str], arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        f.write("\t".join(header) + "\n")
        for row in arr:
            f.write("\t".join(f"{float(v):.6f}" for v in row) + "\n")


def generate_mock_dataset(
    *,
    bids_root: Path,
    labels_csv: Path,
    n_subjects: int,
    t: int,
    n_rois: int,
    seed: int,
) -> list[str]:
    rng = np.random.default_rng(seed)
    subject_ids = [f"sub-{i:04d}" for i in range(1, n_subjects + 1)]

    for sid in subject_ids:
        func_dir = bids_root / sid / "func"
        func_dir.mkdir(parents=True, exist_ok=True)

        # Placeholder BOLD path for intake checks (content not read by later steps).
        bold = func_dir / f"{sid}_task-rest_desc-preproc_bold.nii.gz"
        bold.write_bytes(b"")

        conf = rng.normal(scale=0.2, size=(t, 6))
        _write_tsv(
            func_dir / f"{sid}_desc-confounds_timeseries.tsv",
            ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"],
            conf,
        )

        x = np.zeros((t, n_rois), dtype=np.float64)
        x[0] = rng.normal(scale=0.5, size=n_rois)
        for i in range(1, t):
            x[i] = 0.7 * x[i - 1] + rng.normal(scale=0.35, size=n_rois)
        _write_tsv(
            func_dir / f"{sid}_Yeo17_timeseries.tsv",
            [f"roi_{j+1}" for j in range(n_rois)],
            x,
        )

    labels_csv.parent.mkdir(parents=True, exist_ok=True)
    with labels_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["subject_id", "craving_var"])
        w.writeheader()
        for sid in subject_ids:
            w.writerow({"subject_id": sid, "craving_var": float(rng.uniform(0.05, 1.0))})

    return subject_ids


def generate_mock_abcd(*, abcd_root: Path, n_subjects: int) -> None:
    for i in range(1, n_subjects + 1):
        (abcd_root / f"sub-{i:04d}" / "func").mkdir(parents=True, exist_ok=True)


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def _load_status(path: Path) -> str:
    if not path.exists():
        return "missing_metrics"
    try:
        return str(json.loads(path.read_text()).get("status", "unknown"))
    except Exception:
        return "invalid_metrics_json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock-root", type=Path, default=Path("data/real/mock_marijuana_323"))
    parser.add_argument(
        "--labels",
        type=Path,
        default=Path("data/real/mock_marijuana_323/phenotypes/craving_labels.csv"),
    )
    parser.add_argument("--mock-abcd-root", type=Path, default=Path("data/real/mock_abcd_sud_subset"))
    parser.add_argument("--out-root", type=Path, default=Path("results/phase3_mock_replay"))
    parser.add_argument("--n-subjects", type=int, default=8)
    parser.add_argument("--timepoints", type=int, default=180)
    parser.add_argument("--n-rois", type=int, default=17)
    parser.add_argument("--seed", type=int, default=9001)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    out_root = args.out_root
    out_root.mkdir(parents=True, exist_ok=True)

    subject_ids = generate_mock_dataset(
        bids_root=args.mock_root,
        labels_csv=args.labels,
        n_subjects=args.n_subjects,
        t=args.timepoints,
        n_rois=args.n_rois,
        seed=args.seed,
    )
    generate_mock_abcd(abcd_root=args.mock_abcd_root, n_subjects=max(2, args.n_subjects // 2))

    s68 = out_root / "step68"
    s69 = out_root / "step69"
    s70 = out_root / "step70"
    s71 = out_root / "step71"
    s72 = out_root / "step72"
    s73 = out_root / "step73"
    s74 = out_root / "step74"
    s75 = out_root / "step75"
    s76 = out_root / "step76"

    py = sys.executable
    _run(
        [
            py,
            "code/models/phase3_step68_data_intake.py",
            "--bids-root",
            str(args.mock_root),
            "--label-file",
            str(args.labels),
            "--out-dir",
            str(s68),
        ],
        repo_root,
    )
    _run(
        [
            py,
            "code/models/phase3_step69_sliding_windows.py",
            "--manifest",
            str(s68 / "subject_manifest.csv"),
            "--out-dir",
            str(s69),
            "--window",
            "60",
            "--step",
            "10",
        ],
        repo_root,
    )
    _run(
        [
            py,
            "code/models/phase3_step70_motif_inference.py",
            "--windows-dir",
            str(s69),
            "--labels",
            str(args.labels),
            "--out-dir",
            str(s70),
        ],
        repo_root,
    )
    _run(
        [
            py,
            "code/models/phase3_step71_predict_craving.py",
            "--step70-metrics",
            str(s70 / "metrics_summary.json"),
            "--step70-scores",
            str(s70 / "motif_scores.npy"),
            "--step70-craving",
            str(s70 / "subject_craving.npy"),
            "--out-dir",
            str(s71),
        ],
        repo_root,
    )
    _run(
        [
            py,
            "code/models/phase3_step72_baseline_compare.py",
            "--step71-metrics",
            str(s71 / "metrics_summary.json"),
            "--step70-metrics",
            str(s70 / "metrics_summary.json"),
            "--out-dir",
            str(s72),
        ],
        repo_root,
    )
    _run(
        [
            py,
            "code/models/phase3_step73_visualize_motifs.py",
            "--step70-metrics",
            str(s70 / "metrics_summary.json"),
            "--motif-basis",
            str(s70 / "motif_basis.npy"),
            "--motif-scores",
            str(s70 / "motif_scores.npy"),
            "--out-dir",
            str(s73),
        ],
        repo_root,
    )
    _run(
        [
            py,
            "code/models/phase3_step74_cross_dataset_preflight.py",
            "--abcd-root",
            str(args.mock_abcd_root),
            "--out-dir",
            str(s74),
        ],
        repo_root,
    )
    _run(
        [
            py,
            "code/models/phase3_step75_neuro_ablation.py",
            "--step70-metrics",
            str(s70 / "metrics_summary.json"),
            "--step70-scores",
            str(s70 / "motif_scores.npy"),
            "--step70-craving",
            str(s70 / "subject_craving.npy"),
            "--out-dir",
            str(s75),
        ],
        repo_root,
    )
    _run(
        [
            py,
            "code/models/phase3_step76_gate3_assessment.py",
            "--step70",
            str(s70 / "metrics_summary.json"),
            "--step71",
            str(s71 / "metrics_summary.json"),
            "--step72",
            str(s72 / "metrics_summary.json"),
            "--step73",
            str(s73 / "metrics_summary.json"),
            "--step74",
            str(s74 / "metrics_summary.json"),
            "--step75",
            str(s75 / "metrics_summary.json"),
            "--out-dir",
            str(s76),
        ],
        repo_root,
    )

    status_map = {
        "step68": _load_status(s68 / "metrics_summary.json"),
        "step69": _load_status(s69 / "metrics_summary.json"),
        "step70": _load_status(s70 / "metrics_summary.json"),
        "step71": _load_status(s71 / "metrics_summary.json"),
        "step72": _load_status(s72 / "metrics_summary.json"),
        "step73": _load_status(s73 / "metrics_summary.json"),
        "step74": _load_status(s74 / "metrics_summary.json"),
        "step75": _load_status(s75 / "metrics_summary.json"),
        "step76": _load_status(s76 / "metrics_summary.json"),
    }

    report = {
        "mock_root": str(args.mock_root),
        "mock_abcd_root": str(args.mock_abcd_root),
        "labels": str(args.labels),
        "n_subjects": len(subject_ids),
        "status_map": status_map,
    }
    (out_root / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
