# Step 44 Results: Heavy-Tailed / Contaminated Noise Robustness

Date: 2026-03-12
Artifacts:
- `results/phase1_step44_noise_robustness/metrics_summary.json`
- `results/phase1_step44_noise_robustness/noise_model_robustness.png`
- `code/models/step44_heavy_tail_robustness.py`

## Setup
Switching-LDS benchmark with identical structural parameters, varying observation noise model:
1. Gaussian
2. Student-t (df=3)
3. Contaminated Gaussian (2% outliers, 6x scale)

(3 seeds, N=10, T=1400, obs noise sigma=0.15)

## Main Findings
1. Gaussian baseline:
   - support F1 mean: 0.889
   - regime accuracy mean: 0.866
2. Student-t:
   - support F1 mean: 0.821 (drop 0.068)
   - regime accuracy mean: 0.818 (drop 0.048)
3. Contaminated:
   - support F1 mean: 0.829 (drop 0.061)
   - regime accuracy mean: 0.811 (drop 0.055)

## Interpretation
1. Recovery degrades under heavy-tailed and contaminated noise, as expected.
2. Performance remains materially above random, indicating baseline robustness but not invariance.
3. This supports claim-safe wording: current estimator is moderately robust, with clear room for robustified inference (Huber/trimmed objectives, heavy-tail concentration adjustments).

## Fundamental Upgrade Added
`run_switching_lds` now supports explicit `obs_noise_model` options (`gaussian`, `student_t`, `contaminated`) to prevent robustness claims from relying on Gaussian-only simulations.
