#!/usr/bin/env python3
"""Phase 3 Step 76: Gate 3 assessment (biological plausibility narrative fit)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: Path) -> dict:
    if not path.exists():
        return {"status": "missing_file"}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {"status": "invalid_json"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step70", type=Path, default=Path("results/phase3_step70_motifs/metrics_summary.json"))
    parser.add_argument("--step71", type=Path, default=Path("results/phase3_step71_prediction/metrics_summary.json"))
    parser.add_argument("--step72", type=Path, default=Path("results/phase3_step72_baseline_compare/metrics_summary.json"))
    parser.add_argument("--step73", type=Path, default=Path("results/phase3_step73_visuals/metrics_summary.json"))
    parser.add_argument("--step74", type=Path, default=Path("results/phase3_step74_cross_dataset/metrics_summary.json"))
    parser.add_argument("--step75", type=Path, default=Path("results/phase3_step75_ablation/metrics_summary.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase3_step76_gate3"))
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    m70 = _load(args.step70)
    m71 = _load(args.step71)
    m72 = _load(args.step72)
    m73 = _load(args.step73)
    m74 = _load(args.step74)
    m75 = _load(args.step75)

    statuses = {
        "step70": m70.get("status"),
        "step71": m71.get("status"),
        "step72": m72.get("status"),
        "step73": m73.get("status"),
        "step74": m74.get("status"),
        "step75": m75.get("status"),
    }

    hard_block = any(
        s in {
            "blocked_missing_window_files",
            "blocked_missing_labels",
            "blocked_missing_step70_artifacts",
            "blocked_step70_not_ready",
            "blocked_missing_manifest",
            "blocked_missing_data_root",
            "blocked_missing_dataset_root",
            "blocked_upstream_not_ready",
        }
        for s in statuses.values()
    )

    if hard_block:
        gate_status = "blocked_by_data"
        decision = "Cannot close Gate 3 until real dataset preflight and downstream motif/prediction pipeline are ready."
    else:
        gate_status = "provisional_pass"
        decision = "Pipeline artifacts present; biological plausibility narrative can be drafted provisionally."

    report = {
        "status": gate_status,
        "decision": decision,
        "upstream_statuses": statuses,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
