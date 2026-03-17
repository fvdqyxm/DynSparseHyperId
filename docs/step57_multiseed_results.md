# Step 57 Results: Multi-Seed Expansion (Current Stage)

Date: 2026-03-12

## Artifact
1. `results/phase2_step57_multiseed_50/metrics_summary.json`

## Configuration
1. `N={20,80,150}`, `k={2,3,4}`, `T={500,2000}`, `sigma={0.1,1.0}`, `seeds=50`.
2. Total requested runs: 1800.
3. Total executed: 1800.
4. Total skipped: 0.

## Logic Check
1. Solver-confound removed for scaling analysis by forcing consistent solver mode (`lasso_scaled`) across all cells.
2. This is intentionally conservative and lowers low-sample support sensitivity relative to CV-tuned fits.

## Status
1. Step 57 seed-budget target is now met at the lower bound (50 seeds/cell for this grid).
2. Remaining expansion concerns are coverage breadth (additional `T`, regime settings), not seed count.
