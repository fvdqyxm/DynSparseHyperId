# Theorem 1 Draft Notes (Global Identifiability)

## Candidate Statement
Under A1-A6 (see `proofs/latex/master.tex`), the latent regime-switching higher-order model is globally identifiable up to:
1. permutation of regimes,
2. representation-equivalent latent symmetries.

## Decomposition Strategy
1. Prove k=2 identifiability (base model).
2. Show k=3 operator contributes additional identifiable moments/features under incoherence.
3. Show combined parameterization remains injective modulo symmetries.
4. Quantify regime decoding stability via eigengap + emission-separation terms.

## Proof Dependency Graph
1. Lemma L1: regime path identifiability from separated emission families.
2. Lemma L2: support uniqueness for sparse operators under restricted eigenvalue and beta-min.
3. Lemma L3: higher-order feature map injectivity on sparse class.
4. Lemma L4: mixing/eigengap-driven regime posterior stability and effective sample size.
5. Theorem T1 from L1+L2+L3+L4 + symmetry quotient argument.

## Working Artifact Links
1. k=2 base identifiability scaffold: `docs/k2_identifiability_proof_sketch.md`.
2. k=3 extension logic: `docs/k3_identifiability_extension_notes.md`.
3. Regime separation eigengap argument: `docs/regime_separation_eigengap_argument.md`.
4. Key hyperedge irrepresentable lemma candidate: `docs/hyperedge_irrepresentable_lemma.md`.

## Critical Failure Modes to Exclude
1. Regime overlap (small $\Delta_\Theta$) causing non-identifiable mixtures.
2. Design collinearity violating sparse support uniqueness.
3. Hyperedge aliasing in feature map leading to same emissions from distinct supports.

## Evidence Requirements Before Claiming T1
1. Analytical: complete statement+proof with assumptions explicitly checkable.
2. Simulation: stress tests where assumptions are intentionally violated, showing expected theorem failure.
3. Reporting: theorem claim in paper must include "up to" symmetries and assumption qualifiers.
