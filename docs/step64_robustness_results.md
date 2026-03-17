# Step 64 Results: Robustness Checks

Date: 2026-03-12  
Artifact: `results/phase2_step64_robustness/metrics_summary.json`

## Scenarios
1. Baseline (clean synthetic k=3).
2. Outlier contamination (2% heavy-response corruption).
3. Missing-data corruption (10% feature missingness + mean imputation).
4. Wrong-k stress (k=4 generation with restricted library as mismatch proxy).

## Key Metrics
1. Baseline support-F1: `0.8617`.
2. Outlier support-F1: `0.8483` (moderate degradation).
3. Missing-data support-F1: `0.8517` (moderate degradation).
4. Wrong-k restricted-library path degrades fit quality versus true-library path.

## Logic Check
1. Degradation is present but not catastrophic under moderate corruption.
2. Wrong-order specification measurably hurts recovery, consistent with model-misspecification expectations.
