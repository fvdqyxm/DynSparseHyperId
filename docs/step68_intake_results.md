# Step 68 Progress: rs-fMRI Intake Preflight

Date: 2026-03-12  
Artifact: `code/models/phase3_step68_data_intake.py`

## What Was Implemented
1. BIDS-style subject discovery (`sub-*`).
2. Per-subject manifest fields for:
   - rest BOLD path,
   - confounds path,
   - atlas-timeseries path.
3. Label-file presence check.
4. Explicit blocked-state reporting when data is unavailable.

## Current Run Result
1. Output: `results/phase3_step68_intake/metrics_summary.json`.
2. Status: `blocked_missing_data_root`.
3. Blocking reason: local path `data/real/marijuana_323` not found.

## Logic Check
1. Step-68 now fails loudly and structurally (not silently) when the local dataset is absent.
2. Once dataset is mounted locally, the script will auto-generate a manifest and readiness counts for Step 69.
