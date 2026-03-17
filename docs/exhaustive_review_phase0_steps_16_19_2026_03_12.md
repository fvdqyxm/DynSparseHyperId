# Exhaustive Review: Phase 0 Steps 16-19 (2026-03-12)

## Scope
This note records what was implemented, what was validated, what failed, and why the outcomes are still scientifically meaningful for the eventual white paper.

## What Was Implemented
1. `code/models/wilson_cowan_hrf_pipeline.py`
- Deterministic Wilson-Cowan simulator with two latent Markov regimes.
- Regime-specific sparse coupling matrices (`C_true_regime0/1.npy`).
- HRF convolution (`bold_clean.npy`) and realistic artifact injection (`bold_noisy.npy`).
- Pairwise sparse AR recovery on both neural activity and BOLD observations.
- Effective Jacobian diagnostics of local linear observability.
- Explicit claim guardrail text in output JSON.

2. `scripts/run_phase0_checks.sh`
- Extended to run Wilson-Cowan pipeline as part of end-to-end Phase 0 verification.

3. `tests/test_phase0_steps.py`
- Added artifact checks for steps 16-19.
- Added logic gate test enforcing anti-overclaim behavior when Step 19 is marked completed.

4. `tracking/phase0_steps.csv`
- Steps 16-19 marked completed with evidence notes and interpretation constraints.

## Critical Logic Corrections
1. Headless robustness fix
- Forced `matplotlib` backend to `Agg` before `pyplot` import to avoid macOS backend aborts in terminal/CI execution.

2. Target mismatch correction
- Structural coupling (`C`) and AR recovery are not equivalent in saturated nonlinear dynamics.
- Added effective-linearization diagnostics to check whether support recovery is even observable in the generated regime.

3. Overclaim prevention
- Added `low_observability_flag` and `claim_guardrail` in metrics output.
- Added tests to enforce conservative interpretation when observability is low.

## Empirical Evidence (Current Default Run)
From `results/phase0_wilson_cowan/metrics_summary.json`:
- `regime_support_hamming`: `0.2` (regimes are distinct in planted structure).
- `mean_sigmoid_prime_regime_0/1`: ~`0.075` (weak local sensitivity).
- `effective_offdiag_abs_max_mean`: ~`7.58e-4`.
- `low_observability_flag`: `true`.
- Structural-coupling recovery F1:
  - neural pairwise: `0.00`
  - BOLD pairwise: `0.05`

Interpretation:
- The pipeline is functioning correctly.
- Recovery is weak because effective cross-node linear signal is weak under this operating regime, not because of a coding fault.

## Why This Is Meaningful for the White Paper
1. It creates a defensible stress-test baseline.
- Demonstrates that naive pairwise AR on BOLD can fail even with known planted regimes and moderate separation.
- This directly motivates the need for higher-order and latent-regime-aware inference.

2. It demonstrates scientific discipline.
- We do not convert weak recovery into a false claim.
- Diagnostics and tests explicitly gate interpretation.

3. It improves theorem-to-experiment alignment.
- Theoretical assumptions about identifiability/observability must be checked against simulator operating points.
- This run provides concrete evidence for adding explicit observability assumptions in theory sections.

## Robustness / Reproducibility Status
- Full script run passes:
  - baseline generation
  - switching robustness sweep
  - Wilson-Cowan pipeline
  - all unit tests
- Command: `bash scripts/run_phase0_checks.sh`

## Remaining Risks
1. Wilson-Cowan defaults are in a low-observability regime for structural support recovery.
2. Pairwise AR remains a weak proxy under hemodynamic convolution and nonlinear saturation.
3. This does not invalidate the project; it narrows what can be claimed from this baseline.

## Concrete Next Steps (Research-Grade)
1. Add a controlled parameter sweep for sigmoid derivative / effective off-diagonal magnitude and measure recovery transition.
2. Add deconvolution + latent-state models as stronger baselines (not just AR).
3. Move to Step 20 (static k=3 hypergraph reconstruction) with the same gate philosophy:
- deterministic artifacts
- explicit assumptions
- no overclaiming
