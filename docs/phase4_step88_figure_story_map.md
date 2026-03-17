# Phase 4 Step 88: Figure-Story Map

Date: 2026-03-12

## Figure-to-Claim Alignment
1. Structural recovery scaling:
   - `results/phase2_step59_scaling_50/structural_scaling_loglog.png`
   - claim: support error decreases with sample size across `k=2,3,4` synthetic settings.
2. Baseline lift:
   - `results/phase2_step63_baselines/metrics_summary.json`
   - claim: high-order model improves predictive performance over pairwise baseline in planted high-order settings.
3. Robustness/failure boundaries:
   - `results/phase2_step64_robustness/metrics_summary.json`
   - claim: known degradation under outliers/missing data/wrong-order assumptions is quantified.
4. Step-56 expanded coverage:
   - `results/phase2_step56_large_grid/metrics_summary.json`
   - claim: explicit `T=5000` structural coverage included.
5. Multi-regime hard setting:
   - `results/phase2_step56_switching_k_grid_full/metrics_summary.json`
   - claim: `K>=3` switching recovery remains hard under current pipeline (negative-result transparency).

## Logic Check
1. Every major claim has at least one direct artifact.
2. No figure is assigned to a stronger claim than the artifact supports.
3. Neuroscience illustration figures remain blocked pending local real-data availability.
