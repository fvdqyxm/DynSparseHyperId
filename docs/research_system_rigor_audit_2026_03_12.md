# Research System Rigor Audit (Code + Logic + Schema)

Date: 2026-03-12

## Goal
Prevent hidden bugs and conceptual inconsistencies from producing misleadingly strong results.

## Added Rigor Layers
1. Adversarial controls (`code/models/rigor_adversarial_checks.py`)
- k=3 permutation control (break feature-target alignment).
- k=3 null-structure control (zero true hyperedges).
- switching random-label control (oracle labels must dominate random labels).
- deterministic repeat check.

2. Schema/logic coherence checks (`code/models/schema_logic_audit.py`)
- tracker consistency for completed steps.
- claim registry evidence path validity.
- formula-traceability document completeness.
- observability-to-claim alignment check.
- biological realism proxy check in Wilson-Cowan pipeline.

3. Integrated gating
- `scripts/run_phase0_checks.sh` now runs 7 stages including both audits.
- `tests/test_phase0_steps.py` enforces adversarial and schema-level pass conditions.

## Results
1. Adversarial checks: pass
- k=3 baseline F1: ~0.86
- k=3 permutation F1: 0.0
- k=3 null FPR: 0.0
- switching oracle-vs-random label gap: strong (F1 gap ~0.44, acc gap ~0.49)

2. Schema/logic audit: pass
- tracker statuses coherent with notes.
- claim evidence paths resolvable.
- formula-traceability audit includes required caveats.
- low-observability Wilson condition aligns with conservative claim stance.

3. End-to-end gate: pass
- full 7-stage command passes and 19 unit tests pass.

## Meaning for Scientific Viability
1. We now have machine-enforced protection against common false-positive pathways:
- leakage,
- label hacks,
- unsupported claims,
- tracker/doc drift.

2. The project remains ambitious but grounded:
- strong in pairwise/switching synthetic regimes,
- explicitly conservative where observability is weak,
- formula-level boundaries are documented.

## Remaining High-Risk Items
1. Sparse+low-rank CPW-style decomposition is not implemented yet.
2. Turnbull nsRGH likelihood/Bookstein machinery is not implemented yet.
3. k=3 module is currently a surrogate inverse benchmark, not full latent-space hypergraph posterior inference.
