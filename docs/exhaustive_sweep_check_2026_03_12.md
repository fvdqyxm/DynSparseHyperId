# Exhaustive Sweep Check (2026-03-12)

## Objective
Stress-test Step 15 switching LDS recovery under varying observation noise with repeated seeds,
and explicitly verify we are not relying on one-seed artifacts.

## Critical Logic Fixes Before Sweep
1. Fixed regime/trajectory burn-in alignment bug in switching simulator.
2. Fixed noise-sweep validity issue:
   - process-noise scaling alone can be scale-equivariant,
   - added independent observation noise to make robustness sweeps meaningful.
3. Added beta-min edge generation in dynamics (`min_abs_weight`) to match identifiability assumptions.
4. Added stability-selection support recovery to reduce false positives.

## Methods Compared
1. `hard_em`
2. `hard_em_stability`
3. `soft_em_hmm` (sticky transitions + annealed emissions + multi-start init)
4. `soft_em_hmm_stability`
5. `oracle_labels_ceiling`
6. `oracle_labels_ceiling_stability`

## Sweep Configuration
- Script: `code/models/phase0_switching_sweep.py`
- Results: `results/phase0_switching_sweep/sweep_metrics.json`
- Settings:
  - `N=10`, `T=1400`, `sparsity=0.1`, process `sigma=0.5`
  - observation noise in `{0.00, 0.15, 0.30}`
  - 3 seeds (`31, 32, 33`)
  - stability bootstrap runs: 8

## Aggregate Results (Selected Method)
1. Obs noise 0.00:
   - regime accuracy mean: 0.813
   - support F1 mean: 0.815
2. Obs noise 0.15 (moderate):
   - regime accuracy mean: 0.816
   - support F1 mean: 0.791
3. Obs noise 0.30 (hard):
   - regime accuracy mean: 0.778
   - support F1 mean: 0.706

## Interpretation
1. The method is robust at low/moderate observation noise and degrades at harder noise levels.
2. This is scientifically credible behavior, not suspiciously flat performance.
3. The gap to oracle increases with noise, indicating remaining algorithmic headroom.

## Decision
Step 15 is now marked **Completed** for moderate-noise criteria, with explicit limits documented.

## Next Research-Level Upgrades
1. Recurrent transition gating (rSLDS-style transition dependence on state features).
2. Duration-aware switching (HSMM-style dwell modeling).
3. Broader sweep grid over `N, T, obs_noise, transition persistence, separation`.
