#!/usr/bin/env python3
"""Merge stratified Step-56 batch outputs into one canonical artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_metrics(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing metrics file: {path}")
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--batch-metrics",
        type=str,
        default=(
            "results/phase2_step56_large_grid_batchA/metrics_summary.json,"
            "results/phase2_step56_large_grid_batchB/metrics_summary.json"
        ),
    )
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step56_large_grid"))
    args = parser.parse_args()

    metric_paths = [Path(x.strip()) for x in args.batch_metrics.split(",") if x.strip()]
    payloads = [load_metrics(p) for p in metric_paths]

    runs = []
    skipped = []
    for pay in payloads:
        runs.extend(pay.get("runs", []))
        skipped.extend(pay.get("skipped_runs", []))

    config = {
        "merged_from": [str(p) for p in metric_paths],
        "batch_count": len(payloads),
    }
    report = {
        "config": config,
        "requested_total": int(sum(int(p.get("requested_total", 0)) for p in payloads)),
        "executed": int(len(runs)),
        "skipped": int(len(skipped)),
        "runs": runs,
        "skipped_runs": skipped,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"executed": report["executed"], "skipped": report["skipped"]}, indent=2))


if __name__ == "__main__":
    main()
