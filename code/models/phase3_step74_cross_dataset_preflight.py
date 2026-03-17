#!/usr/bin/env python3
"""Phase 3 Step 74: cross-dataset accessibility preflight (ABCD SUD subset)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abcd-root", type=Path, default=Path("data/real/abcd_sud_subset"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase3_step74_cross_dataset"))
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    issues = []
    status = "ready"

    if not args.abcd_root.exists():
        status = "blocked_missing_dataset_root"
        issues.append(f"ABCD subset root not found: {args.abcd_root}")
    else:
        subs = sorted(args.abcd_root.glob("sub-*"))
        if not subs:
            status = "blocked_no_subject_dirs"
            issues.append("No sub-* directories found under ABCD root.")

    report = {
        "status": status,
        "abcd_root": str(args.abcd_root),
        "issues": issues,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
