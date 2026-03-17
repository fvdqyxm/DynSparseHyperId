# DynSparseHyperId

Identifiability and sample complexity for sparse high-order latent dynamical hypergraphs.

## What it is

A personal research project exploring whether you can recover sparse, higher-order interaction structure (triplets and above) from noisy time-series data when the system switches between hidden regimes. The application I had in mind was resting-state fMRI and craving instability — brain systems that don't sit in a single static connectivity pattern but switch between states over time.

The core question: under what conditions is this inverse problem solvable, and how much data do you actually need?

## What's been built

- Sparse graphical model baseline (Graphical Lasso) with support recovery metrics
- EM-style regime inference with Viterbi and forward-backward decoding
- L1-regularized sparse operator recovery
- Multi-restart model selection with anti-collapse controls
- 1,800+ reproducible synthetic experiments across network sizes (N ∈ {20, 80, 150}), regime counts (k ∈ {2,3,4}), time horizons (T ∈ {500, 2000, 5000}), and noise levels
- Full real-data pipeline (intake through motif inference and gate assessment) — validated on mock data, blocked on clinical dataset access
- LaTeX manuscript draft in `proofs/latex/`

## Current status (March 2026)

| Phase | Status |
|-------|--------|
| Phase 0: Foundations | Complete |
| Phase 1: Theory | Complete with contingency — restricted-class closure proved, unrestricted strongest version open |
| Phase 2: Synthetic experiments | Complete with contingency — strong results in planted settings, hard multi-regime cases documented honestly |
| Phase 3: Real data | Blocked — pipeline built and tested on mock data, waiting on dataset access |
| Phase 4: Writeup | In-repo deliverables complete |

## Findings

Higher-order (k≥3) models outperform pairwise baselines in synthetic settings where higher-order structure is planted. Multi-regime recovery (K≥3) improved after initialization and anti-collapse upgrades but didn't hold universally — that's documented rather than tuned away.

An earlier version had an improperly cross-validated static baseline comparison. That was caught mid-project, corrected, and results were rerun.

## Reproducing results

```bash
# Run tests
python -m unittest tests/test_phase0_steps.py -v

# Schema/logic audit
python code/models/schema_logic_audit.py

# Build manuscript
cd proofs/latex
pdflatex master.tex && pdflatex master.tex
```

Key results in `results/` — see `results/phase2_step58_metrics_50/metrics_summary.json` for the 50-seed expansion and `results/phase2_step56_large_grid/` for the T=5000 grid.

## Layout

```
code/models/        inference, simulation, audit scripts
data/               synthetic data and mock real-data
proofs/latex/       manuscript and theorem drafts
results/            experiment metrics and plots
tracking/           phase execution status
literature/         paper summaries
```

## Notes

This is a personal project. The theory is preliminary and the real-data stage is pending. The goal was to build something rigorous enough to eventually publish — hence the phase trackers, audit scripts, and explicit documentation of failure modes alongside successes.
