# Assumption Validity Check (A1-A6) Against Literature

Date: 2026-03-12
Purpose: Verify whether current core assumptions are supported by established theory, and identify where our assumptions are stronger/new.

## Source Set (Primary)
1. Friedman, Hastie, Tibshirani (2008), Graphical Lasso.
2. Chandrasekaran, Parrilo, Willsky (2012), sparse + low-rank latent graphical models.
3. Zhao and Yu (2006), JMLR, irrepresentable condition for Lasso model selection consistency.
4. Wainwright (2009), sharp thresholds / beta-min style support recovery scaling for Lasso.
5. Bach (2008), JMLR, group Lasso consistency conditions.
6. Basu and Michailidis (2015; arXiv 1311.4175 / Ann. Stat. line of work), high-dimensional sparse time-series regularized estimation.
7. Paulin (2012/2015), concentration inequalities for Markov chains with mixing-time dependence.
8. Balsells-Rodas, Wang, Li (ICML 2024), identifiability of switching dynamical systems.
9. Gassiat et al. (JMLR 2016/2020 and related), identifiability in nonparametric HMM settings under full-rank/ergodic transitions and distinct emissions.
10. Turnbull et al. (arXiv 1909.00472), hypergraph latent-space identifiability adjustments (Bookstein constraints).

## A1 Controlled Sparsity
Assumption:
- True support size is sublinear in ambient dimension (sparse operator/hyperedge structure).

Literature grounding:
- Core sparse model-selection literature (Zhao-Yu 2006; Wainwright 2009; Ravikumar et al. 2010) explicitly requires sparsity scaling.
- CPW 2012 assumes sparse structure in observed conditional graphical component.

Validity verdict:
- Strongly standard and well-supported.

## A2 Regime Separation
Assumption:
- Distinct regime parameters/emissions separated by positive margin.

Literature grounding:
- HMM/SDS identifiability generally requires distinct emissions / non-degenerate transitions.
- Balsells-Rodas et al. 2024 establish identifiability under explicit switching structure conditions.

Validity verdict:
- Well-supported in spirit; exact separation metric for our high-order model remains to be formalized.

## A3 Noise Regularity
Assumption:
- Sub-Gaussian (or controlled heavy-tailed extension) innovations.

Literature grounding:
- Sparse recovery proofs routinely use sub-Gaussian/sub-exponential tails.
- Time-series regularized estimation (Basu-Michailidis line) also uses controlled dependence + tail assumptions.

Validity verdict:
- Standard and valid.

## A4 Incoherence / Irrepresentable / RE-type Condition
Assumption:
- Hyperedge design must satisfy sparse recovery identifiability geometry.

Literature grounding:
- Zhao-Yu 2006 (irrepresentable condition).
- Ravikumar et al. 2010 analogous Fisher-information incoherence for graphical model selection.
- CPW 2012 transversality/incoherence geometry in sparse+low-rank decomposition.
- Group Lasso consistency (Bach 2008) uses analogous block-structure conditions.

Validity verdict:
- Strongly supported as a class of assumptions; exact hyperedge-tensor analog still requires our own theorem.

## A5 Mixing / Effective Sample Size
Assumption:
- Latent Markov chain is ergodic/mixing so concentration with dependence is possible.

Literature grounding:
- Paulin's concentration inequalities provide mixing-time-dependent finite-sample control for Markov chains.
- HMM identifiability/inference lines assume full-rank/ergodic transitions.

Validity verdict:
- Standard and valid.

## A6 Beta-Min
Assumption:
- Nonzero coefficients exceed a minimum signal level tied to sample size.

Literature grounding:
- Wainwright 2009 and related support recovery theory require minimum signal assumptions for exact selection.
- Similar signal-floor assumptions appear across sparse model-selection literature.

Validity verdict:
- Strongly standard and necessary for exact support claims.

## Critical Caveat (Most Important)
The assumptions are individually literature-grounded, but the *joint* theorem for
"sparse high-order + latent switching + finite-sample support recovery" is exactly the open contribution.
So we can claim:
1. assumption classes are orthodox,
2. integration is novel and needs full proof.

We should not claim:
1. that existing literature already proves the integrated theorem as-is.

## Immediate Action to Keep Rigor
1. In theorem statements, explicitly annotate each assumption with nearest literature archetype.
2. Add violation experiments (A2/A4/A6 breaks) to show expected failure modes.
3. Keep "claim-safe" language in all drafts until integrated proofs are complete.
