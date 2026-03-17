# Phase 3 Dataset Contract (No-Sloppy Version)

Date: 2026-03-12

## What We Need Mounted Locally
1. Primary dataset root:
   - `data/real/marijuana_323`
2. Cross-dataset validation root:
   - `data/real/abcd_sud_subset`

## Required Structure for Primary Root
For each subject `sub-XXXX`, the following paths must exist:
1. `data/real/marijuana_323/sub-XXXX/func/*task-rest*desc-preproc_bold.nii.gz`
2. `data/real/marijuana_323/sub-XXXX/func/*desc-confounds_timeseries.tsv`
3. `data/real/marijuana_323/sub-XXXX/func/*Yeo*17*timeseries*.tsv`

Required labels file:
1. `data/real/marijuana_323/phenotypes/craving_labels.csv`

## Required Label Schema
`craving_labels.csv` must include:
1. one subject column: `subject_id` (or `participant_id`),
2. either:
   - direct variance target: `craving_var` (preferred), or
   - repeated columns `craving_*` from which variance can be computed.

## Minimum Data Sufficiency
1. Step 70 requires at least 5 subjects with both windows and labels.
2. Step 71/72/75 require at least 5 subjects for cross-validated estimates.
3. Recommended for stable inference: >= 50 subjects after QC.

## Why These Specific Datasets
1. We need resting-state fMRI with subject-level behavioral phenotype (craving instability or close proxy) to support Steps 70-72.
2. We need a second cohort for Step 74 cross-dataset sanity checks.
3. Generic healthcare tables without fMRI time-series and phenotype linkage are insufficient for this pipeline.

## Candidate Sources
From your provided list (`awesome-healthcare-datasets`), neuroimaging-relevant entries include:
1. INDI (1000 Functional Connectomes),
2. Human Connectome Project (HCP),
3. UK Biobank (imaging subset).

Source: [awesome-healthcare-datasets](https://github.com/geniusrise/awesome-healthcare-datasets)

## Acceptance Commands (Hard Gate)
After mounting data, run:

```bash
./scripts/run_phase3_on_data_mount.sh
```

Success means:
1. `results/phase3_step68_intake/metrics_summary.json` has `status=ready_for_step69` or `partial_ready` with acceptable missingness.
2. `results/phase3_step70_motifs/metrics_summary.json` has `status=ok`.
3. `results/phase3_step71_prediction/metrics_summary.json` has `status=ok`.
4. `results/phase3_step72_baseline_compare/metrics_summary.json` has `status=ok` (real static baseline; no proxy).
5. `results/phase3_step76_gate3/metrics_summary.json` is not data-blocked.
