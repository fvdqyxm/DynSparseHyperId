# Phase 3 Steps 69-76 Progress (Real-Data Block + Mock-Validated Pipeline)

Date: 2026-03-12

## Implemented Pipelines
1. Step 69: `code/models/phase3_step69_sliding_windows.py`
2. Step 70: `code/models/phase3_step70_motif_inference.py`
3. Step 71: `code/models/phase3_step71_predict_craving.py`
4. Step 72: `code/models/phase3_step72_baseline_compare.py`
5. Step 73: `code/models/phase3_step73_visualize_motifs.py`
6. Step 74: `code/models/phase3_step74_cross_dataset_preflight.py`
7. Step 75: `code/models/phase3_step75_neuro_ablation.py`
8. Step 76: `code/models/phase3_step76_gate3_assessment.py`

## Critical Fix Applied
1. Step 72 previously used a static baseline proxy (`ok_proxy`), which was methodologically weak.
2. Step 72 now computes real cross-validated static baselines from Step-70 static features:
   - `static_ridge`
   - `static_pca_ridge`
   - `intercept_only`
3. Dynamic model is now compared against the best static baseline with explicit metric:
   - `relative_mse_lift_vs_best_static`.

## Real-Data Status (Still Blocked)
1. Local real roots remain unavailable:
   - `data/real/marijuana_323`
   - `data/real/abcd_sud_subset`
2. Therefore tracker remains blocked for Phase-3 completion claims.

## Mock End-to-End Validation Status
Source: `results/phase3_mock_replay/metrics_summary.json`

1. Step 68: `ready_for_step69`
2. Step 69: `ready_for_step70`
3. Step 70: `ok`
4. Step 71: `ok`
5. Step 72: `ok` (real static baseline comparison, no proxy)
6. Step 73: `ok`
7. Step 74: `ready`
8. Step 75: `ok`
9. Step 76: `provisional_pass`

## Logic Check
1. The Phase-3 software stack is operational and validated on mock BIDS-like inputs.
2. Blocking condition is now strictly external data availability, not missing or fragile code paths.
3. Claims remain conservative: real-data scientific conclusions are not asserted from mock replay.
