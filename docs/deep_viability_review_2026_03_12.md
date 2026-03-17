# Deep Viability Review (Research Logic Audit)

Date: 2026-03-12

## Executive Verdict
1. Research direction is viable and nontrivial.
2. Project is now internally coherent for a theory-first submission path under explicit scope limits.

## High-Severity Findings (Current)
1. **Universal empirical recovery claim is still false**:
   - Even after expanded Step-56 evidence, some hard cells remain below F1 0.75.
   - Explicit `K>=3` switching sweep is weak under current pipeline (`results/phase2_step56_switching_k_grid_full/metrics_summary.json`).
2. **Real-data illustration cannot be executed locally**:
   - Phase 3 remains blocked by missing local dataset mounts.

## Medium-Severity Findings
1. **Switching diagnostics are still seed-limited for confident uncertainty quantification**:
   - Hard `K>=3` settings need larger seed budgets for stable confidence intervals.
2. **Theory closure is reframed**:
   - Closed for an explicit restricted class; unrestricted strongest theorem remains open by design.

## Low-Severity Findings
1. **Step 65 tuning is proxy-based, not full joint tuning**:
   - Appropriate as an interim decision aid; should remain labeled as proxy in manuscript text.

## Logic Integrity Checks Passed
1. Confound control:
   - solver-policy confound in scaling analysis was detected and corrected via consistent solver rerun.
2. Reproducibility:
   - Tests and schema audits remain passing after changes.
3. Failure transparency:
   - failure modes are now explicitly documented with triggers and mitigations.
4. No-threshold-cheating check:
   - weak `K>=3` results are reported directly, including stress runs with stronger optimization budgets.

## Immediate Priority Order
1. Increase multi-regime switching seed budgets (`K>=3`) and test improved inference families.
2. Keep manuscript claims locked to restricted-class theorem + synthetic evidence boundaries.
3. Resume Phase 3 immediately when local real-data mounts are available.
