# OR PhD Mastery Standard (Fixed Version)

Last updated: 2026-03-16

## Verdict
Completing only the current linked problem sets is strong coursework prep, but not sufficient by itself for "learn all 32 classes very well" at OR-PhD research depth.

This fixed standard upgrades the requirement from "done psets" to "research-ready mastery."

## What "truly very well" means (OR PhD level)

You pass only if all 5 conditions are met:

1. Problem depth
- Complete all linked psets in [problem_set_links_coverage.md](/Users/keshavramamurthy/Berkeley/research/docs/problem_set_links_coverage.md) with full writeups (not sketch answers).
- For proof-heavy classes, at least 70% of solutions must be formal proof quality.

2. Timed exam performance
- For each core cluster, complete 2 timed closed-notes exams (or equivalent timed pset blocks).
- Target: >= 80% average under time pressure.

3. Implementation competency
- For optimization/stochastic/numerical/ML classes, implement core algorithms from scratch and verify against known baselines.
- No black-box-only submissions.

4. Modeling and transfer
- Solve open-ended modeling tasks where formulation is not given.
- At least 1 transfer problem per class: take a method from class A and apply to class B domain.

5. Research extension
- For each class, complete one "extension problem": strengthen theorem assumptions, derive a variant algorithm, or run a nontrivial empirical stress test.

## Why this fixes the gap
- Removes the "I solved fixed-format homework so I’m done" failure mode.
- Enforces qual-like pressure, proof rigor, and research behavior.
- Aligns with what OR PhD qualifiers and first-year research actually demand.

## Class-level gates (must satisfy all listed gates)

Gate legend:
- `P`: All linked psets completed with full solutions
- `E`: Timed exam block(s)
- `I`: Implementation project(s)
- `M`: Open-ended modeling case(s)
- `R`: Research extension note

### Pure Math / Analysis
- `MATH 104`: `P E R`
- `MATH 105`: `P E R`
- `MATH 185`: `P E R`
- `MATH 202A`: `P E R`
- `MATH 202B`: `P E R`
- `MATH 220`: `P E I R`

### Algebra & Topology
- `MATH 113`: `P E R`
- `MATH 142`: `P E R`
- `MATH 142B`: `P E R`
- `MATH 110`: `P E I R`

### Probability & Stochastic Processes
- `STAT 150`: `P E I M R`
- `STAT 205A`: `P E R`
- `STAT 205B`: `P E R`
- `IEOR 263A`: `P E I M R`
- `IEOR 263B`: `P E I M R`
- `STAT 210A`: `P E R`
- `STAT 210B`: `P E R`

### Optimization & OR
- `IEOR 160`: `P E I M R`
- `IEOR 162`: `P E I M R`
- `IEOR 169`: `P E I M R`
- `IEOR 261`: `P E I M R`
- `IEOR 266`: `P E I M R`
- `IEOR 221`: `P E I M R`
- `IEOR 222`: `P E I M R`
- `IEOR 180`: `P E I M R`
- `IEOR 269`: `P E I M R`

### High-Dimensional Stats & ML Theory
- `STAT 260`: `P E I R`
- `CS 189`: `P E I R`
- `CS 170`: `P E I R`

### Computational & Systems
- `CS 61C`: `P E I`
- `MATH 128A`: `P E I R`
- `MATH 128B`: `P E I R`

## Cluster capstones (required)

1. Convex/LP/IP Capstone
- Implement and benchmark: simplex, interior-point, projected gradient, branch-and-bound/cuts.
- Include complexity/runtime scaling plots.

2. Stochastic Processes + Simulation Capstone
- Build a queueing or inventory stochastic simulator.
- Validate against theoretical stationary distributions / performance bounds.

3. Statistical Inference Capstone
- Prove one concentration/empirical-process style result and test finite-sample behavior in code.

4. ML Theory Capstone
- Derive a generalization bound variant and compare to empirical curves on synthetic + real data.

5. Numerical Methods Capstone
- Stability + conditioning study with reproducible experiments and failure-case analysis.

## Minimum evidence package (deliverables)

Per class:
- `solutions/<class>/` complete writeups
- `timed/<class>/` timed attempts with scores and postmortems
- `extensions/<class>/` 1-2 page research extension note

For implementation classes:
- `code/<class>/` reproducible scripts/notebooks
- `results/<class>/` tables/figures + error/runtime analysis

Global:
- `docs/mastery_log.md` with weekly progress + unresolved weaknesses
- `docs/qual_readiness_report.md` with area-by-area pass/fail

## Pass/fail definition

You can claim "learned very well" only when:
- all class gates are complete,
- all 5 capstones are complete,
- and qual-readiness report shows no failed core area.

If any area fails timed performance, proof quality, or transfer tasks, mastery is not yet complete.
