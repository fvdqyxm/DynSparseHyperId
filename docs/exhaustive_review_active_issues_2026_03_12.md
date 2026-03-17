# Exhaustive Active-Issue Review (Research Rigor Pass)

Date: 2026-03-12

## Scope
This review targeted "active issues" with strict separation between:
1. in-repo fixable issues (algorithm, logic, tests, reproducibility), and
2. external blockers (datasets, mentor feedback, submission systems).

## Active Issues Found and Fixed
1. **Degenerate support collapse in upgraded multi-regime recovery**
   - Symptom: improved regime decoding but near-zero support-F1 in some upgraded runs.
   - Root cause: sparse refit candidate selection could prefer over-regularized all-zero supports.
   - Fixes:
     - added support-cardinality diagnostics (`support_nnz`);
     - added anti-collapse rescue refit with lower regularization when support is empty;
     - added minimum-support gating in candidate selection.
   - Files:
     - `code/models/phase0_baselines.py`
     - `code/models/phase2_step67_multiregime_upgrade.py`
     - `tests/test_phase2_multiregime_upgrade.py`

2. **Initialization sophistication gap**
   - Symptom: earlier strategy set was limited and did not enforce temporal persistence explicitly.
   - Fixes:
     - added `local_ar_gmm_sticky` and `residual_gmm_sticky` initialization strategies;
     - benchmarked expanded strategy set with deterministic artifact outputs.
   - Files:
     - `code/models/phase0_baselines.py`
     - `code/models/phase2_step67_init_benchmark.py`
     - `results/phase2_step67_init_benchmark_v2/metrics_summary.json`

3. **Infrastructure noise from global plotting import**
   - Symptom: non-plot experiment scripts triggered Matplotlib/font-cache warnings at import time.
   - Root cause: `matplotlib.pyplot` imported globally in `phase0_baselines.py`.
   - Fix:
     - moved plotting imports into plotting-only functions.
   - Effect:
     - cleaner non-plot runs and reduced side-effect risk.

## Verification Evidence
1. Unit tests:
   - `venv/bin/python -m unittest discover -s tests -v` -> **34/34 passed**.
2. Logic audits:
   - `venv/bin/python code/models/schema_logic_audit.py` -> passed.
   - `venv/bin/python code/models/assumption_literature_audit.py` -> passed.
3. New empirical artifact:
   - `results/phase2_step67_multiregime_upgrade_v2_fastcheck/metrics_summary.json`.
4. Multi-seed upgraded check:
   - `results/phase2_step67_multiregime_upgrade_v2_multiseed/metrics_summary.json`.
4. Regression protection:
   - new tests prevent reintroduction of zero-support collapse behavior in v2 fastcheck.

## Remaining Non-Fixable Blockers (External)
1. Phase 3 real-data steps (68-76): blocked by unavailable local dataset roots.
2. Phase 1 step 37/38: blocked by mentor/prof feedback dependency.
3. Phase 4 step 132/133/134: blocked by external human and submission workflows.

## Why This Matters for Whitepaper Quality
1. Removes a key artifact-risk pattern (false gains from degenerate supports).
2. Narrows methodological uncertainty to a concrete calibration frontier instead of broad pipeline fragility.
3. Converts "we think it works" into auditable, reproducible evidence with explicit negative-result boundaries.
4. Strengthens credibility of theory-to-algorithm narrative by aligning claims with measured behavior.
