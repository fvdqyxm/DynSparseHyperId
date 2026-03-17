# Step 41 Working Note: Deriving an Explicit T Bound

Date: 2026-03-12
Status: In Progress

## Goal
Refine the Step-39 theorem template into an explicit sample-size form that displays dependence on
\(N\), \(k\), sparsity, number of regimes, and confidence.

## Dimensional Quantities
For fixed \(k=3\):
1. per-target high-order feature count: \(M_3 = \binom{N}{2} = O(N^2)\),
2. grouped parameter ambient size across regimes: \(p \asymp K N M_3 = O(KN^3)\),
3. active groups per regime: \(s\).

## Working Concentration-to-Recovery Chain
1. Concentration term for dependent design:
\[
\epsilon_T \asymp \sqrt{\frac{\log(p/\delta)}{T_{\mathrm{eff}}}}.
\]
2. Group-sparse recovery requires
\[
\epsilon_T \lesssim \frac{\beta_{\min}\kappa_0}{\sqrt{s}},
\]
which yields
\[
T_{\mathrm{eff}} \gtrsim \frac{s}{\beta_{\min}^2\kappa_0^2}\log\frac{p}{\delta}.
\]
3. Replace \(T_{\mathrm{eff}}\approx T/\tau_{\mathrm{mix}}\):
\[
T \gtrsim \tau_{\mathrm{mix}}\frac{s}{\beta_{\min}^2\kappa_0^2}\log\frac{KN^3}{\delta}.
\]
4. Add regime-separation penalty (decoding layer):
\[
T \gtrsim \tau_{\mathrm{mix}}\,\Delta_{\min}^{-2}\,\log\frac{K}{\delta}.
\]

## Combined Working Upper Bound
\[
T \gtrsim
\tau_{\mathrm{mix}}\left[
\frac{s}{\beta_{\min}^2\kappa_0^2}\log\frac{KN^3}{\delta}
+
\Delta_{\min}^{-2}\log\frac{K}{\delta}
\right].
\]

## Logic Check
1. Polynomial dependence in structural hardness terms.
2. Logarithmic dependence in dimension/regimes/confidence.
3. Explicitly separates support-estimation and regime-decoding burdens.

## Remaining Tasks
1. Replace \(N^3\) placeholder by precise support-index combinatorics under selected parameterization.
2. Tighten constants and identify dominant term by operating regime.
3. Map this bound directly into `master.tex` theorem statement after proof lemmas are locked.
