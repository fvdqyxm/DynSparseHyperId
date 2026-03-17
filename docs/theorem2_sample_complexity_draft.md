# Step 39 Working Draft: Theorem 2 (Sample Complexity)

Date: 2026-03-12
Status: Drafted (initial theorem form)

## Target Objects
Estimate:
1. regime-conditioned sparse operators \((A_r,H_r)\),
2. transition matrix \(\Pi\),
3. support sets \(\mathrm{supp}(H_r)\),
from observed \(y_{1:T}\).

## Draft Theorem 2 Statement (Working)
Under A1--A6, fixed interaction order \(k=3\), and suitable regularization
\(\lambda_H \asymp \sqrt{\log M_3 / T_{\mathrm{eff}}}\), there exist constants \(C,c>0\)
such that if
\[
T \ge C\,\tau_{\mathrm{mix}}\,\kappa_0^{-2}\,s\,\log(M_3 K/\delta)\,\Delta_{\min}^{-2},
\]
then with probability at least \(1-\delta\):
1. exact support recovery holds for each regime (up to permutation),
2. \(\|\hat H_r - H_r^\star\|_F\) and \(\|\hat A_r - A_r^\star\|_F\) are bounded at the expected high-dimensional rate,
3. transition estimation error \(\|\hat\Pi-\Pi^\star\|_F\) is controlled by \(\tilde O((KT_{\mathrm{eff}})^{-1/2})\).

Here:
- \(s\): max regime support size,
- \(M_3=\binom{N}{2}\): triplet feature count per target,
- \(\tau_{\mathrm{mix}}\): latent-chain mixing penalty,
- \(\kappa_0\): restricted eigenvalue constant,
- \(\Delta_{\min}\): minimum regime emission separation.

## Interpretation
1. Polynomial in structural hardness terms \((s,\kappa_0^{-1},\Delta_{\min}^{-1})\).
2. Logarithmic in ambient combinatorial index \((M_3,K,1/\delta)\).
3. Dependence correction enters through \(\tau_{\mathrm{mix}}\) and effective sample size.

## Required Proof Ingredients
1. Regime decoding concentration bound with eigengap/separation dependence.
2. Group-sparse recovery bound under dependent design and irrepresentable geometry.
3. Error-propagation control from posterior regime uncertainty into operator estimation.
4. Union bound/control across regimes and hyperedge groups.

## Claim-Safe Caveat
This is a theorem form candidate; constants and exact exponents remain to be proved. No publication claim should treat this as established until proof completion.
