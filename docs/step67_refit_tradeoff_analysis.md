# Step 67: Refit Tradeoff Analysis (`K=3` Multi-Seed)

Date: 2026-03-12

## Objective
Evaluate whether the post-assignment refit choice is the core bottleneck for multi-regime support recovery.

## Compared Configurations
1. Baseline soft-EM + hard sparse refit.
2. Upgraded init/schedule + stability refit.
3. Upgraded init/schedule + **no** stability refit.

## Artifacts
1. Stability-refit multi-seed:
   - `results/phase2_step67_multiregime_upgrade_fastmultiseed/metrics_summary.json`
2. No-stability multi-seed:
   - `results/phase2_step67_multiregime_upgrade_fastmultiseed_nostability/metrics_summary.json`
3. Additional stronger stability run:
   - `results/phase2_step67_multiregime_upgrade_multiseed/metrics_summary.json`

## Aggregate Findings
1. **Upgraded + stability refit**:
   - regime accuracy improves,
   - transition error improves strongly,
   - support-F1 decreases on average.
2. **Upgraded + no stability refit**:
   - support-F1 improves versus baseline,
   - transition error improves modestly,
   - regime accuracy is flat/slightly lower.

## Interpretation
1. Refit choice controls the primary tradeoff:
   - stability refit favors cleaner regime-transition estimates,
   - non-stability refit preserves or improves sparse support recovery.
2. This is a real multi-objective frontier, not a single scalar "best" mode.

## Claim-Safe Conclusion
1. The project now has a tested mechanism to tune for:
   - regime-tracking quality (`use_stability_refit=True`),
   - support-recovery quality (`use_stability_refit=False`).
2. This should be reported as an explicit methodological tradeoff in the white paper.
