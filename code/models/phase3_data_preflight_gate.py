#!/usr/bin/env python3
"""Phase 3 data preflight gate: prove data readiness before real runs."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {"status": "missing_file", "path": str(path)}
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        return {"status": "invalid_json", "path": str(path), "error": str(exc)}


def _check_label_schema(label_file: Path) -> dict:
    report = {
        "exists": label_file.exists(),
        "subject_column_ok": False,
        "target_column_ok": False,
        "columns": [],
        "issues": [],
    }
    if not label_file.exists():
        report["issues"].append(f"Label file missing: {label_file}")
        return report

    with label_file.open(newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
    cols_l = [c.lower() for c in cols]
    report["columns"] = cols

    has_subject = any(c in {"subject_id", "participant_id", "sub"} for c in cols_l)
    has_var = any(c in {"craving_var", "craving_variance"} for c in cols_l)
    craving_cols = [c for c in cols_l if c.startswith("craving_")]
    has_repeated = len(craving_cols) >= 2

    report["subject_column_ok"] = has_subject
    report["target_column_ok"] = has_var or has_repeated
    if not has_subject:
        report["issues"].append("Missing subject id column (subject_id/participant_id/sub).")
    if not report["target_column_ok"]:
        report["issues"].append(
            "Missing craving target: need craving_var or >=2 craving_* columns."
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bids-root", type=Path, default=Path("data/real/marijuana_323"))
    parser.add_argument(
        "--label-file",
        type=Path,
        default=Path("data/real/marijuana_323/phenotypes/craving_labels.csv"),
    )
    parser.add_argument("--abcd-root", type=Path, default=Path("data/real/abcd_sud_subset"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase3_data_preflight_gate"))
    parser.add_argument("--min-subjects", type=int, default=5)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    step68_dir = out_dir / "step68"
    step74_dir = out_dir / "step74"
    step68_dir.mkdir(parents=True, exist_ok=True)
    step74_dir.mkdir(parents=True, exist_ok=True)

    py = sys.executable
    subprocess.run(
        [
            py,
            "code/models/phase3_step68_data_intake.py",
            "--bids-root",
            str(args.bids_root),
            "--label-file",
            str(args.label_file),
            "--out-dir",
            str(step68_dir),
        ],
        check=True,
    )
    subprocess.run(
        [
            py,
            "code/models/phase3_step74_cross_dataset_preflight.py",
            "--abcd-root",
            str(args.abcd_root),
            "--out-dir",
            str(step74_dir),
        ],
        check=True,
    )

    m68 = _load_json(step68_dir / "metrics_summary.json")
    m74 = _load_json(step74_dir / "metrics_summary.json")
    label_schema = _check_label_schema(args.label_file)

    issues: list[str] = []
    step68_ok = m68.get("status") in {"ready_for_step69", "partial_ready"}
    step74_ok = m74.get("status") == "ready"
    if not step68_ok:
        issues.append(f"Step68 not ready: {m68.get('status')}")
    if not step74_ok:
        issues.append(f"Step74 not ready: {m74.get('status')}")

    n_subjects = int(m68.get("n_subjects", 0))
    n_atlas = int(m68.get("n_with_atlas_timeseries", 0))
    if n_subjects < args.min_subjects:
        issues.append(
            f"Insufficient subjects for minimum CV: {n_subjects} < {args.min_subjects}."
        )
    if n_atlas < args.min_subjects:
        issues.append(
            f"Insufficient atlas-timeseries subjects: {n_atlas} < {args.min_subjects}."
        )
    issues.extend(label_schema["issues"])

    passed = step68_ok and step74_ok and len(issues) == 0
    report = {
        "status": "pass" if passed else "fail",
        "passed": passed,
        "inputs": {
            "bids_root": str(args.bids_root),
            "label_file": str(args.label_file),
            "abcd_root": str(args.abcd_root),
            "min_subjects": int(args.min_subjects),
        },
        "step68_status": m68.get("status"),
        "step74_status": m74.get("status"),
        "n_subjects": n_subjects,
        "n_with_atlas_timeseries": n_atlas,
        "label_schema": label_schema,
        "issues": issues,
        "next_command_if_pass": (
            "BIDS_ROOT=<...> LABELS_CSV=<...> ABCD_ROOT=<...> ./scripts/run_phase3_on_data_mount.sh"
        ),
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
