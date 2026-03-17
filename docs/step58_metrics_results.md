# Step 58 Results: Metrics Aggregation and Confidence Intervals

Date: 2026-03-12

## Artifact
1. `results/phase2_step58_metrics_50/metrics_summary.json`

## Structural Metrics (Selected Cells)
1. `k2_n20_t500_sigma0.10`: F1=0.3297, P=1.0000, R=0.2003.
2. `k2_n20_t2000_sigma0.10`: F1=0.8415, P=1.0000, R=0.7278.
3. `k3_n20_t500_sigma0.10`: F1=0.8073, P=1.0000, R=0.6771.
4. `k3_n20_t2000_sigma0.10`: F1=0.8695, P=1.0000, R=0.7693.
5. `k4_n20_t500_sigma0.10`: F1=0.3246, P=0.8494, R=0.2007.
6. `k4_n20_t2000_sigma0.10`: F1=0.7391, P=1.0000, R=0.5862.

## Switching Diagnostics (Step-58 Extension)
1. `t600_obs0.15`: regime-acc=0.6628, support-F1=0.4029, state-MSE=0.281476.
2. `t1200_obs0.15`: regime-acc=0.6547, support-F1=0.5427, state-MSE=0.280954.
3. `t600_obs0.30`: regime-acc=0.6536, support-F1=0.2381, state-MSE=0.349653.
4. `t1200_obs0.30`: regime-acc=0.5651, support-F1=0.3735, state-MSE=0.353393.

## Logic Check
1. Precision-heavy, recall-limited pattern appears in conservative sparse regimes (expected under strong regularization).
2. Higher-order recovery improves strongly with more samples (`T=500 -> 2000`) at fixed noise.
3. Switching regime-accuracy remains moderate and unstable under current reduced switching budget; treat as provisional.
