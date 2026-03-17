# Step 59 Results: Scaling Laws (Log-Log)

Date: 2026-03-12

## Artifact
1. `results/phase2_step59_scaling_50/metrics_summary.json`
2. `results/phase2_step59_scaling_50/structural_scaling_loglog.png`
3. `results/phase2_step59_scaling_50/switching_regime_scaling_loglog.png`

## Structural Slopes (Selected)
1. `k2_n20_sigma0.10`: slope `-1.0402`.
2. `k2_n80_sigma0.10`: slope `-0.9218`.
3. `k2_n150_sigma0.10`: slope `-0.8720`.
4. `k3_n20_sigma0.10`: slope `-0.2809`.
5. `k4_n20_sigma0.10`: slope `-0.6862`.

## Switching Slopes
1. `obs0.15`: regime-error slope `+0.0341`, state-MSE slope `-0.0027`.
2. `obs0.30`: regime-error slope `+0.3284`, state-MSE slope `+0.0154`.

## Logic Check
1. Structural slopes are now directionally coherent after removing solver-mode confounding.
2. Switching slopes are still weak/unstable with current 2-seed reduced-budget diagnostics; do not over-interpret.
3. Next reliability target: increase switching seeds and include additional `T` points before claiming switching scaling behavior.
