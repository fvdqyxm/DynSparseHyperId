# Steps 60-62 Results: Ablation Suite

Date: 2026-03-12  
Artifact: `results/phase2_step60_62_ablations/metrics_summary.json`

## Step 60 (Sparsity Ablation, lambda=0 Dense Fit)
1. `k=3`: sparse val-MSE `0.1351` vs dense val-MSE `0.1509` (sparse better by `0.0158`).
2. `k=4`: sparse val-MSE `0.4937` vs dense val-MSE `2.3072` (sparse better by `1.8135`).
3. Interpretation: removing sparsity strongly hurts predictive generalization in higher-order regimes.

## Step 61 (Regime Ablation: Switching vs Single-Regime)
1. Switching regime accuracy: `0.7641`.
2. Single-regime accuracy proxy (majority-class): `0.5518`.
3. Switching state-MSE: `0.2787`; single-regime state-MSE: `0.2793`.
4. Interpretation: clear regime-identification lift; MSE gain is present but small in this single-seed run.

## Step 62 (High-Order vs Pairwise-Only)
1. `k_true=3`: high-order val-MSE `0.1365` vs pairwise-only `0.6856` (gain `0.5490`).
2. `k_true=4`: high-order val-MSE `0.4656` vs pairwise-only `2.5859` (gain `2.1203`).
3. Interpretation: pairwise-only models underfit planted high-order dynamics substantially.

## Logic Check
1. Ablation directions are consistent with the project thesis.
2. Current ablations are single-seed and should be expanded to multi-seed before venue-level claims.
