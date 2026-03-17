# Step 34 Working Note: Regime Separation via Eigenvalue-Gap Argument

Date: 2026-03-12
Status: In Progress

## Objective
Translate regime-separation assumptions into quantifiable filtering/decoding stability using transition-matrix spectral gap and emission contrast.

## Setup
Let \(\Pi\) be the latent transition matrix with stationary distribution \(\pi\).
Define spectral gap (reversible surrogate):
\[
\gamma_{\Pi} := 1 - |\lambda_2(\Pi)|.
\]
Let emission separation between regimes \(r\neq r'\) be
\[
\Delta_{rr'} := \mathrm{KL}\big(p_{\Theta_r}(y_t\mid y_{t-1})\;\|\;p_{\Theta_{r'}}(y_t\mid y_{t-1})\big).
\]
Assume \(\Delta_{\min} := \min_{r\neq r'} \Delta_{rr'} > 0\).

## Logic Chain
1. Positive \(\gamma_{\Pi}\) implies exponential forgetting/mixing in latent chain.
2. Positive \(\Delta_{\min}\) implies distinguishable regime-conditioned one-step emissions.
3. Jointly, posterior regime assignment errors decay with effective sample size:
\[
\mathbb{P}(\hat z_t \neq z_t) \lesssim \exp\{-c\,T_{\mathrm{eff}}\,\Delta_{\min}\},
\]
where \(T_{\mathrm{eff}}\) degrades with mixing time \(\tau_{\mathrm{mix}}\approx O(\gamma_{\Pi}^{-1})\).

## Working Claim (Qualitative Bound)
A sufficient scaling regime is
\[
T \gtrsim \tau_{\mathrm{mix}}\,\Delta_{\min}^{-1}\,\log(K/\delta),
\]
for stable regime decoding at confidence level \(1-\delta\) up to constant/model terms.

## Why This Matters for Theorem 1/2
1. It converts A2/A5 into explicit finite-sample dependencies.
2. It isolates a core bottleneck term: \(\gamma_{\Pi}^{-1}\Delta_{\min}^{-1}\).
3. It prevents vague statements like "regimes are separated" without quantitative consequence.

## Caveat
This note gives a proof direction, not a complete bound. Final theorem must specify:
1. exact divergence metric for autoregressive emissions,
2. required regularity for dependent covariates,
3. constants and remainder terms.

## Empirical Proxy Alignment
Current synthetic proxies already logged:
1. `regime_contrast_fro_ratio` and `regime_support_diff_rate` in switching outputs,
2. degradation curves vs observation noise in switching sweep.
These are not theorem constants, but they are consistent diagnostics for A2/A5 violations.
