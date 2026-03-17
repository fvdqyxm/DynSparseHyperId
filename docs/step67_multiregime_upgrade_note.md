# Step 67 Extension: Multi-Regime Recovery Upgrade Checks

Date: 2026-03-12

## Why This Extension Was Added
The core remaining weakness is multi-regime (`K>=3`) recovery.
This extension tests whether stronger initialization plus anti-degeneracy sparse refit controls materially improve that regime.

## Added / Updated Artifacts
1. Upgrade runner:
   - `code/models/phase2_step67_multiregime_upgrade.py`
2. Initialization benchmark:
   - `code/models/phase2_step67_init_benchmark.py`
3. Core solver updates:
   - `code/models/phase0_baselines.py`
4. New outputs:
   - `results/phase2_step67_init_benchmark_v2/metrics_summary.json`
   - `results/phase2_step67_multiregime_upgrade_v2_tiny_fix_loglik/metrics_summary.json`
   - `results/phase2_step67_multiregime_upgrade_v2_fastcheck/metrics_summary.json`
   - `results/phase2_step67_multiregime_upgrade_v2_multiseed/metrics_summary.json`
5. Regression tests:
   - `tests/test_phase2_multiregime_upgrade.py`

## What Changed Technically
1. Added richer initialization strategies:
   - `local_ar_gmm_sticky`
   - `residual_gmm_sticky`
2. Added model-selection controls in soft-EM:
   - `selection_mode` (`loglik` / `bic` / `ebic`)
   - multi-scale sparse refit (`sparse_alpha_scales`)
3. Added anti-collapse guard:
   - detect all-zero recovered support;
   - rerun sparse refit with reduced regularization;
   - enforce minimum support cardinality during candidate selection.
4. Added diagnostics:
   - per-run support nonzero count (`support_nnz`) and summary deltas.

## Key Findings
1. Initialization benchmark (`init_benchmark_v2`):
   - best mean and robust strategy on this benchmark: `window_ar_cluster`.
   - `local_ar_gmm_sticky` is competitive and more stable than pure random starts.
2. Before anti-collapse guard:
   - upgraded regime metrics improved but support-F1 often degraded sharply or collapsed.
3. After anti-collapse guard (`v2_fastcheck`):
   - regime accuracy improves in all difficulty tiers.
   - transition-L1 improves strongly in all tiers.
   - support-F1 improves in medium and hard tiers; easy tier still declines.
4. Representative upgraded-minus-baseline deltas from `v2_fastcheck`:
   - easy: acc `+0.047`, F1 `-0.043`, transition-L1 `-0.399`
   - medium: acc `+0.067`, F1 `+0.119`, transition-L1 `-0.368`
   - hard: acc `+0.062`, F1 `+0.113`, transition-L1 `-0.443`
5. Representative upgraded-minus-baseline deltas from `v2_multiseed`:
   - easy: acc `+0.105`, F1 `+0.090`, transition-L1 `-0.179`
   - medium: acc `+0.045`, F1 `-0.002`, transition-L1 `-0.202`
   - hard: acc `+0.037`, F1 `+0.076`, transition-L1 `-0.262`

## Logic Check
1. No overclaim: this is not a universal fix for `K>=3`.
2. Improvement is configuration-dependent; medium-tier support remains near-neutral in the stronger multiseed run.
3. The upgrade is meaningful because it removes a concrete failure mode (zero-support collapse) and yields simultaneous accuracy+support gains in multiple tiers, which was absent in earlier runs.
4. This supports a stronger whitepaper narrative: the bottleneck is now narrower (calibration and regime-specific regularization), not complete method failure.
