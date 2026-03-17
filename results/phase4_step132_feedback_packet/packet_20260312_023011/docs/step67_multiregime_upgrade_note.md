# Step 67 Extension: Multi-Regime Recovery Upgrade Checks

Date: 2026-03-12

## Why This Extension Was Added
The core remaining weakness is multi-regime (`K>=3`) recovery.  
This extension tests whether stronger initialization and inference schedules materially improve that regime.

## Added Artifacts
1. Upgraded comparison runner:
   - `code/models/phase2_step67_multiregime_upgrade.py`
2. Fast initialization benchmark:
   - `code/models/phase2_step67_init_benchmark.py`
3. Executed outputs:
   - `results/phase2_step67_multiregime_upgrade_quick2/metrics_summary.json`
   - `results/phase2_step67_multiregime_upgrade_quick3/metrics_summary.json`
   - `results/phase2_step67_multiregime_upgrade_multiseed/metrics_summary.json`
   - `results/phase2_step67_multiregime_upgrade_fastmultiseed/metrics_summary.json`
   - `results/phase2_step67_multiregime_upgrade_fastmultiseed_nostability/metrics_summary.json`
   - `results/phase2_step67_init_benchmark/metrics_summary.json`
4. Tradeoff memo:
   - `docs/step67_refit_tradeoff_analysis.md`

## Key Findings
1. **Initialization quality improves with structured local methods**:
   - init benchmark robust scores (mean - 0.5*std) ranked:
     - `local_ar_gmm`: `0.4248`,
     - `random_blocks`: `0.4086`,
     - `window_ar_cluster`: `0.3977`.
2. **Upgraded inference tradeoff appears** (quick + multi-seed runs):
   - with stability-refit upgrade: regime accuracy and transition quality improve, support-F1 often drops.
   - with no-stability variant: support-F1 improves vs baseline, while regime-accuracy gains are weaker/flat.
3. Representative multi-seed summaries:
   - stability-refit fast multi-seed:
     - baseline: acc `0.3592`, F1 `0.0882`, transition-L1 `0.4324`
     - upgraded: acc `0.3689`, F1 `0.0656`, transition-L1 `0.3340`
   - no-stability fast multi-seed:
     - baseline: acc `0.3592`, F1 `0.0882`, transition-L1 `0.4324`
     - upgraded: acc `0.3567`, F1 `0.1122`, transition-L1 `0.4199`
4. Interpretation:
   - better latent-state partitioning does not automatically translate to better sparse support recovery under the current sparse-refit stage.

## Logic Check
1. No overclaim: this is not presented as a solved `K>=3` recovery fix.
2. The extension identifies a concrete bottleneck split:
   - latent-state decoding vs sparse-operator support estimation.
3. Next algorithmic target is now clearer:
   - adaptive refit policy that switches between regime-focused and support-focused modes by objective.
