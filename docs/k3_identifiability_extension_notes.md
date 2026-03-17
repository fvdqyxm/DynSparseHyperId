# Step 33 Working Note: Extending Identifiability from k=2 to k=3

Date: 2026-03-12
Status: In Progress

## Objective
Show how k=2 identifiability can be lifted to k=3 (triplet) structure under explicit non-aliasing and incoherence assumptions.

## Model Slice (per regime r)
Let
\[
\mathbb{E}[y_t \mid y_{t-1}, z_t=r] = A_r y_{t-1} + H_r \phi(y_{t-1}),
\]
with pairwise term \(A_r\) and triplet term \(H_r\), where \(\phi(y)\) stacks \(y_i y_j\), \(i<j\).

## Decomposition Strategy
1. Recover regime path and regime-conditioned moments up to permutation (from Step 32 path).
2. Separate linear and quadratic regressors in regime-conditioned design matrix.
3. Use block-injectivity argument: if
   - linear block has RE/incoherence,
   - quadratic block has RE/incoherence,
   - cross-block collinearity is bounded,
   then \((A_r,H_r)\) is unique on sparse class.

## Core Injectivity Condition (Working)
Define feature map
\[
\Psi(y) := \begin{bmatrix} y \\ \phi(y) \end{bmatrix} \in \mathbb{R}^{N+\binom{N}{2}}.
\]
For sparse supports \(S_A, S_H\), require restricted Gram eigenvalue lower bound
\[
\lambda_{\min}\left( \mathbb{E}[\Psi_{S}\Psi_{S}^{\top}] \right) \ge \kappa_0 > 0,
\]
with \(S=S_A\cup S_H\), and irrepresentable-type control for \(S^c\) against \(S\).

## Non-Aliasing Requirement (k=3 specific)
Distinct sparse triplet supports should not produce identical conditional means almost surely under regime-conditioned covariate law:
\[
H\phi(y) = H'\phi(y) \;\text{a.s.} \Rightarrow H=H' \quad \text{on sparse class}.
\]
This excludes feature-aliasing between different hyperedge supports.

## Proposition Skeleton (Not Yet Proved)
Under:
1. Step-32 regime/path identifiability up to permutation,
2. restricted injectivity of \(\Psi\) on sparse supports,
3. beta-min on nonzero entries,
4. regime separation and mixing assumptions,
\((A_r,H_r)_{r=1}^K\) is identifiable up to regime permutation.

## Failure Modes to Test
1. Quadratic-feature collinearity (violates injectivity).
2. Vanishing excitation in specific node pairs (kills triplet recoverability).
3. Regime overlap too small relative to noise (path misassignment leakage).

## Immediate Next Theoretical Tasks
1. Formalize sparse-class non-aliasing as a lemma with sufficient moment conditions.
2. Derive explicit constants linking RE constants to support recovery margin.
3. Integrate this proposition into Theorem 1 dependency chain.
