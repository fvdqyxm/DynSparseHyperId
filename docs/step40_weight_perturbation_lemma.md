# Step 40 Supplement: Oracle-to-Inferred Weight Perturbation Lemma (Draft)

Date: 2026-03-12
Status: Drafted

## Objective
Complete Step-40 concentration chain by quantifying the gap between:
1. oracle regime weights \(w_t^\star\), and
2. inferred regime weights \(\hat w_t\).

## Quantity
For centered matrices \(G_t := \Psi_t\Psi_t^\top - \mathbb{E}[\Psi_t\Psi_t^\top]\),
control
\[
\left\|\frac{1}{T}\sum_{t=1}^T (\hat w_t - w_t^\star) G_t\right\|_{op}.
\]

## Working Lemma
Assume:
1. \(|\hat w_t - w_t^\star| \le \varepsilon_w\) uniformly (or in high-probability average),
2. \(\|G_t\|_{op} \le B_G\) almost surely (or sub-exponential tail with bounded envelope),
3. weak dependence/mixing for \(G_t\).

Then
\[
\left\|\frac{1}{T}\sum_{t=1}^T (\hat w_t - w_t^\star) G_t\right\|_{op}
\le
\varepsilon_w \cdot \frac{1}{T}\sum_{t=1}^T \|G_t\|_{op}
\approx O(\varepsilon_w B_G),
\]
with concentration-refined versions replacing the empirical average by high-probability bounds.

## Concentration Chain Closure
1. Oracle term: matrix Bernstein on \(\frac{1}{T}\sum w_t^\star G_t\).
2. Perturbation term: lemma above.
3. Total bound: sum of oracle concentration radius + \(O(\varepsilon_w B_G)\).

## Implication
Step-40's concentration result is valid once posterior-weight error \(\varepsilon_w\) is controlled by regime decoding theory (Step 34/L4 path).

## Remaining Formal Gap
Need explicit high-probability control of \(\varepsilon_w\) from forward-backward posterior under finite separation and mixing constants.
