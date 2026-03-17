# Step 43 Results: Small Numerical Tightness Check

Date: 2026-03-12
Artifacts:
- `results/phase1_step43_tightness/metrics_summary.json`
- `results/phase1_step43_tightness/step43_f1_vs_t.png`
- `results/phase1_step43_tightness/step43_loglog_error_vs_t.png`

## Configuration
- T grid: 600, 900, 1200, 1600
- Seeds: 141, 142, 143
- Switching setting: N=10, obs noise=0.15
- k=3 setting: N=10, noise sigma=0.25

## Main Numerical Findings
1. Switching recovery improves with T:
   - mean support F1 rises from 0.452 (T=600) to 0.739 (T=1600).
   - log-log slope of error (1-F1) vs T: **-0.736**.
2. k=3 recovery is already high and near saturation:
   - mean support F1 around 0.90 across all T.
   - log-log slope of error: **-0.077** (weak because error floor dominates at this noise/model scale).

## Tightness Logic Check
1. Switching slope is in the expected negative direction and close to the theoretical high-level trend (error decreases with T).
2. k=3 slope is weakly negative due to plateau behavior; this does not contradict theory, but indicates current regime is not informative for slope estimation.
3. Conclusion: Step 43 supports the upper-bound trend qualitatively for switching; additional harder k=3 regimes are needed for informative slope diagnostics.

## Next Rigorous Upgrade
1. Add harder k=3 settings (higher noise, lower beta-min, lower T) to avoid saturation.
2. Report confidence intervals for slopes via seed bootstrap.
3. Compare observed slopes against both Step-41 upper and Step-42 lower template exponents.
