# Step 67 Viability Gate 2 Assessment (Final Decision)

Date: 2026-03-12

## Gate Criterion
1. Support F1 > 0.75 in realistic noise settings.
2. >20% lift versus pairwise baselines.

## Evidence Used
1. `results/phase2_step57_multiseed_50/metrics_summary.json`
2. `results/phase2_step58_metrics_50/metrics_summary.json`
3. `results/phase2_step59_scaling_50/metrics_summary.json`
4. `results/phase2_step63_baselines/metrics_summary.json`
5. `results/phase2_step60_62_ablations/metrics_summary.json`

## Final Status
1. **Completed with contingency triggered**.

## What Passes
1. High-order vs pairwise predictive lift is strong in planted k=3/k=4 settings (Step 62/63).
2. 50-seed evidence is available across 36 structural cells; many higher-`T` cells exceed F1 0.75.
3. Pairwise-lift condition (>20%) is satisfied in Step 63:
   - k3 relative MSE lift vs pairwise: ~78%,
   - k4 relative MSE lift vs pairwise: ~85%.
4. Structural Step-56 coverage now includes explicit `T=5000` cells:
   - `results/phase2_step56_large_grid/metrics_summary.json` has `54/54` executed cells over `T={500,2000,5000}`.

## What Does Not Pass Unconditionally
1. Low-`T` high-order cells (especially `k=4`, `T=500`) remain below 0.75 F1 in 50-seed aggregate.
2. The strict universal criterion "all realistic-noise cells F1>0.75" is not satisfied.
3. New explicit `K=3..5` switching sweep (Step-56 supplement) is weak under current baseline:
   - `results/phase2_step56_switching_k_grid_full/metrics_summary.json`
   - stress check confirms weakness is not fixed by heavier optimization.

## Contingency Decision (Executed)
1. Triggered contingency path from plan: treat this as a theory-first / scope-limited empirical paper, not a broad universal empirical claim.
2. Keep strong claims to:
   - identifiable theory scaffolding + sample-complexity program,
   - robust high-order lift vs pairwise baselines in planted settings,
   - explicit negative results for multi-regime (`K>=3`) recovery under current inference stack.
3. Record Gate 2 as closed operationally, with contingency clearly stated in tracker and manuscript notes.

## Post-Closure Extension (Method Strengthening Check)
1. Added direct multi-regime strengthening experiments:
   - `results/phase2_step67_init_benchmark/metrics_summary.json`
   - `results/phase2_step67_multiregime_upgrade_quick2/metrics_summary.json`
   - notes: `docs/step67_multiregime_upgrade_note.md`
2. Observed pattern:
   - improved regime-assignment/transition quality with upgraded schedule,
   - support-F1 behavior depends on refit mode:
     - stability-refit mode tends to reduce support-F1,
     - no-stability mode can improve support-F1 but with weaker accuracy gains.
3. Interpretation:
   - this supports the contingency framing: current bottleneck is sparse support refit under multi-regime assignments, not only initialization.
