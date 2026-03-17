# Huge Literature Sweep: Unique Tricks for Step 15+ (2026-03-12)

## Sweep Goal
Find research-level, nontrivial methods that can materially improve latent regime-switching
recovery and later transfer to sparse high-order hypergraph dynamics.

## Primary Sources Reviewed
1. [Recurrent switching linear dynamical systems (arXiv:1610.08466)](https://arxiv.org/abs/1610.08466)
2. [Tree-Structured Recurrent SLDS (arXiv:1811.12386)](https://arxiv.org/abs/1811.12386)
3. [On the Identifiability of Switching Dynamical Systems (PMLR 2024)](https://proceedings.mlr.press/v235/balsells-rodas24a.html)
4. [Nonparametric Bayesian Learning of Switching LDS (NeurIPS 2008)](https://papers.nips.cc/paper/3546-nonparametric-bayesian-learning-of-switching-linear-dynamical-systems)
5. [Stochastic Variational Inference for Hidden Markov Models (arXiv:1411.1670)](https://arxiv.org/abs/1411.1670)
6. [Stochastic Variational Inference for the HDP-HMM (AISTATS 2016)](https://proceedings.mlr.press/v51/zhang16a.html)
7. [Latent variable graphical model selection via convex optimization (arXiv:1008.1290)](https://arxiv.org/abs/1008.1290)
8. [Latent Space Modelling of Hypergraph Data (arXiv:1909.00472)](https://arxiv.org/abs/1909.00472)
9. [Reconstructing hypergraphs from observed dynamics (Nature Communications 2025)](https://www.nature.com/articles/s41467-025-58285-z)
10. [Bayesian Nonparametric Inference for Switching Dynamic Linear Models (AISTATS 2014)](https://proceedings.mlr.press/v32/johnson14.html)
11. [Markov-Switching Process with Time-Varying Autonomous Dynamics (arXiv:2107.12552)](https://arxiv.org/abs/2107.12552)
12. [Changing-State Autoregressive Models for Time Series Data (arXiv:2210.07456)](https://arxiv.org/abs/2210.07456)

## Key Technical Ideas Extracted
1. **Persistence priors / sticky transitions**  
   From HDP-HMM work: add explicit self-transition bias to reduce spurious switching.
2. **Annealed inference schedules**  
   Start with smoother posteriors (high temperature), then sharpen; reduces poor local minima.
3. **Recurrent/state-dependent switching laws**  
   rSLDS: regime transition logits depend on latent/observed state, not only fixed Markov matrix.
4. **Multi-scale regime hierarchy**  
   Tree-rSLDS: coarse-to-fine switching can stabilize inference and interpretability.
5. **Stochastic variational minibatching for sequence models**  
   SVI-HMM/HDP-HMM: scalable updates with chain-edge corrections.
6. **Explicit duration modeling (HSMM/HDP-HSMM)**  
   Avoids geometric-duration bias of plain HMMs, often crucial when dwell times are long.
7. **Identifiability-first design**  
   Switching identifiability work emphasizes explicit conditions (separation, observability, noise).
8. **False-positive filtering for high-order reconstruction**  
   Hypergraph reconstruction work highlights filtering strategies to avoid inflated higher-order claims.
9. **Latent-space identifiability constraints**  
   Hypergraph latent models require alignment constraints to eliminate geometric symmetries.

## What We Already Integrated into Code
File: `code/models/phase0_baselines.py`
1. Sticky transition regularization in soft-EM transition updates.
2. Temperature annealing in soft-EM emission likelihood.
3. Multi-start initialization with:
   - `kmeans_full`
   - `kmeans_delta`
   - `residual_split`
   - `window_ar_cluster` (local dynamics clustering)
   - `random_blocks` (persistence-aware prior init)
   - `random`
4. Multi-method benchmarking:
   - hard-EM baseline,
   - soft-EM HMM baseline,
   - oracle-label ceiling for optimization-vs-identifiability gap.
5. Fundamental evaluation correction: fixed simulation/label misalignment bug in switching data generation.

## High-Value Tricks Not Yet Implemented (Priority Order)
1. **Recurrent transition model (rSLDS-style gating)**  
   Transition matrix conditioned on state features (e.g., logistic regression on `x_{t-1}`).
2. **Semi-Markov durations (HSMM/HDP-HSMM)**  
   Explicit duration modeling can strongly improve segmentation under dwell-time structure.
3. **Variational Bayesian uncertainty over A-regimes**  
   Posterior uncertainty can prevent overconfident support calls.
4. **Spectral/moment initialization for HMM state posteriors**  
   Better than KMeans when emission overlap is severe.
5. **Two-stage false-positive control for support**  
   Candidate screen + debiased refit + stability selection before declaring edges.
6. **Negative-control stress tests**  
   Pairwise-only nulls and shuffled-regime controls to detect algorithmic hallucination.

## Research-Level Logic Check
1. Current results show strong pairwise baselines and improved switching regime accuracy after a
   fundamental bug fix, but switching support recovery is still below theorem-grade targets.
2. This indicates the project remains scientifically interesting: the hard part is not solved
   by naive heuristics.
3. Next progress should target the gap to oracle support recovery, not just tuning accuracy metrics.

## Immediate Action Plan
1. Implement recurrent transition gating for soft-EM.
2. Add HSMM duration prior (or sticky-duration surrogate).
3. Add support-stability selection across bootstrap resamples.
4. Re-run full step checks and update `tracking/phase0_steps.csv` only when thresholds are met.
