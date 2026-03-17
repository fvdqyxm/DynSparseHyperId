# DynSparseHyperId

Identifiability and Sample Complexity for Sparse High-Order Latent Dynamical Hypergraphs.

## Core Idea Summary
Recover sparse, high-order (`k >= 3`) interaction structure and latent regime dynamics from noisy time-series data.  
Primary setting: latent Markov regime switching + sparse high-order operators + finite-sample inverse recovery.

## Current Project Status (March 12, 2026)
1. Phase 0: Completed.
2. Phase 1: Completed with contingency (restricted-class theorem closure; unrestricted strongest version explicitly open).
3. Phase 2: Completed with contingency (expanded synthetic coverage + transparent hard-regime negative results).
4. Phase 3: Blocked by external real-dataset availability (pipelines implemented and blocked-safe).
5. Phase 4: Completed for in-repo deliverables; external steps (mentor feedback and submission) remain blocked.

Trackers:
1. `tracking/phase0_steps.csv`
2. `tracking/phase1_steps.csv`
3. `tracking/phase2_steps.csv`
4. `tracking/phase3_steps.csv`
5. `tracking/phase4_steps.csv`

## Reproducibility Commands
1. Run tests:
```bash
venv/bin/python -m unittest tests/test_phase0_steps.py -v
```
2. Run schema/logic audit:
```bash
venv/bin/python code/models/schema_logic_audit.py
```
3. Build interim LaTeX PDF:
```bash
cd proofs/latex
pdflatex -interaction=nonstopmode -halt-on-error master.tex
pdflatex -interaction=nonstopmode -halt-on-error master.tex
```

## Key Artifacts
1. Phase 2 large multi-seed metrics: `results/phase2_step58_metrics_50/metrics_summary.json`
2. Scaling laws: `results/phase2_step59_scaling_50/metrics_summary.json`
3. Step-56 expanded grid (`T` up to 5000): `results/phase2_step56_large_grid/metrics_summary.json`
4. Step-56 explicit `K=3..5` sweep: `results/phase2_step56_switching_k_grid_full/metrics_summary.json`
5. Gate 2 assessment: `docs/step67_viability_gate2_assessment.md`
6. Multi-regime tradeoff analysis: `docs/step67_refit_tradeoff_analysis.md`
7. Multi-regime v2 anti-collapse artifacts: `results/phase2_step67_multiregime_upgrade_v2_fastcheck/metrics_summary.json` and `results/phase2_step67_multiregime_upgrade_v2_multiseed/metrics_summary.json`
8. Deep viability review: `docs/deep_viability_review_2026_03_12.md`
9. Active-issue exhaustive review note: `docs/exhaustive_review_active_issues_2026_03_12.md`
10. Phase 3 dataset contract: `docs/phase3_dataset_requirements.md`

## Repository Layout
1. `code/models/`: simulation, inference, audits, and phase scripts.
2. `results/`: generated metrics and plots.
3. `docs/`: step notes, gate assessments, and white-paper logs.
4. `proofs/latex/`: manuscript and theorem draft.
5. `tracking/`: execution status trackers.
