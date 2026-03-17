# k=2 Identifiability Proof Sketch (Working Draft)

## Target Statement
For a two-regime sparse linear switching model
\[
y_t = A_{z_t} y_{t-1} + \varepsilon_t, \quad z_t \in \{1,\dots,K\},\quad z_t\sim\text{Markov}(\Pi),
\]
identify $(\Pi,\{A_r\})$ up to permutation of regime labels from observed trajectories under explicit conditions.

## Proposed Assumptions
1. Regime separation: $\|A_r-A_{r'}\|_F \ge \Delta_A > 0$ for $r\neq r'$.
2. Markov ergodicity and non-degenerate transition matrix (bounded away from 0/1 entries).
3. Stable dynamics: spectral radii of $A_r$ bounded below 1.
4. Noise non-degeneracy: i.i.d. sub-Gaussian innovations with full covariance.
5. Sparse support with beta-min on nonzero entries.

## Proof Skeleton
1. Observable law decomposition:
- show trajectory distribution is a finite mixture over latent regime paths with Markov constraints.

2. Emission distinguishability:
- under separation and non-degenerate covariates, conditional one-step densities for distinct regimes are separated in KL/TV.

3. HMM-style identifiability transfer:
- map to an autoregressive HMM with regime-specific linear-Gaussian emissions.
- invoke identifiable HMM component decomposition up to label permutation.

4. Parameter uniqueness within regime:
- given regime-conditioned samples, sparse linear model identifiability follows from restricted eigenvalue + beta-min assumptions.

5. Combine symmetries:
- only global regime permutation remains.

## Required Technical Lemmas
1. Regime-conditioned design matrix concentration under mixing.
2. Lower bound on pairwise regime KL divergence in terms of $\Delta_A$.
3. Sparse regression support uniqueness under dependent samples.

## Current Gaps
1. Need a clean theorem reference or self-contained proof for AR-HMM identifiability with covariate dependence.
2. Need explicit constants linking separation $\Delta_A$ to finite-sample misclassification rate.
3. Need a unified treatment of dependence + sparsity in support recovery (not just iid lasso).

## Empirical Tie-In
Use existing switching sweep artifacts in `results/phase0_switching_sweep/` as sanity checks for assumptions:
1. regime contrast ratio,
2. support-diff rate,
3. degradation under observation noise.
