# Step 56 Supplement: Explicit Regime-Count Sweep (`K=3..5`)

Date: 2026-03-12

## Why This Supplement Was Added
Step 56 originally covered structural scaling (`N,k,T,\sigma`) but did not explicitly instantiate latent-regime count `K=3..5`.  
To close that gap, we added a dedicated switching-LDS sweep:

1. Script: `code/models/phase2_step56_switching_k_grid.py`
2. Main artifact: `results/phase2_step56_switching_k_grid_full/metrics_summary.json`
3. Stress-check artifact: `results/phase2_step56_switching_k_grid_stress_k3/metrics_summary.json`

## Executed Coverage
1. Main sweep:
   - `K={3,4,5}`, `T={500,2000,5000}`, observation noise `{0.1,1.0}`, 1 seed/cell.
   - Requested/executed/failed: `18/18/0`.
2. Stress check:
   - hard cell `K=3, T=5000, obs=0.1` with stronger optimization budget (24 EM iterations, 8 restarts).
   - Requested/executed/failed: `1/1/0`.

## Result Summary (Key Finding)
1. Structural Step-56 runs scale well with high support recovery for many `k<=4` cells, especially at `T=5000`.
2. Switching `K>=3` recovery is currently weak under this baseline pipeline:
   - regime accuracy is far below 0.75 across tested cells,
   - support F1 also remains below 0.75 in these multi-regime settings.
3. Stress-test optimization did not resolve this gap, indicating a likely fundamental difficulty (identifiability/optimization hardness), not merely poor hyperparameter tuning.

## Logic Check
1. We did not "fix" the weak cells by changing success thresholds.
2. We added stronger optimization checks to test whether performance was artifactually low.
3. The weakness persists, so the honest conclusion is that the current algorithmic stack is not yet sufficient for robust `K>=3` switching recovery in this setup.

## Consequence for Gate Decisions
1. Step 56 is complete with full requested-axis coverage evidence.
2. Gate 2 should be treated as a conditional pass with contingency (theory/scope-first positioning), not an unconditional empirical victory.
