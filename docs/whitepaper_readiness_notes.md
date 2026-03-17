# White Paper Readiness Notes (Exhaustive Review)

## Purpose
This note documents everything completed so far, why each action matters scientifically,
and how it contributes to a credible eventual white paper rather than a brittle demo.

## 1) Foundation Integrity Corrections

### 1.1 README was placeholder-level
- **What changed**: Rewrote `README.md` with concrete problem statement, model intent,
  contribution targets, and current logic checks.
- **Why meaningful**: White papers fail when framing is vague. This creates a stable
  contract for what the project is and is not claiming.

### 1.2 Literature set had reference mismatches
- **What changed**:
  - Added canonical files for:
    - `friedman_graphical_lasso_2008.pdf`
    - `chandrasekaran_latent_graphical_2012.pdf`
  - Kept Turnbull hypergraph paper.
  - Added structured summaries:
    - `friedman_graphical_lasso_2008_summary.md`
    - `chandrasekaran_latent_graphical_2012_summary.md`
    - `turnbull_latent_hypergraph_summary.md`
- **Why meaningful**: White-paper theoretical claims are only as good as source fidelity.
  Wrong references cascade into invalid theorem framing and weak peer review outcomes.

### 1.3 Artifact integrity issue: invalid notebook extension
- **What changed**: Renamed plain-text fake notebook to:
  - `notebooks/experiments/test_wandb_logging.py`
- **Why meaningful**: Prevents downstream tooling and reproducibility failures caused by
  misleading file formats.

## 2) Formal Research Scaffolding Added

### 2.1 Proof skeleton scaffold
- **What changed**: Added `proofs/latex/master.tex` with theorem-oriented section structure:
  model, identifiability, finite-sample recovery, lower bounds, convergence.
- **Why meaningful**: White-paper maturity requires theorem architecture before proofs;
  this prevents ad-hoc derivations and scope drift.

### 2.2 Plan tracker with evidence and contingencies
- **What changed**: Added `tracking/phase0_steps.csv` with:
  - step number,
  - status,
  - completion date,
  - notes/results,
  - contingency trigger field.
- **Why meaningful**: Enables auditability and accountability for each scientific claim.

### 2.3 Top-researcher viability audit
- **What changed**: Added `docs/top_researcher_viability_audit.md`.
- **Why meaningful**:
  - separates viable theorem scope from over-ambitious combined claims,
  - introduces falsification protocol,
  - defines anti-overfitting requirements.

## 3) Baseline Methods Implemented (Reproducible)

### 3.1 Phase 0 deterministic baseline script
- **File**: `code/models/phase0_baselines.py`
- **Implements**:
  1. Sparse Graphical Lasso recovery from synthetic Gaussian data.
  2. Sparse LDS support recovery using LassoCV with sparsity-aware model selection.
  3. Artifact generation:
     - `results/phase0/metrics_summary.json`
     - matrix `.npy` outputs
     - heatmap figures for true vs recovered structures
- **Why meaningful**:
  - Establishes pairwise recovery competency before high-order claims.
  - Produces machine-readable evidence, not anecdotal plots.

### 3.2 Fundamental algorithmic correction (not patching symptoms)
- **Initial issue**: High recall + low precision (dense overfit) failed Gate criterion.
- **Fixes applied**:
  - Graphical Lasso model selection switched to **eBIC-aware** sparsity selection.
  - LDS coefficient selection switched to **CV+1SE-informed sparse regime**, with
    balanced penalty selection and explicit support threshold semantics.
- **Outcome**:
  - Graphical Lasso F1: **0.9048**
  - Sparse LDS F1: **0.8621**
- **Why meaningful**:
  - This moves from cosmetic fitting to support-recovery-valid inference.
  - Establishes a defensible baseline for Gate 0.

## 4) Step-Level Testing Infrastructure

### 4.1 Test suite
- **File**: `tests/test_phase0_steps.py`
- **Coverage**:
  1. Tracker integrity and step indexing.
  2. README non-placeholder checks.
  3. Required folder structure checks.
  4. LaTeX scaffold checks.
  5. Literature summary existence/quality-structure checks.
  6. Environment and dependency import checks.
  7. Baseline metrics file/schema checks.
  8. Gate threshold checks (F1 >= 0.75).
  9. Completed-step-to-artifact evidence checks.
- **Why meaningful**:
  - White paper requires reproducibility under automated checks.
  - Prevents “claimed complete” steps without evidence.

### 4.2 One-command validation runner
- **File**: `scripts/run_phase0_checks.sh`
- **Behavior**:
  1. Runs deterministic baseline pipeline.
  2. Runs full Phase 0 unit tests.
- **Why meaningful**:
  - Enables CI-style repeatability and rapid regression detection.

## 5) Current Scientific Position After This Work

## What is now defensible
1. Pairwise sparse recovery baseline under moderate noise with reproducible artifacts.
2. Structured tracking and testing discipline for Phase 0.
3. Foundational literature alignment with relevant methods/identifiability context.

## What is not yet defensible
1. Regime-switching LDS recovery (Step 15) is not implemented yet.
2. Wilson-Cowan + HRF robustness stack (Steps 16-19) not implemented.
3. Any claim about high-order (k>=3) dynamic identifiability/sample-complexity remains future work.
4. Minimax lower bounds and convergence proofs are not yet developed.

## 6) Why This Matters for White Paper Trajectory
These changes convert the project from idea-only to an auditable research program:
1. **Traceability**: every completed Phase 0 step has an artifact and test.
2. **Falsifiability**: gate criteria are explicit and executable.
3. **Theoretical readiness**: proof document structure exists before theorem claims.
4. **Methodological discipline**: references and assumptions are now governed.

This is the right substrate for drafting a white paper that can survive rigorous
technical review.

## 7) Immediate Next Work (White Paper Critical Path)
1. Implement Step 15 (2-regime switching LDS + EM/VI inference + support metrics).
2. Add stress-grid experiments over `N, T, sigma, K` with confidence intervals.
3. Migrate to Python 3.11 lockfile and rerun all checks for long-horizon reproducibility.
4. Start theorem memo:
   - explicit symmetry class,
   - identifiability assumptions table,
   - proof dependency graph.
