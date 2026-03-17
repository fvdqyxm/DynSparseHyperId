# Formula Traceability Audit (Core Papers -> Current Code)

Date: 2026-03-12
Scope: formula-level audit of what is implemented now vs. what remains planned.

Archived mismatched PDFs intentionally excluded from formula grounding:
- `literature/summaries/archive_mismatched/1006.0563v3_wrong_target.pdf`
- `literature/summaries/archive_mismatched/friedman08a_wrong_target.pdf`

## Source Extraction Provenance
Text extracted from:
- `literature/summaries/friedman_graphical_lasso_2008.pdf`
- `literature/summaries/chandrasekaran_latent_graphical_2012.pdf`
- `literature/summaries/1909.00472v3.pdf`

Extracted text files:
- `literature/summaries/text_extracts/friedman_2008.txt`
- `literature/summaries/text_extracts/chandrasekaran_2012.txt`
- `literature/summaries/text_extracts/turnbull_1909_00472.txt`

## A. Paper Formula -> Code Mapping

### 1) Friedman et al. (2008), Eq. (2.1)
Paper formula (objective):
- maximize `log det(Theta) - tr(S Theta) - rho ||Theta||_1` over `Theta >= 0`.

Implementation status:
- Implemented conceptually (exact objective solved inside sklearn `GraphicalLasso`).
- Code path: `code/models/phase0_baselines.py` (`run_graphical_lasso`, lines 104-180).
- Added model-selection layer (EBIC): lines 140-143.

Logic check:
- This is a faithful static pairwise baseline.
- It is not a latent-regime or higher-order model.

### 2) Friedman et al. coordinate descent soft-threshold update (Eq. (2.11)-(2.12))
Paper formula:
- coordinate updates using soft-threshold operator `S(x,t)=sign(x)(|x|-t)+`.

Implementation status:
- Not manually coded; delegated to sklearn optimizer.
- Equivalent optimization family is used.

Logic check:
- Acceptable for baseline benchmarking; not appropriate as a "new algorithm" claim.

### 3) Chandrasekaran et al. (2012), Eq. (1.1)
Paper formula (Schur complement decomposition):
- `K_tilde_O = K_O - K_OH (K_H)^(-1) K_HO`
- motivates sparse + low-rank observed concentration structure.

Implementation status:
- Not explicitly implemented in current code.
- Concept used to justify latent-effect identifiability assumptions in notes/theory planning.

Logic check:
- We currently do not have a sparse+low-rank solver in code.
- No claim should imply we do.

### 4) Chandrasekaran et al. (2012), Eq. (1.2)
Paper formula (convex program):
- `(S_hat, L_hat) = argmin -ell(S-L; Sigma_n) + lambda_n (gamma ||S||_1 + tr(L))`
  with PSD constraints.

Implementation status:
- Not implemented yet.
- Closest related behavior: L1 sparsity in Lasso-based regressions only.

Logic check:
- Current code lacks nuclear-norm regularization and sparse+low-rank decomposition.
- This is an explicit future work item, not present capability.

### 5) Turnbull et al. hypergraph discrepancy likelihood (Eq. (8)-(9))
Paper formulas:
- Hamming-type discrepancy over hyperedge states:
  `d_k(g,h) = sum_{e_k in E_{N,k}} |y_e^(g) - y_e^(h)|`
- likelihood:
  `L(U,r,phi;h) proportional to product_k phi_k^{d_k} (1-phi_k)^{C(N,k)-d_k}`.

Implementation status:
- Not implemented exactly.
- Current Step 20 uses continuous polynomial regression surrogate for k=3 support recovery:
  `y = Phi * H^T + epsilon`
  in `code/models/static_hypergraph_k3.py` lines 52-66.

Logic check:
- This is a valid toy reconstruction benchmark, but not Turnbull likelihood inference.
- We should label it as "surrogate sparse polynomial inverse problem," not "nsRGH posterior inference."

### 6) Turnbull identifiability decomposition (Eq. (14))
Paper formula:
- `p(g*(U,r,phi), g(U,r)|...) = p(g*|g,phi) p(g|mu,Sigma,r)`
- non-identifiability fixed with Bookstein coordinates.

Implementation status:
- Not implemented.
- Only conceptual influence: explicit symmetry/identifiability guardrails in notes.

Logic check:
- No Bookstein coordinate constraints or DA-MCMC currently in code.

## B. Formulas Currently Active But Not Directly From Those Papers

### 1) Sparse LDS / switching LDS dynamics
- `x_t = A x_{t-1} + epsilon_t`
- `z_t ~ Markov(Pi)` and regime-specific `A_{z_t}`.
- Implemented in `code/models/phase0_baselines.py`.

### 2) Wilson-Cowan simulator and observability diagnostics
- Nonlinear neural dynamics + HRF convolution + artifact model.
- Effective Jacobian diagnostics to explain recovery limits.
- Implemented in `code/models/wilson_cowan_hrf_pipeline.py`.

### 3) Static k=3 surrogate hypergraph recovery
- Sparse regression on pair-product features (`x_j x_k`) per target node.
- Implemented in `code/models/static_hypergraph_k3.py`.

## C. Critical Gaps (Research Integrity)
1. No explicit sparse+low-rank convex program from Chandrasekaran currently implemented.
2. No Turnbull nsRGH likelihood + DA-MCMC implementation.
3. Current k=3 module is a surrogate benchmark, not a latent-space hypergraph posterior model.

## D. Immediate Upgrade Plan (Formula-Faithful)
1. Add a true sparse+low-rank estimator baseline for observed precision decomposition (CPW-style objective).
2. Add a Turnbull-style binary hyperedge likelihood module (or clearly scoped approximation) with explicit discrepancy term.
3. Keep surrogate k=3 module as separate baseline class and name it accordingly to avoid category confusion.

## E. Claim Guardrail (for writing)
Safe statement now:
- "We use Graphical Lasso as an exact convex sparse precision baseline and use surrogate higher-order sparse regression stress tests; full sparse+low-rank and latent-space hypergraph likelihood inference are planned, not yet implemented."

Unsafe statement now:
- "We implemented Chandrasekaran sparse+low-rank decomposition and Turnbull latent-space likelihood inference."
