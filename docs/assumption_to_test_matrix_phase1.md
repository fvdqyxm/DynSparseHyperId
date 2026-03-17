# Assumption-to-Test Matrix (Phase 1)

This matrix ties theoretical assumptions to executable falsification tests.

| Assumption | Meaning | Empirical Proxy/Test | Literature Anchor Gate | Current Status |
|---|---|---|---|---|
| A1 Controlled sparsity | True regime hyperedge support is sparse | `k3` support density in synthetic generators (`edge_prob`) with seed sweeps | `results/rigor_checks/assumption_literature_audit.json` must pass | Partially enforced (empirical); literature gate enforced |
| A2 Regime separation | Distinct regime emissions/transitions | `regime_support_diff_rate` and Frobenius contrast checks in switching simulations | `results/rigor_checks/assumption_literature_audit.json` must pass | Enforced in simulation + literature gate |
| A3 Noise regularity | Sub-Gaussian bounded noise | Gaussian noise sweeps (`obs_noise` and `sigma`) + high-noise degradation checks | `results/rigor_checks/assumption_literature_audit.json` must pass | Enforced + literature gate |
| A4 Hyperedge incoherence | Design is not collinear on support | Adversarial permutation controls; future: RE/irrepresentable diagnostics | `results/rigor_checks/assumption_literature_audit.json` must pass | Partial (needs direct RE stats) + literature gate |
| A5 Mixing / effective sample size | Markov chain explores regimes sufficiently | Transition self-probability constraints + per-regime sample count floors | `results/rigor_checks/assumption_literature_audit.json` must pass | Enforced + literature gate |
| A6 Beta-min | Nonzero edges large enough above estimation noise | `min_abs_weight` floors in LDS; future explicit triplet beta-min tracking | `results/rigor_checks/assumption_literature_audit.json` must pass | Partial (triplet beta-min TODO) + literature gate |

## Immediate Additions Needed
1. Add explicit restricted-eigenvalue diagnostics for `phi(y)` in k=3 generator.
2. Log per-regime effective sample size and dwell-time concentration bounds.
3. Add beta-min histogram artifacts to all synthetic runs.
