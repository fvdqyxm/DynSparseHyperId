# Step 63 Results: Baseline Comparison

Date: 2026-03-12  
Artifact: `results/phase2_step63_baselines/metrics_summary.json`

## Baselines Included
1. Pairwise sparse LDS (`run_sparse_lds`) on k=2 dynamics.
2. Sparse high-order surrogate (current method path) on k=3/k=4 static data.
3. SINDy-like STLSQ baseline on same high-order feature library.
4. Pairwise-only ridge baseline on high-order-generated data.

## Key Outcomes
1. `k=3`: pairwise-only val-MSE exceeds sparse high-order by `+0.4661`.
2. `k=4`: pairwise-only val-MSE exceeds sparse high-order by `+2.1738`.
3. Sparse high-order also outperforms SINDy-like STLSQ in predictive MSE on both k=3 and k=4.

## Logic Check
1. Baseline direction is consistent with planted high-order generative structure.
2. This is still a limited-seed comparison and should be expanded with uncertainty bands before final claims.
