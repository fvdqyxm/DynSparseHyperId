# Friedman, Hastie, Tibshirani (2008) — Graphical Lasso

## Citation
Jerome Friedman, Trevor Hastie, Robert Tibshirani.  
Sparse inverse covariance estimation with the graphical lasso.  
*Biostatistics* 9(3):432-441, 2008.

## Why This Paper Matters for DynSparseHyperId
This is the canonical computational/statistical baseline for sparse inverse covariance
estimation in the static Gaussian case. It anchors the optimization structure behind
support recovery with L1 penalties and provides a direct baseline against which dynamic
and higher-order extensions must be justified.

## Core Technical Points
1. Formulates sparse precision recovery as penalized Gaussian log-likelihood with L1 norm.
2. Uses block-coordinate updates equivalent to repeated lasso subproblems.
3. Produces sparse precision estimates and practical regularization paths.
4. Enables interpretable support recovery (nonzero precision entries imply conditional dependence).

## Relevance to Current Plan
1. Step-11/12 baseline should recover pairwise support from synthetic Gaussian data.
2. Optimization motifs (sparsity-promoting convex penalties) map conceptually to group-sparse
   hyperedge penalties in later phases.
3. Identifiability in the latent-switching high-order model must be stronger than static
   pairwise consistency guarantees from this line of work.

## Logic Checks
1. Graphical Lasso is static and pairwise; it cannot validate claims about regime switching
   or k>=3 interactions.
2. Support recovery quality is sensitive to lambda selection, sample size, and incoherence.
3. Any extension claims should separate computational success from identifiability guarantees.

## Action Items
1. Keep this as baseline comparator only.
2. Report support F1 versus sample size/noise before any higher-order claim.
