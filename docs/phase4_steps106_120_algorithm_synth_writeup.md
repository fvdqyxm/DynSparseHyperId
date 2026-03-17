# Phase 4 Steps 106-120: Algorithm and Synthetic Results Draft

Date: 2026-03-12

## Algorithm Section Drafted
1. Amortized regime encoder, hypergraph emission, proximal sparsity, and temporal smoothness modules documented.
2. Training and curriculum details included with explicit caveats where gains are mixed.

## Synthetic Section Drafted
1. Large-grid synthetic infrastructure now includes k=2/3/4 and 50-seed aggregate runs.
2. Metrics include support precision/recall/F1, state-MSE (where applicable), and scaling-law summaries.
3. Ablations and baselines are integrated:
   - sparsity on/off,
   - switching vs single-regime,
   - high-order vs pairwise,
   - SINDy-like baseline.

## Claim Boundary
1. Structural gains are robust in many cells and baseline lift is strong.
2. Gate 2 remains open because F1>0.75 is not universal across all hard low-T cells.
