# Step 40 Working Note: Matrix/Tensor Bernstein for Hyperedge Sums

Date: 2026-03-12
Status: In Progress

## Objective
Connect dependent high-order feature sums to concentration inequalities required for Theorem 2.

## Random Quantity of Interest
For regime-weighted design/residual terms, we need to control objects like
\[
\frac{1}{T}\sum_{t=1}^{T} w_t\,\Psi_t\Psi_t^\top - \mathbb{E}[\Psi_t\Psi_t^\top],
\]
where \(\Psi_t=[y_{t-1};\phi(y_{t-1})]\), and \(w_t\) are latent posterior or decoded regime weights.

## Reduction Strategy
1. Represent tensor-feature concentration via matrix concentration on lifted feature vectors \(\Psi_t\).
2. Use dependence-aware concentration (mixing corrections) to replace iid variance proxy:
\[
T \to T_{\mathrm{eff}} \approx T / c_{\mathrm{mix}}.
\]
3. Apply matrix Bernstein/Freedman form to bound operator norm deviations.

## Working Bound Template
With sub-exponential tails and bounded mixing coefficients,
\[
\left\|\frac{1}{T}\sum_{t=1}^{T} X_t\right\|_{op}
\lesssim
\sqrt{\frac{v\log(d/\delta)}{T_{\mathrm{eff}}}}
+
\frac{L\log(d/\delta)}{T_{\mathrm{eff}}},
\]
for centered matrix process \(X_t\), variance proxy \(v\), and envelope \(L\).

## Literature Anchors
1. Matrix concentration baseline (Tropp line).
2. Markov-dependent concentration (Paulin line).
3. Tensor concentration adaptation via lifting/matricization (`arXiv:2007.10985`).

## Oracle-to-Inferred Bridge Added
See `docs/step40_weight_perturbation_lemma.md` for the perturbation lemma draft:
\[
\left\|\frac{1}{T}\sum_{t=1}^{T}(\hat w_t-w_t^\star)G_t\right\|_{op}
\lesssim O(\varepsilon_w B_G),
\]
which closes the concentration chain once posterior-weight error \(\varepsilon_w\) is controlled.

## Remaining Derivation Task
1. Replace informal \(\varepsilon_w\) control with explicit high-probability bounds from regime decoding.
2. Combine oracle Bernstein radius and perturbation radius into one theorem-ready statement.
3. Plug resulting bound into Step-39/41 sample complexity constants.
