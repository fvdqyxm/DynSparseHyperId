# Step 47 Contingency Note: Nonconvex Convergence Hardness

Date: 2026-03-12

## Why Contingency Is Needed
The full variational EM + latent switching + sparsity-regularized high-order model is nonconvex.
A global convergence-rate theorem for the entire pipeline is substantially harder than the convex surrogate proof in Step 46.

## Contingency Action Taken
1. Keep rigorous convergence claim at convex-block level only (Step 46: proximal subproblem O(1/m)).
2. For full nonconvex loop, cite standard stationarity/descent literature and provide empirical convergence diagnostics.

## Citation Anchors
1. Proximal-gradient convex rates (Beck-Teboulle line).
2. Nonconvex block-coordinate/proximal EM stationarity literature (PALM/majorization-minimization families).
3. Variational inference convergence discussions (local optima and ELBO ascent behavior).

## Empirical Convergence Evidence
Using `results/phase1_step45_proxem/metrics_summary.json`:
1. expected log-likelihood is monotone in selected run (`loglik_monotone_fraction = 1.0`),
2. objective and log-likelihood traces are archived in plots.

## Claim-Safe Wording for Paper
- Safe: "We prove O(1/m) convergence for the convex proximal subproblem and report empirical monotone ELBO/log-likelihood behavior for the full nonconvex routine."
- Unsafe: "We prove global convergence of the full nonconvex variational switching hypergraph estimator."
