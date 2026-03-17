# Step 42 Working Note: Fano/MI Lower-Bound Sketch

Date: 2026-03-12
Status: In Progress

## Goal
Construct minimax lower bounds for support recovery in latent switching high-order models and compare to Step-41 upper bound shape.

## Parameter Packing Idea
1. Build a packing set of regime-conditioned sparse supports
\(\{H^{(1)},\dots,H^{(M)}\}\) with pairwise Hamming distance at least \(d_0\).
2. Keep transition matrix in a controlled separated class to avoid trivial indistinguishability.
3. Enforce beta-min amplitude \(\alpha\) on active coefficients.

## Fano Template
For estimator \(\hat\theta\) over packing index \(V\in[M]\):
\[
\inf_{\hat\theta}\sup_{\theta\in\Theta}
\mathbb{P}(\hat\theta\neq\theta)
\ge
1 - \frac{I(Y_{1:T};V)+\log 2}{\log M}.
\]
Need to upper-bound mutual information via pairwise KL divergence:
\[
I(Y_{1:T};V) \le \max_{i\neq j} \mathrm{KL}(P_i\|P_j).
\]

## Working KL Scaling Direction
Under Gaussian innovations and bounded dynamics, pairwise KL between packed models scales like
\[
\mathrm{KL}(P_i\|P_j)
\lesssim
T_{\mathrm{eff}}\,\alpha^2\,d_0,
\]
with additional penalties from regime confusion when \(\Delta_{\min}\) is small.

## Lower-Bound Consequence (Sketch)
To keep error bounded away from zero, need
\[
T_{\mathrm{eff}} \gtrsim \frac{\log M}{\alpha^2 d_0}.
\]
Given sparse-support packings with \(\log M\sim s\log(p/s)\), this yields
\[
T \gtrsim \tau_{\mathrm{mix}}\frac{s\log(p/s)}{\alpha^2},
\]
up to model constants and switching-separation terms.

## Near-Optimality Check Against Step 41
1. Upper: \(\tilde O(\tau_{\mathrm{mix}} s \log p)\)-type dependence.
2. Lower: \(\Omega(\tau_{\mathrm{mix}} s \log(p/s))\)-type dependence.
3. Gap appears logarithmic/constant-level under current sketch.

## Remaining Tasks
1. Formalize packing under latent-regime nuisance parameters.
2. Tighten KL bound with explicit switching contribution.
3. Prove lower bound with exact minimax loss (support Hamming or exact recovery).
