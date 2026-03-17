# Phase 1 Literature Sweep (Round 3): Rows 22-30

Date: 2026-03-12
Purpose: close the remaining Step-28 topics with assumption-aware summaries and explicit guarantee classes.

## 22) Kolar et al. (2011) — Time-Varying Graphical Models
Source: https://proceedings.mlr.press/v15/kolar11a.html
Summary: This paper provides consistency results for estimating time-varying undirected graphs under smoothness and sparsity assumptions. The guarantee class is high-dimensional support recovery with temporal regularity constraints. It supports our A1/A4 framing for sparse structure under dynamics but remains pairwise and does not include latent switching hyperedges.

## 23) de Castro et al. (2016) — Minimax Adaptive Estimation in Nonparametric HMMs
Source: https://jmlr.org/papers/v17/14-111.html
Summary: Establishes minimax rates for nonparametric HMM estimation and adaptive procedures under regularity conditions. Guarantee class is statistical rate optimality, directly relevant for our sample-complexity and lower-bound ambitions (Steps 39-42). It supports A2/A5 style assumptions (distinct emissions + mixing) while not addressing sparse high-order regression operators.

## 24) Tran et al. (2016) — Spectral M-Estimation for HMMs
Source: https://proceedings.mlr.press/v51/tran16.html
Summary: Combines spectral initialization ideas with M-estimation for HMMs to improve practical and theoretical behavior under latent-state models. Guarantee class is latent-model parameter estimation with spectral identifiability conditions. It supports our regime-identifiability decomposition logic (L1/L4) but does not solve sparse hyperedge support recovery.

## 25) Jedra and Proutiere (2019) — Sample Complexity of Linear System Identification
Source: https://arxiv.org/abs/1904.09396
Summary: Analyzes sample complexity for identifying linear systems and characterizes dependence on system dynamics and noise assumptions. Guarantee class is finite-sample identification scaling for dynamical models. This informs our Step-41 dependency structure (explicit T-scaling) but is not a sparse latent-switching high-order theorem.

## 26) Tensor Recovery in High-Dimensional Ising Models (2024)
Source: https://www.sciencedirect.com/science/article/pii/S0047259X24000423
Summary: Provides high-dimensional tensor recovery guarantees for structured interactions, including support-recovery style behavior under sparsity and regularity assumptions. Guarantee class is tensor-parameter consistency/support recovery in high-dimensional settings. This supports the plausibility of A4-type geometry for higher-order interactions while our regime-switching dynamic extension remains open.

## 27) Dong et al. (2020) — Switching State-Space Models with Nonlinear Dynamics
Source: https://proceedings.neurips.cc/paper_files/paper/2020/hash/47e534f0f4cd81dbd9c8f4b7885f685c-Abstract.html
Summary: Develops nonlinear switching state-space inference with scalable variational methods. Guarantee class is algorithmic/inference performance under expressive nonlinear latent regimes. It supports our Step-45 modeling direction (nonlinear variational switching) but does not provide our targeted identifiability + support-complexity theorem.

## 28) Yu (2010) — Hidden Semi-Markov Models
Source: https://www.sciencedirect.com/science/article/pii/S0004370209001978
Summary: A foundational treatment of HSMMs with explicit state-duration modeling and inference implications. Guarantee class is model-theoretic and algorithmic treatment for semi-Markov latent dynamics. It supports extension paths beyond first-order Markov assumptions and clarifies how A5-like mixing assumptions can change under duration processes.

## 29) Johnson and Willsky (2013) — Bayesian Nonparametric HSMMs
Source: https://jmlr.org/papers/v14/johnson13a.html
Summary: Introduces a nonparametric HSMM framework with explicit duration handling and practical inference schemes. Guarantee class is Bayesian model/inference development for switching processes with durations. This complements Step-28/29 scope (duration-aware switching) and helps stress-test whether Markov assumptions are too restrictive for neuroscience trajectories.

## 30) Luo, Qi, Toint (2020) — High-Dimensional Tensor Bernstein Concentration
Source: https://arxiv.org/abs/2007.10985
Summary: Presents concentration inequalities in tensor settings with explicit dimensional dependence. Guarantee class is concentration tool development, directly relevant for Step-40 style arguments on high-order sums. It does not directly resolve latent switching dependence, so a dependence-aware adaptation (mixing-corrected) remains required.

## Round-3 Logic Check
1. Step-28 source coverage is now complete at 30/30 citations.
2. Summaries explicitly separate transferable theorem archetypes from non-transferable claims.
3. The integrated novelty claim remains unchanged: no reviewed source closes sparse high-order latent regime-switching identifiability + finite-sample support recovery in one theorem.
