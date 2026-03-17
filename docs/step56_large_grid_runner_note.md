# Step 56 Progress Note: Large Grid Runner (Finalized)

Date: 2026-03-12  
Artifact: `code/models/phase2_large_grid_runner.py`

## What Changed Fundamentally
1. Removed the old `k>=4` skip-path by adding a generic `k`-order surrogate module:
   - `code/models/static_hypergraph_korder.py`
2. Added adaptive complexity controls to avoid silent computational collapse:
   - feature-capped high-order dictionaries (`--max-features-khigh`),
   - target-subsample controls (`--max-targets-khigh`),
   - solver switch logging (`lasso_cv` vs `lasso_scaled`) for auditability.
3. Added pairwise (`k=2`) complexity controls so solver choice is explicit and comparable across runs.

## Current Coverage
1. Structural grid now includes `N=20,80,150`, `k=2,3,4`, `T=500,2000,5000`, `sigma=0.1,1.0`.
2. Canonical merged structural artifact:
   - `results/phase2_step56_large_grid/metrics_summary.json`
3. Structural execution status:
   - requested: 54
   - executed: 54
   - skipped: 0
4. Supplementary explicit regime-count sweep (`K=3,4,5`) is now present:
   - runner: `code/models/phase2_step56_switching_k_grid.py`
   - artifact: `results/phase2_step56_switching_k_grid_full/metrics_summary.json`
   - requested/executed: `18/18` (no runtime failures)

## Logic Checks
1. No unsupported order omissions remain in Step-56 output.
2. Solver mode is recorded per run to prevent hidden confounds in scaling analysis.
3. `T=5000` coverage is now explicitly present in structural grid.
4. The `K=3..5` sweep exposes a real difficulty: naive switching recovery under many regimes remains weak even at large `T` (stress test included in `results/phase2_step56_switching_k_grid_stress_k3/metrics_summary.json`).
5. This is treated as a substantive scientific finding, not patched away by threshold tuning.
