# Chandrasekaran, Parrilo, Willsky (2012) — Latent Variable Graphical Model Selection

## Citation
Venkat Chandrasekaran, Pablo A. Parrilo, Alan S. Willsky.  
Latent variable graphical model selection via convex optimization.  
*Annals of Statistics* 40(4):1935-1967, 2012.

## Why This Paper Matters for DynSparseHyperId
This paper directly targets identifiability under hidden confounding: observed precision
structure decomposes into sparse plus low-rank components. It is foundational for handling
latent effects without collapsing into non-identifiability.

## Core Technical Points
1. Observed concentration is decomposed as sparse + low-rank under latent variables.
2. Proposes convex program with L1 penalty (sparse) and nuclear norm (low-rank).
3. Gives structural conditions for identifiability of each component.
4. Provides consistency guarantees under high-dimensional scaling regimes.

## Relevance to Current Plan
1. Your latent regime variable introduces hidden structure analogous in spirit to latent
   confounding; identifiability requires explicit structural separation assumptions.
2. Incoherence/irrepresentability-type conditions are not optional details; they are
   central to proving uniqueness and support recovery.
3. Provides a template for separating recoverability statements from algorithmic convergence.

## Logic Checks
1. Sparse+low-rank decomposition is not equivalent to regime-switching tensor recovery;
   assumptions cannot be transplanted without proof.
2. Label switching in latent regimes introduces additional symmetries beyond this paper.
3. Future theorems should explicitly state which ambiguities remain (permutation, scaling,
   rotations in latent embeddings).

## Action Items
1. Reuse proof style and condition-check discipline, not the model directly.
2. Build a assumptions table that maps each condition to an empirical stress test.
