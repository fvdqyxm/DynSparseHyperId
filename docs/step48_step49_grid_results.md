# Steps 48-49 Results: Small Synthetic Grid and Recovery Curves

Date: 2026-03-12
Artifacts:
- `code/models/step48_small_synthetic_grid.py`
- `code/models/step49_plot_recovery_curves.py`
- `results/phase1_step48_grid/metrics_summary.json`
- `results/phase1_step48_grid/k2_grid_f1.png`
- `results/phase1_step48_grid/k3_grid_f1.png`
- `results/phase1_step49_curves/f1_vs_t_over_n.png`

## Grid Executed
1. k=2 sparse LDS:
   - N = 20, 35, 50
   - T = 500, 1000, 2000
2. k=3 static surrogate:
   - N = 20
   - T = 500, 1000, 2000

## Main Observations
1. k=2 support F1 is high and generally improves with larger T in this compact grid.
2. k=3 support F1 is stable in the high-0.8 range, with weak non-monotone variation across T in this single-seed run.
3. F1 vs T/N curves are now available for reporting and follow-up slope analysis.

## Logic Check
1. This is a compact computational sweep (1 seed) for pipeline continuity, not a final statistical scaling study.
2. For publication-grade scaling laws, repeat with multi-seed confidence intervals and harder regimes to avoid saturation effects.
