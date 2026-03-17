#!/usr/bin/env python3
"""Phase 3 Step 68: local rs-fMRI intake and preprocessing preflight."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _glob_first(root: Path, patterns: list[str]) -> str:
    for pat in patterns:
        hits = sorted(root.glob(pat))
        if hits:
            return str(hits[0])
    return ""


def build_subject_manifest(bids_root: Path) -> list[dict]:
    rows = []
    for subdir in sorted(bids_root.glob("sub-*")):
        if not subdir.is_dir():
            continue
        sid = subdir.name
        bold = _glob_first(
            bids_root,
            [
                f"**/{sid}/**/*task-rest*desc-preproc_bold.nii.gz",
                f"**/{sid}/**/*task-rest*_bold.nii.gz",
            ],
        )
        confounds = _glob_first(
            bids_root,
            [
                f"**/{sid}/**/*desc-confounds_timeseries.tsv",
                f"**/{sid}/**/*confounds*.tsv",
            ],
        )
        atlas_ts = _glob_first(
            bids_root,
            [
                f"**/{sid}/**/*Yeo*17*timeseries*.tsv",
                f"**/{sid}/**/*atlas*timeseries*.tsv",
            ],
        )
        rows.append(
            {
                "subject_id": sid,
                "bold_path": bold,
                "confounds_path": confounds,
                "atlas_timeseries_path": atlas_ts,
                "has_bold": bool(bold),
                "has_confounds": bool(confounds),
                "has_atlas_timeseries": bool(atlas_ts),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bids-root", type=Path, default=Path("data/real/marijuana_323"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase3_step68_intake"))
    parser.add_argument("--atlas", type=str, default="Yeo17")
    parser.add_argument("--label-file", type=Path, default=Path("data/real/marijuana_323/phenotypes/craving_labels.csv"))
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "bids_root": str(args.bids_root),
        "atlas": args.atlas,
        "label_file": str(args.label_file),
        "status": "ok",
        "issues": [],
    }

    if not args.bids_root.exists():
        report["status"] = "blocked_missing_data_root"
        report["issues"] = [f"BIDS root not found: {args.bids_root}"]
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    rows = build_subject_manifest(args.bids_root)
    if not rows:
        report["status"] = "blocked_no_subjects"
        report["issues"] = [f"No sub-* directories found under: {args.bids_root}"]
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    manifest_path = out_dir / "subject_manifest.csv"
    with manifest_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "subject_id",
                "bold_path",
                "confounds_path",
                "atlas_timeseries_path",
                "has_bold",
                "has_confounds",
                "has_atlas_timeseries",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    n_subjects = len(rows)
    n_bold = sum(int(r["has_bold"]) for r in rows)
    n_conf = sum(int(r["has_confounds"]) for r in rows)
    n_atlas = sum(int(r["has_atlas_timeseries"]) for r in rows)

    issues: list[str] = []
    if n_bold < n_subjects:
        issues.append(f"{n_subjects - n_bold} subjects missing rest BOLD path.")
    if n_conf < n_subjects:
        issues.append(f"{n_subjects - n_conf} subjects missing confounds path.")
    if n_atlas < n_subjects:
        issues.append(f"{n_subjects - n_atlas} subjects missing atlas timeseries path.")
    if not args.label_file.exists():
        issues.append(f"Label file missing: {args.label_file}")

    report.update(
        {
            "n_subjects": n_subjects,
            "n_with_bold": n_bold,
            "n_with_confounds": n_conf,
            "n_with_atlas_timeseries": n_atlas,
            "manifest_path": str(manifest_path),
            "issues": issues,
            "status": "ready_for_step69" if not issues else "partial_ready",
        }
    )
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
