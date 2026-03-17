# Claim Logic Registry (White Paper Draft Backbone)

## Purpose
Track each candidate white-paper claim with:
1. formal statement,
2. required assumptions,
3. current evidence,
4. falsification tests,
5. status.

## Claim C1 — Pairwise sparse structure is recoverable at moderate noise
- Statement:
  In synthetic linear-Gaussian settings with controlled sparsity, pairwise support can be
  recovered with F1 > 0.75 at sigma = 0.5.
- Assumptions:
  sparse true support, stable dynamics, sufficient T.
- Evidence:
  `results/phase0/metrics_summary.json` (glasso + sparse_lds).
- Falsification test:
  `tests/test_phase0_steps.py::test_metrics_schema_and_gate_thresholds`.
- Status:
  Supported.

## Claim C2 — Step-level progress is reproducible and auditable
- Statement:
  Completed milestones map to concrete artifacts and machine checks.
- Assumptions:
  Tracker and tests remain synchronized.
- Evidence:
  `tracking/phase0_steps.csv`, test suite, runner script.
- Falsification test:
  `tests/test_phase0_steps.py::test_completed_tracker_steps_have_artifact_evidence`.
- Status:
  Supported.

## Claim C3 — Regime-switching sparse recovery is solved
- Statement:
  Two-regime sparse LDS parameters/regimes can be recovered robustly with current baseline.
- Assumptions:
  identifiable separation + adequate optimization.
- Evidence:
  `results/phase0/metrics_summary.json` (`switching_lds` block).
- Falsification test:
  robustness sweep under observation-noise stress (`results/phase0_switching_sweep/sweep_metrics.json`).
- Status:
  Supported for moderate noise; degrades in harder noise (documented limit).

## Claim C4 — High-order latent regime-switching theory is new and impactful
- Statement:
  Combined framework (sparse high-order + latent Markov switching + identifiability/sample complexity)
  is underdeveloped relative to components.
- Assumptions:
  no existing work already closes this full gap.
- Evidence:
  See novelty memo and source links in `docs/novelty_landscape_2026_03_12.md`.
- Falsification test:
  literature scan updates; if near-identical theorem exists, narrow contribution.
- Status:
  Plausible but requires continuous literature verification.

## Claim C5 — Neuroscience illustration can be interpreted mechanistically
- Statement:
  recovered motifs reflect causal craving circuitry.
- Assumptions:
  confound controls and robustness analyses.
- Evidence:
  None yet.
- Falsification test:
  motion/physio confound stress tests, negative controls.
- Status:
  Not supported.

## Claim C6 — Current synthetic gains are not leakage artifacts
- Statement:
  strong synthetic recovery in implemented modules is not explained by label leakage or permutation artifacts.
- Assumptions:
  adversarial controls remain in CI and continue passing.
- Evidence:
  `results/rigor_checks/metrics_summary.json`,
  `results/rigor_checks/schema_logic_audit.json`.
- Falsification test:
  `tests/test_phase0_steps.py::test_adversarial_rigor_controls`,
  `tests/test_phase0_steps.py::test_schema_logic_audit_controls`.
- Status:
  Supported (for current synthetic settings).

## Claim C7 — Core assumptions are literature-orthodox individually
- Statement:
  A1-A6 are individually grounded in established theory families (sparsity, incoherence, beta-min, mixing, regime separation, controlled noise).
- Assumptions:
  Source mapping remains explicit and claim-safe language ("integrated theorem open") is preserved.
- Evidence:
  `docs/assumption_literature_matrix.csv`,
  `docs/assumption_validity_literature_check_2026_03_12.md`,
  `docs/phase1_assumption_literature_summaries_round2.md`.
- Falsification test:
  `code/models/assumption_literature_audit.py`,
  `results/rigor_checks/assumption_literature_audit.json`.
- Status:
  Supported at assumption-class level; integrated theorem still open.
