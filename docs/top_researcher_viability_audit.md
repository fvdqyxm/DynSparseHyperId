# Viability Audit (Top-Researcher Lens)

## Executive Verdict
The idea is **scientifically viable** and potentially high-impact, but only if claims are
staged and falsifiable. The current all-at-once target (global identifiability + finite-sample
rates + minimax tightness + scalable inference for sparse k>=3 regime-switching dynamics) is
too broad for a single first theorem package unless sharply scoped.

## Non-Negotiable Scope Correction
1. **Primary theorem scope for paper v1**:
   - Regime-switching **pairwise** sparse dynamics (k=2), linear-Gaussian emissions.
   - Identifiability up to regime permutation.
   - Finite-sample support recovery rates under explicit separation/incoherence assumptions.
2. **Secondary extension**:
   - Static k=3 identifiability/recovery (no switching), then dynamic k=3 in a follow-up.
3. **Illustrative neuroscience section**:
   - Must be labeled as application/illustration, not proof of mechanistic causality.

## Core Logic Risks and Fundamental Fixes
1. **Identifiability overclaim risk**
   - Risk: claiming global identifiability without resolving latent symmetries and regime overlap.
   - Fix: theorem statements must explicitly list equivalence classes and separation constants.
2. **Sample-complexity overclaim risk**
   - Risk: bounds not matched to estimator actually run.
   - Fix: keep theorem estimator aligned with implementable proximal/variational objective.
3. **Algorithm-theory mismatch risk**
   - Risk: nonconvex amortized inference with convex-style guarantees.
   - Fix: separate guarantees:
     - statistical consistency (population/idealized estimator),
     - optimization convergence (to stationary points under practical algorithm).
4. **Neuroscience confounding risk**
   - Risk: motion/HRF/noise artifacts mistaken as high-order effects.
   - Fix: enforce nuisance regression, motion-scrub stress tests, and negative controls.

## Minimal Theorem Ladder (Defensible)
1. **T1 (k=2, switching, sparse linear Gaussian):**
   identifiability under transition separation + sparse dynamics + noise bounds.
2. **T2 (k=2):**
   finite-sample support recovery with explicit scaling in N, sparsity, K, delta.
3. **T3 (lower bound):**
   Fano packing for near-matching lower complexity class.
4. **T4 (k=3 static or weakly dynamic):**
   extension under stronger incoherence and bounded tensor order.

## Anti-Overfitting Protocol (Required)
1. Evaluate across multiple generative families, not one simulator:
   - linear Gaussian switching,
   - nonlinear Wilson-Cowan + HRF,
   - misspecified noise (heavy-tailed/outliers).
2. Include hard negative controls:
   - data generated with pairwise-only structure should not create false k=3 gains.
   - shuffled regime labels should destroy switching advantage.
3. Report uncertainty:
   - >= 50 seeds per setting,
   - confidence intervals for F1/accuracy,
   - calibration of regime posterior confidence.
4. External-validity checks:
   - train on one synthetic family, test on another.
5. No single-metric gate:
   - require precision-recall profile + calibration + robustness ablations.

## Step-Level Test Design (Full-Plan)
1. **Phase 0 (implemented)**:
   environment/artifact integrity tests + baseline metric thresholds + tracker integrity.
2. **Phase 1 (to add)**:
   theorem-spec tests:
   - every theorem has assumptions block, identifiability symmetries, and proof dependency map.
3. **Phase 2 (to add)**:
   scaling-law tests:
   - monotone error decrease with T,
   - degradation under increasing noise,
   - ablation sanity checks.
4. **Phase 3 (to add)**:
   biological plausibility tests:
   - motif stability under preprocessing perturbations,
   - confound sensitivity analyses.
5. **Phase 4 (to add)**:
   reproducibility tests:
   - full pipeline rerun from clean env,
   - figure regeneration checksum.

## Immediate Next Actions (Highest ROI)
1. Implement Step 15 (regime-switching LDS) and make Gate 0 depend on switching recovery.
2. Migrate runtime to Python 3.11 and rerun all tests for stability.
3. Add synthetic stress-grid runner (N, T, sigma, K) with confidence intervals.
4. Freeze reproducibility:
   - exact dependency lockfile,
   - one-command check script,
   - archived metrics artifacts.
