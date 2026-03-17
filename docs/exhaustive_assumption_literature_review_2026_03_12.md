# Exhaustive Assumption-Literature Review (A1-A6)

Date: 2026-03-12
Purpose: enforce a top-researcher logic standard that separates (i) assumption-level validity from (ii) integrated-theorem novelty.

## Why This Review Was Necessary
The project risk is not only coding bugs; it is epistemic overclaiming. A mathematically serious white paper needs explicit proof boundaries:
1. what is already standard in the literature,
2. what transfers with caveats,
3. what is actually new and still unproven.

## What Was Added
1. `docs/assumption_literature_matrix.csv`
   - machine-readable A1-A6 mapping,
   - three primary sources per assumption,
   - explicit transferability caveats,
   - mandatory "integrated theorem open" status tags.
2. `docs/phase1_assumption_literature_summaries_round2.md`
   - targeted paragraph-level summaries for additional assumption-critical papers,
   - each summary includes relevance and transfer limits.
3. `code/models/assumption_literature_audit.py`
   - executable gate that fails if assumptions lack sources/caveats,
   - checks claim-safe language (open integrated theorem),
   - checks links between assumptions, artifacts, and LaTeX assumptions.

## Logic Check (Research-Integrity)
1. A1-A6 are each supported by established theory families.
2. No source proves the full integrated theorem in our exact setting.
3. Therefore novelty claim is structurally valid only as an integration theorem/proof objective.
4. Any statement implying full theorem completion before proofs are done is invalid and blocked by audit gates.

## Why This Matters for a Future White Paper
1. Reviewers can trace each assumption to classical precedents without conflating model classes.
2. The paper can present novelty cleanly: integrated sparse high-order latent-switching identifiability/recovery.
3. Failure modes are pre-specified, reducing the chance of accidental overfitting narratives.

## Remaining Risk and Next Fundamental Work
1. Step 28 remains in progress until all 30 sources are fully summarized.
2. Step 32/35 proof artifacts must convert from sketches to complete theorems/lemmas.
3. Assumption A4 (hyperedge incoherence analog) still needs a model-specific formal definition and verification statistic.
