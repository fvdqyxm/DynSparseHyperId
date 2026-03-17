# Phase 0 Vetting and Fundamental Modifications

## Objective
Convert Phase 0 from a checklist into a falsifiable, auditable pipeline with explicit
logic checks, failure modes, and pass/fail criteria.

## Fundamental Issues Found
1. **Reference integrity risk**: initial PDF set included unrelated papers.
2. **Environment drift risk**: active venv is Python 3.14, while robust reproducibility in
   this ecosystem is usually stronger under Python 3.11/3.12.
3. **Artifact integrity risk**: a file named `.ipynb` contained plain Python code.
4. **No audit trail**: no step tracker with evidence and contingency logging.
5. **No executable acceptance tests**: progress was narrative, not test-backed.

## Modifications Applied
1. Replaced placeholder README content with concrete model/goal description.
2. Added formal step ledger (`tracking/phase0_steps.csv`) with status/evidence.
3. Added LaTeX proof scaffold (`proofs/latex/master.tex`).
4. Added literature summaries for the three foundational papers.
5. Renamed invalid notebook artifact to script (`test_wandb_logging.py`).
6. Implemented deterministic baseline experiment script:
   - Sparse Graphical Lasso recovery.
   - Sparse LDS support recovery with LassoCV.
7. Added test suite (`tests/test_phase0_steps.py`) to validate step evidence.

## Step-Level Logic Checks (Phase 0)
1. Step 8-10 (literature) now require:
   - Correct citation.
   - Relevance to identifiability/sample complexity claims.
   - Explicit non-transferable assumptions section.
2. Step 11-15 (baselines) now require:
   - Fixed random seed and parameter logging.
   - Saved metrics JSON + matrix artifacts.
   - Support-level precision/recall/F1, not only visual plots.
3. Step 21 (Gate 0) now requires:
   - Pairwise dynamical recovery metric reported from scripted pipeline.
   - No claim of gate pass without reproducible metrics artifact.

## Additional Required Fixes (Next)
1. Create and switch to a Python 3.11 venv, then rerun all baselines and tests.
2. Implement regime-switching LDS baseline (Step 15) before Gate 0 decision.
3. Implement Wilson-Cowan + HRF stress tests before moving beyond Phase 0.
