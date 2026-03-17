# Turnbull et al. — Latent Space Modelling of Hypergraph Data

## Citation
Kathryn Turnbull, Simón Lunagómez, Christopher Nemeth, Edoardo Airoldi.  
Latent Space Modelling of Hypergraph Data.  
arXiv:1909.00472.

## Why This Paper Matters for DynSparseHyperId
It provides a latent-space statistical framework for hypergraph data and explicitly handles
identifiability issues in latent representations (e.g., via coordinate constraints), which is
conceptually aligned with your high-order latent-regime setting.

## Core Technical Points
1. Extends latent space modeling from pairwise networks to hypergraphs.
2. Uses a likelihood construction with manageable computational cost.
3. Uses delayed-acceptance MCMC for posterior sampling.
4. Discusses identifiability adjustments in latent coordinates.

## Relevance to Current Plan
1. Supports the claim that latent-space representations of hypergraphs require explicit
   alignment constraints to avoid non-identifiability.
2. Supplies modeling insights for high-order structures but not dynamic latent Markov regimes.
3. Serves as a static high-order baseline for assumptions and geometric constraints.

## Logic Checks
1. This is not a finite-sample identifiability theorem for sparse regime-switching dynamics.
2. MCMC feasibility does not imply scalable variational/proximal optimization guarantees.
3. Static latent hypergraph results should be cited as partial precedent only.

## Action Items
1. Use this as static high-order reference in related work and assumption design.
2. Keep separate from claims about dynamic recovery/sample complexity.
