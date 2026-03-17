# Step 36 Note: Key Lemma Candidate for Hyperedge Irrepresentable Condition

Date: 2026-03-12
Status: Drafted (candidate key lemma identified)

## Candidate Lemma (Working Statement)
Let \(\Phi \in \mathbb{R}^{T\times p}\) be the regime-conditioned design matrix for grouped triplet features,
partitioned by true support \(S\) and complement \(S^c\).
If there exists \(\eta\in(0,1]\) such that
\[
\left\|\Sigma_{S^cS}\Sigma_{SS}^{-1}\right\|_{\infty,2} \le 1-\eta,
\quad
\lambda_{\min}(\Sigma_{SS})\ge \kappa_0>0,
\]
with \(\Sigma = \mathbb{E}[\Phi^{\top}\Phi/T]\), then group-sparse support for hyperedges is uniquely recoverable
under suitable \(\lambda\)-scaling and beta-min condition.

## Interpretation
1. First inequality is the group-irrepresentable condition: off-support groups cannot be too correlated with on-support groups.
2. Second is restricted invertibility on true support.
3. Together they are the direct high-order analog of classical lasso/graphical-model irrepresentable geometry.

## Why This Is the "Key Lemma"
This is the exact hinge between:
1. high-order feature geometry (triplet design), and
2. support identifiability/consistency claims.
Without it, support claims collapse to prediction-only guarantees.

## Dependencies
1. Concentration for dependent design (mixing-corrected).
2. Regime-conditioning error control (posterior or decoding uncertainty).
3. Beta-min threshold tied to \(\lambda\) and effective sample size.

## Minimal Empirical Diagnostic Plan
To avoid purely symbolic assumptions, report:
1. estimated \(\|\hat\Sigma_{S^cS}\hat\Sigma_{SS}^{-1}\|_{\infty,2}\),
2. estimated \(\lambda_{\min}(\hat\Sigma_{SS})\),
3. support recovery degradation when diagnostics violate thresholds.

## Step Status Decision
- Step 36 ("Identify key lemma") can be marked Completed once this lemma is accepted as canonical in `master.tex` theorem dependency map.
- Full proof remains future work (Step 39-41 dependency).
