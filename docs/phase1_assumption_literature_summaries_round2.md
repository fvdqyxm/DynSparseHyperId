# Phase 1 Literature Sweep (Round 2): Assumption-Critical Sources

Date: 2026-03-12
Scope: Additional primary sources focused on validating A1-A6 assumptions and identifying transfer limits to our integrated model.

## 1) Zhao and Yu (2006) — Lasso model-selection consistency
Source: https://www.jmlr.org/papers/v7/zhao06a.html
Summary: Establishes model-selection consistency conditions for Lasso, emphasizing the irrepresentable condition and sparsity-dependent scaling. This directly supports A1 (controlled sparsity), A4 (irrepresentable geometry), and A6 (signal floor implications for exact support recovery). Transfer caveat: the result is for linear sparse regression and must be generalized for higher-order hyperedge operators and latent switching.

## 2) Wainwright (2009) — Sharp thresholds for sparse recovery
Source: https://doi.org/10.1109/TIT.2009.2016018
Summary: Characterizes sample complexity and sharp phase transitions for exact support recovery under L1-constrained estimation, including explicit beta-min behavior. This strongly supports A1/A6 structure and expected polynomial-log scaling forms in finite-sample guarantees. Transfer caveat: dynamic latent-regime and high-order operators are outside original scope.

## 3) Ravikumar et al. (2011) — L1-penalized log-det covariance estimation
Source: https://projecteuclid.org/journals/annals-of-statistics/volume-39/issue-3/High-dimensional-covariance-estimation-by-minimizing-l1-penalized-log-determinant/10.1214/11-AOS949.full
Summary: Provides high-dimensional consistency for sparse inverse covariance estimation with explicit incoherence and sample scaling conditions. Supports A1, A4, and A6 for the static pairwise Gaussian setting and informs our support-recovery proof strategy. Transfer caveat: no latent switching and no high-order interactions.

## 4) Bach (2008) — Group Lasso consistency
Source: https://www.jmlr.org/papers/v9/bach08b.html
Summary: Gives consistency conditions for group Lasso and multiple-kernel learning, aligning with block-structured sparsity assumptions in our hyperedge grouping strategy. Supports A4 as a block-level extension of irrepresentable/restricted geometry and motivates grouped penalties in the ELBO. Transfer caveat: static supervised setting; temporal latent-state coupling remains open in our context.

## 5) Negahban et al. (2012) — Unified M-estimator framework
Source: https://projecteuclid.org/journals/statistical-science/volume-27/issue-4/A-unified-framework-for-high-dimensional-analysis-of-M-estimators/10.1214/12-STS400.full
Summary: Introduces decomposable regularizers and restricted strong convexity as a general recipe for high-dimensional recovery guarantees. Supports A3/A4 by formalizing when regularized estimators can concentrate under noisy observations, and gives a rigorous template for deriving rates. Transfer caveat: latent Markov switching and hypergraph multilinear features require model-specific extension.

## 6) Basu and Michailidis (2015 line; arXiv preprint)
Source: https://arxiv.org/abs/1311.4175
Summary: Develops regularized estimation for high-dimensional time-series models under dependence and tail assumptions, with nontrivial rates in dynamical settings. Supports A3 (noise regularity under dependence) and informs sample-size scaling under temporal dependence. Transfer caveat: regime switching plus high-order emissions are not included.

## 7) Paulin (2012/2015) — Concentration for Markov chains
Source: https://arxiv.org/abs/1212.2015
Summary: Provides concentration inequalities with explicit dependence on spectral gap/mixing quantities for Markov chains. Supports A5 by justifying effective-sample-size corrections for dependent latent-state trajectories and confidence bounds under mixing. Transfer caveat: application to parameterized switching hypergraph estimators requires an additional reduction argument.

## 8) Gassiat, Cleynen, Robin (2016) — HMM identifiability
Source: https://projecteuclid.org/journals/annals-of-statistics/volume-44/issue-6/Finite-state-space-non-parametric-hidden-Markov-models-are-identifiable/10.1214/16-AOS1526.full
Summary: Gives identifiability results for finite-state nonparametric HMMs under distinct emission and transition conditions. Supports A2/A5 (separation plus ergodic/nondegenerate transitions) as canonical regime identifiability requirements. Transfer caveat: does not directly prove sparse high-order operator recovery.

## 9) Balsells-Rodas, Wang, Li (ICML 2024) — Switching dynamics identifiability
Source: https://proceedings.mlr.press/v235/balsells-rodas24a.html
Summary: Establishes identifiability results for switching dynamical systems under structural assumptions and permutation symmetries. Directly supports A2 and validates the need to state identifiability only up to trivial symmetries. Transfer caveat: sparse high-order hypergraph emission structure is beyond this theorem.

## Round-2 Logic Check
1. The assumption classes A1-A6 remain orthodox and literature-supported.
2. No single cited source closes the full integrated theorem (sparse high-order + latent switching + finite-sample support recovery).
3. Claim-safe framing remains mandatory: novelty is the integrated theorem and proof, not the assumption primitives.
