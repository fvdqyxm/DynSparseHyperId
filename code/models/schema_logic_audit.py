#!/usr/bin/env python3
"""Cross-artifact schema/logic audit for research coherence."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def tracker_consistency_checks() -> dict:
    phase0 = load_csv(ROOT / "tracking" / "phase0_steps.csv")
    phase1 = load_csv(ROOT / "tracking" / "phase1_steps.csv")

    issues: list[str] = []

    for name, rows in [("phase0", phase0), ("phase1", phase1)]:
        for row in rows:
            status = row["Status"].strip()
            notes = row["Notes/Results"].strip()
            step = row["Step #"].strip()
            if status == "Completed":
                if not notes:
                    issues.append(f"{name} step {step}: completed but notes empty")
                if "Not implemented yet" in notes:
                    issues.append(f"{name} step {step}: completed but notes say not implemented")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
    }


def claim_registry_evidence_checks() -> dict:
    text = (ROOT / "docs" / "claim_logic_registry.md").read_text()
    paths = re.findall(r"`([^`]+)`", text)

    missing: list[str] = []
    checked: list[str] = []
    for p in paths:
        # Only check repo-local path-like entries.
        if p.startswith(("results/", "tracking/", "tests/", "docs/", "proofs/", "code/", "literature/")):
            canonical = p.split("::", 1)[0]
            checked.append(canonical)
            if not (ROOT / canonical).exists():
                missing.append(canonical)

    return {
        "passed": len(missing) == 0,
        "checked_paths": checked,
        "missing_paths": missing,
    }


def formula_audit_checks() -> dict:
    path = ROOT / "docs" / "formula_traceability_audit_2026_03_12.md"
    text = path.read_text() if path.exists() else ""

    required_phrases = [
        "implemented exactly",
        "not yet implemented",
        "Unsafe statement now",
        "Turnbull",
        "Chandrasekaran",
        "Friedman",
    ]
    missing = [p for p in required_phrases if p not in text]

    return {
        "passed": len(missing) == 0,
        "missing_phrases": missing,
    }


def observability_claim_alignment_checks() -> dict:
    metrics_path = ROOT / "results" / "phase0_wilson_cowan" / "metrics_summary.json"
    claim_path = ROOT / "docs" / "claim_logic_registry.md"

    issues: list[str] = []
    if not metrics_path.exists():
        issues.append("Wilson metrics missing")
    else:
        report = json.loads(metrics_path.read_text())
        low_obs = bool(report["dynamics_diagnostics"]["low_observability_flag"])
        if low_obs:
            claim_text = claim_path.read_text()
            if "Claim C5" in claim_text and "Not supported" not in claim_text:
                issues.append("C5 should remain not-supported when observability is low")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
    }


def biological_realism_proxy_checks() -> dict:
    script = (ROOT / "code" / "models" / "wilson_cowan_hrf_pipeline.py").read_text()
    required_tokens = [
        "motion_spike_prob",
        "physio_amp",
        "drift_amp",
        "canonical_hrf",
    ]
    missing_tokens = [t for t in required_tokens if t not in script]

    return {
        "passed": len(missing_tokens) == 0,
        "missing_tokens": missing_tokens,
    }


def assumption_literature_gate_checks() -> dict:
    path = ROOT / "results" / "rigor_checks" / "assumption_literature_audit.json"
    if not path.exists():
        return {
            "passed": False,
            "issues": [f"missing assumption literature audit report: {path}"],
        }

    report = json.loads(path.read_text())
    passed = bool(report.get("all_passed", False))
    issues = [] if passed else [f"assumption literature audit failed: {report.get('checks', {})}"]
    return {
        "passed": passed,
        "issues": issues,
    }


def main() -> None:
    out_dir = ROOT / "results" / "rigor_checks"
    out_dir.mkdir(parents=True, exist_ok=True)

    checks = {
        "tracker_consistency": tracker_consistency_checks(),
        "claim_registry_evidence": claim_registry_evidence_checks(),
        "formula_audit": formula_audit_checks(),
        "observability_claim_alignment": observability_claim_alignment_checks(),
        "biological_realism_proxy": biological_realism_proxy_checks(),
        "assumption_literature_gate": assumption_literature_gate_checks(),
    }
    all_passed = bool(all(v.get("passed", False) for v in checks.values()))

    report = {
        "checks": checks,
        "all_passed": all_passed,
    }
    (out_dir / "schema_logic_audit.json").write_text(json.dumps(report, indent=2))
    print("Schema logic audit complete.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
