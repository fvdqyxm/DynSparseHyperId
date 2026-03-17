# Phase 1 Theory Closure (Reframed, Claim-Safe)

Date: 2026-03-12

## Purpose
Close Phase 1 steps with explicit mathematical scope control:

1. What is closed at theorem-program level.
2. What remains open and cannot be overclaimed.
3. Which contingency from the plan is triggered.

## Closed Scope (What We Can Defend)
We close the theory program for the following restricted class:

1. First-order switching autoregression with sparse linear (`k=2`) and triplet-feature (`k=3`) emissions.
2. Fixed finite `K`, ergodic latent chain, bounded sub-Gaussian noise.
3. Sparse supports under RE/irrepresentable and beta-min conditions.
4. Non-aliasing of triplet feature map on sparse class.

Within this class:

1. `k=2` identifiability logic is closed up to regime permutation.
2. `k=3` extension is closed as a decomposition/injectivity result conditional on non-aliasing + cross-block incoherence.
3. Regime-separation dependence is explicit via spectral-gap / divergence terms.
4. Sample-size upper bound and Fano lower-bound scaling are matched up to log/constant factors.

## Final Working Scaling Pair
Upper (support + regime decoding burdens separated):
\[
T \gtrsim
\tau_{\mathrm{mix}}
\left[
\frac{s}{\beta_{\min}^2\kappa_0^2}\log\frac{K N^3}{\delta}
+
\Delta_{\min}^{-2}\log\frac{K}{\delta}
\right].
\]

Lower (packing + Fano):
\[
T \gtrsim
\tau_{\mathrm{mix}}
\frac{s\log(p/s)}{\alpha^2},
\]
with switching-separation penalties absorbed in constants/auxiliary terms.

Interpretation:

1. The two sides are near-matched at the structural level (`s log p` form with mixing penalties).
2. Remaining gap is constant/log refinement, not order-level contradiction.

## What Is Not Closed
1. Full end-to-end theorem for unrestricted high-order dynamical hypergraphs with arbitrary feature maps and no non-aliasing structure.
2. Full constant-tight finite-sample theorem with every nuisance term explicit.
3. External mentor/professor review loop (requires human interaction).

## Contingency Trigger Used
Plan contingency is triggered in a controlled way:

1. We keep claims at the restricted but mathematically coherent theorem class above.
2. We do not claim the unrestricted strongest version as fully proved.
3. Manuscript framing is theory-first and claim-safe, with explicit open-problem boundaries.

## Step Closure Mapping
1. Steps 32-35, 41, 42 are closed under this reframed theorem class.
2. Step 50 (Gate 1) is closed with contingency: proof program coherent and near-matched, but strongest unrestricted theorem remains future work.
