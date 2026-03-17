# Phase 1 Gap Table (Integrated Setting)

## Scope
Gap analysis for: sparse high-order (`k>=3`) + latent regime switching + finite-sample guarantees + scalable inference.

## Gap Matrix

| Work Family | High-Order Hyperedges (`k>=3`) | Latent Regime Switching | Global Identifiability (up to trivial symmetries) | Finite-Sample Support Recovery Bounds | Minimax Lower Bounds | Practical Scalable Inference | Main Gap Relative to Project |
|---|---|---|---|---|---|---|---|
| Graphical Lasso / static sparse GGMs | No (pairwise) | No | Partial in static setting | Yes (static regimes, assumptions vary) | Partial | Yes | Missing high-order and switching |
| Latent sparse+low-rank GGMs (CPW style) | No | Indirect latent confounding only | Yes under transversality/incoherence | Yes | Limited | Convex but static | Missing switching and high-order |
| Static latent-space hypergraph models (Turnbull class) | Yes | No | Partial (with coordinate constraints) | No full support bounds in switching context | No | MCMC feasible but not switching-targeted | Missing temporal regimes and recovery bounds |
| Hypergraph reconstruction from dynamics | Yes | Usually no explicit latent Markov regimes | Limited (task-specific) | Limited/empirical | Rare | Varies | Missing latent switching identifiability theorem stack |
| Switching LDS / HMM dynamical identifiability | Typically pairwise linear | Yes | Growing recent theory | Some parameter recovery results | Partial | Yes | Missing high-order sparse hyperedge recovery |
| Current project target | Yes | Yes | Targeted | Targeted | Targeted | Targeted | Integrated theorem + algorithm stack |

## Claim-Safe Summary
1. Existing literature strongly covers components of the problem.
2. The integrated problem class remains underdeveloped in theorem-level form.
3. Novelty must be phrased as integration plus explicit assumptions, not as "nothing exists".
4. Round-3 literature additions reinforce this: strong partial precedents for time-varying graphs, HMM rates, spectral latent inference, HSMM duration modeling, and tensor concentration, but still no single end-to-end theorem matching the project target.

## Evidence Anchors
1. `docs/formula_traceability_audit_2026_03_12.md`
2. `docs/novelty_landscape_2026_03_12.md`
3. `docs/literature_sweep_unique_tricks_2026_03_12.md`
4. `docs/phase1_literature_matrix_30_target.md`
5. `docs/phase1_literature_summaries_round3.md`

## Immediate Phase 1 Use
1. This table becomes the canonical related-work lens for theorem positioning.
2. Every theorem statement in `proofs/latex/master.tex` should map to one explicit row-gap above.
