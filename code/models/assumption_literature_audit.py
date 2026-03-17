#!/usr/bin/env python3
"""Audit assumption-to-literature grounding for A1-A6.

This script enforces a claim-safe standard:
1. every core assumption has explicit primary-source anchors,
2. every assumption has a transferability caveat,
3. no row claims the integrated theorem is already solved,
4. each assumption maps to an executable artifact path.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs" / "assumption_literature_matrix.csv"
NOTE_PATH = ROOT / "docs" / "assumption_validity_literature_check_2026_03_12.md"
TEX_PATH = ROOT / "proofs" / "latex" / "master.tex"
OUT_PATH = ROOT / "results" / "rigor_checks" / "assumption_literature_audit.json"

EXPECTED_ASSUMPTIONS = ["A1", "A2", "A3", "A4", "A5", "A6"]


def _load_rows() -> list[dict[str, str]]:
    with MATRIX_PATH.open(newline="") as f:
        return list(csv.DictReader(f))


def _path_exists(expr: str) -> bool:
    canonical = expr.split("::", 1)[0].strip()
    if not canonical:
        return False
    return (ROOT / canonical).exists()


def check_matrix_structure(rows: list[dict[str, str]]) -> dict:
    issues: list[str] = []
    ids = [r.get("Assumption ID", "").strip() for r in rows]

    if sorted(ids) != EXPECTED_ASSUMPTIONS:
        issues.append(f"expected IDs {EXPECTED_ASSUMPTIONS}, found {sorted(ids)}")

    required_cols = [
        "Assumption Statement",
        "Primary Source 1",
        "Primary Source 2",
        "Validity Verdict",
        "Transferability Caveat",
        "Current Empirical Gate",
        "Status",
    ]

    for row in rows:
        aid = row.get("Assumption ID", "?").strip() or "?"
        for col in required_cols:
            if not row.get(col, "").strip():
                issues.append(f"{aid}: missing {col}")

        source_fields = [
            row.get("Primary Source 1", "").strip(),
            row.get("Primary Source 2", "").strip(),
            row.get("Primary Source 3", "").strip(),
        ]
        nonempty_sources = [s for s in source_fields if s]
        if len(nonempty_sources) < 2:
            issues.append(f"{aid}: fewer than 2 primary sources")
        for src in nonempty_sources:
            if not re.match(r"^https?://", src):
                issues.append(f"{aid}: source is not URL-like: {src}")

        verdict = row.get("Validity Verdict", "").lower()
        if "supported" not in verdict:
            issues.append(f"{aid}: verdict must include 'supported' to remain explicit")

        caveat = row.get("Transferability Caveat", "").lower()
        if len(caveat.split()) < 6:
            issues.append(f"{aid}: transferability caveat too short")

        status = row.get("Status", "").lower()
        if "open" not in status:
            issues.append(f"{aid}: status must state integrated theorem remains open")

        gate = row.get("Current Empirical Gate", "").strip()
        if not _path_exists(gate):
            issues.append(f"{aid}: gate path missing: {gate}")

    return {"passed": len(issues) == 0, "issues": issues, "count": len(rows)}


def check_assumption_note() -> dict:
    issues: list[str] = []
    if not NOTE_PATH.exists():
        return {"passed": False, "issues": [f"missing note: {NOTE_PATH}"]}

    text = NOTE_PATH.read_text()
    for aid in EXPECTED_ASSUMPTIONS:
        if f"## {aid}" not in text:
            issues.append(f"missing heading for {aid} in assumption validity note")

    required_phrases = [
        "Critical Caveat",
        "open contribution",
        "We should not claim",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            issues.append(f"missing phrase in assumption note: {phrase}")

    return {"passed": len(issues) == 0, "issues": issues}


def check_latex_alignment() -> dict:
    issues: list[str] = []
    if not TEX_PATH.exists():
        return {"passed": False, "issues": [f"missing tex file: {TEX_PATH}"]}

    text = TEX_PATH.read_text()
    for aid, label in [
        ("A1", "Controlled Sparsity"),
        ("A2", "Regime Separation"),
        ("A3", "Noise Regularity"),
        ("A4", "Hyperedge Incoherence"),
        ("A5", "Mixing and Effective Sample Size"),
        ("A6", "Beta-Min"),
    ]:
        marker = f"[A{aid[-1]}: {label}]"
        if marker not in text:
            issues.append(f"missing LaTeX marker: {marker}")

    return {"passed": len(issues) == 0, "issues": issues}


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not MATRIX_PATH.exists():
        report = {"all_passed": False, "checks": {"matrix": {"passed": False, "issues": [f"missing matrix: {MATRIX_PATH}"]}}}
        OUT_PATH.write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        raise SystemExit(1)

    rows = _load_rows()
    checks = {
        "matrix_structure": check_matrix_structure(rows),
        "assumption_note": check_assumption_note(),
        "latex_alignment": check_latex_alignment(),
    }
    all_passed = bool(all(v.get("passed", False) for v in checks.values()))
    report = {"all_passed": all_passed, "checks": checks}

    OUT_PATH.write_text(json.dumps(report, indent=2))
    print("Assumption literature audit complete.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
