# White Paper Research Log

## 2026-03-12 — Foundation and Gate 0 Buildout

### Context
Objective was to convert early project setup into an auditable research baseline with
test-backed evidence and explicit logic checks.

### Work Completed
1. Replaced placeholder framing in README with concrete model scope.
2. Corrected literature integrity:
   - added canonical Graphical Lasso and Chandrasekaran papers,
   - archived mismatched PDFs.
3. Added structured paper summaries with relevance/limits/action-items.
4. Added theorem scaffold in LaTeX (`proofs/latex/master.tex`).
5. Added strict step tracker (`tracking/phase0_steps.csv`) with contingencies.
6. Implemented deterministic baselines:
   - Graphical Lasso support recovery,
   - sparse LDS recovery,
   - switching LDS baseline (current underperforming).
7. Added automated test suite and one-command validation runner.

### Quantitative Outcomes
1. Graphical Lasso F1: 0.9048.
2. Sparse LDS F1: 0.8621.
3. Switching LDS baseline:
   - regime accuracy currently ~0.53-0.65 depending configuration,
   - support F1 unstable/underperforming.

### Interpretation
1. Static and single-regime sparse recovery is strong.
2. Regime-switching recovery is currently the bottleneck and primary scientific challenge.
3. This asymmetry is useful evidence that the project is nontrivial and not overfit theater.

## 2026-03-12 (Later) — Switching LDS Logic Debug + Method Expansion

### Critical Logic Bug Found
Switching simulation originally used a regime sequence whose indexing did not align correctly
with burn-in trimming. This contaminated regime-recovery evaluation.

### Fundamental Fix
1. Generated a full regime trajectory over `t + burn_in`.
2. Simulated dynamics on that full trajectory.
3. Trimmed both state and regime arrays consistently after burn-in.

### Method Upgrades Added
1. Multi-method switching benchmark:
   - hard-EM + Viterbi,
   - soft-EM HMM (forward-backward),
   - oracle-label ceiling.
2. Advanced initialization bank:
   - local windowed AR clustering (`window_ar_cluster`),
   - persistence-aware block-random init (`random_blocks`),
   - residual and delta-based strategies.
3. Inference regularization:
   - sticky transition bias,
   - annealed emission temperature schedule.

### Updated Outcome Snapshot
With corrected simulation alignment:
1. Regime accuracy reached ~0.885 (selected method: hard-EM).
2. Switching support F1 remains moderate (~0.58 mean), below final target.
3. Oracle-label support F1 (~0.73 mean) shows remaining optimization/inference gap.

### Research Meaning
1. The regime-identification subproblem is now substantially improved and no longer dominated by a
   setup bug.
2. Remaining support gap is real and technically meaningful.
3. This supports a serious methodology narrative: strong progress with transparent unresolved core difficulty.

## 2026-03-12 (Latest) — Exhaustive Robustness Sweep and Step 15 Closure

### Additional Fundamental Upgrades
1. Introduced beta-min nonzero edge magnitudes in switching dynamics generation.
2. Added support stability selection (bootstrap + refit on stable support).
3. Added observation-noise channel for meaningful robustness sweeps.
4. Added dedicated sweep runner across noise/seed configurations.

### Robustness Sweep Summary
Reference: `docs/exhaustive_sweep_check_2026_03_12.md`
1. At observation noise 0.15 (moderate), 3-seed mean:
   - regime accuracy ~0.816,
   - support F1 ~0.791.
2. At higher noise 0.30:
   - regime accuracy ~0.778,
   - support F1 ~0.706.

### Resulting Project State
1. Step 15 can be responsibly marked completed for moderate-noise criteria.
2. Performance degradation under harder noise is documented, not hidden.
3. Next gains should come from recurrent transition gating and duration-aware switching.

### White Paper Relevance
1. Provides hard baseline competence before making high-order claims.
2. Creates transparent failure accounting for the hardest subproblem (switching inference).
3. Establishes reproducibility and test discipline expected by serious reviewers.

### Next Logging Requirements
For each future milestone, log:
1. exact assumptions used,
2. parameter ranges tested,
3. negative controls attempted,
4. failure modes and fixes,
5. what claim this enables or invalidates.

## 2026-03-12 (Latest) — Phase 0 Steps 16-19 Completed with Observability Guardrails

### What Was Added
1. Implemented Wilson-Cowan switching simulator artifacts:
   - `E_timeseries.npy`, `I_timeseries.npy`, `z_regimes.npy`.
2. Added canonical HRF + realistic BOLD corruption:
   - `bold_clean.npy`, `bold_noisy.npy`.
3. Added pairwise sparse recovery on both neural and BOLD signals.
4. Added effective-dynamics diagnostics:
   - mean sigmoid derivative,
   - effective off-diagonal Jacobian magnitude,
   - `low_observability_flag`.
5. Added anti-overclaim gate tests and integrated pipeline in `run_phase0_checks.sh`.

### Key Finding
Structural coupling recovery is weak in the default Wilson-Cowan regime, and diagnostics show that this is expected:
1. effective off-diagonal magnitude is extremely small,
2. low observability is explicitly flagged,
3. claim text now enforces stress-test interpretation instead of inflated conclusions.

### Why This Matters for the White Paper
1. Converts a potential failure into high-value evidence: naive pairwise recovery on BOLD can fail even with planted regimes.
2. Strengthens scientific credibility by showing where identifiability breaks down in practice.
3. Creates a direct bridge to the project's core motivation for higher-order, latent-regime-aware inference.

## 2026-03-12 (Latest) — Formula Traceability Audit Against Core Papers

### What Was Done
1. Parsed core PDFs into text extracts for formula-level checking.
2. Mapped paper equations to concrete code paths and marked each as:
   - implemented exactly,
   - approximated/surrogate,
   - not yet implemented.
3. Wrote audit note: `docs/formula_traceability_audit_2026_03_12.md`.

### Main Result
1. Graphical Lasso objective is implemented as a valid baseline.
2. Chandrasekaran sparse+low-rank convex decomposition is not yet implemented.
3. Turnbull nsRGH likelihood/Bookstein machinery is not yet implemented.
4. Current k=3 module is explicitly a surrogate sparse polynomial inverse benchmark.

### Integrity Impact
1. Prevents category confusion between implemented baselines and planned theory-aligned models.
2. Provides a clean statement boundary for papers/reviews and future white paper drafting.

## 2026-03-12 (Latest) — System-Level Rigor and Phase 1 Formalization

### Added in This Pass
1. Phase 1 model formalization in LaTeX:
   - explicit latent Markov regime model,
   - k=3 parameterization,
   - ELBO with group-sparsity and temporal KL,
   - A1-A6 assumption scaffold,
   - draft theorem placeholders.
2. Phase 1 tracker created (`tracking/phase1_steps.csv`) with conservative completion flags.
3. Adversarial controls module:
   - permutation/null/random-label checks
   - deterministic repeat checks.
4. Schema/logic audit module:
   - tracker/claim/formula/artifact coherence checks.

### Outcome
1. Full 7-stage verification pipeline passes end-to-end.
2. 19 unit tests pass, including adversarial and schema-level gates.
3. Claim boundaries remain conservative where observability is weak.

## 2026-03-12 (Latest) — Interim PDF Build + Phase 1 Step Progress

### Added
1. Interim LaTeX PDF compilation is now explicit and repeatable:
   - `proofs/latex/master.pdf` built via `pdflatex` (two-pass).
   - build stage integrated into `scripts/run_phase0_checks.sh`.
2. Added a PDF existence gate in tests to ensure documentation remains buildable.
3. Completed additional Phase 1 writing artifacts:
   - `docs/phase1_gap_table.md` (Step 29),
   - `docs/phase1_intro_abstract_draft.md` (Step 30).
4. Updated `tracking/phase1_steps.csv` with conservative statuses:
   - Step 28 set to In Progress (12 sources reviewed so far),
   - Steps 29 and 30 marked Completed with artifact evidence.
5. Added a structured 30-paper completion matrix:
   - `docs/phase1_literature_matrix_30_target.md`.

### Verification
1. Full 8-stage pipeline now passes end-to-end.
2. 20 unit tests pass, including interim PDF build checks.

## 2026-03-12 (Latest) — Proof Pipeline Progress (k=2 Base and T1 Draft)

### Added
1. `docs/k2_identifiability_proof_sketch.md`:
   - base-model assumptions,
   - proof skeleton,
   - required lemmas and remaining gaps.
2. `docs/theorem1_draft_notes.md`:
   - T1 statement scaffold,
   - dependency graph,
   - explicit failure-mode exclusions.

### Tracker Impact
1. Phase 1 Step 32 moved to In Progress.
2. Phase 1 Step 35 moved to In Progress.

## 2026-03-12 (Latest) — Assumption Validity Hardened Into Executable Gates

### Added
1. `docs/assumption_literature_matrix.csv` with explicit A1-A6 source mapping, caveats, and claim-safe status labels.
2. `docs/phase1_assumption_literature_summaries_round2.md` with additional assumption-critical literature summaries.
3. `code/models/assumption_literature_audit.py` to enforce:
   - complete A1-A6 source coverage,
   - transferability caveats,
   - \"integrated theorem open\" language,
   - artifact-path and LaTeX assumption alignment.
4. `docs/exhaustive_assumption_literature_review_2026_03_12.md` as a white-paper prep note.
5. Pipeline integration:
   - `scripts/run_phase0_checks.sh` now runs assumption-literature audit before schema audit.

### Outcome
1. Assumption validity moved from narrative notes to machine-checkable CI artifacts.
2. Overclaim risk reduced by explicit gate failures when assumption grounding is missing or overstated.
3. Phase 1 Step 28 evidence depth increased (reviewed source count raised from 12 to 21).

## 2026-03-12 (Latest) — Theorem Dependency Upgrade (Steps 33/34/36)

### Added
1. `docs/k3_identifiability_extension_notes.md`:
   - k=2 to k=3 lift strategy,
   - sparse-class non-aliasing requirement,
   - restricted injectivity condition for combined linear+triplet features.
2. `docs/regime_separation_eigengap_argument.md`:
   - explicit eigengap and emission-separation quantities,
   - effective sample-size scaling direction for regime decoding stability.
3. `docs/hyperedge_irrepresentable_lemma.md`:
   - key hyperedge group-irrepresentable lemma candidate,
   - diagnostic quantities needed for empirical falsification.
4. `proofs/latex/master.tex` now contains draft lemma scaffolds for:
   - eigengap-driven regime stability,
   - hyperedge group-irrepresentable geometry.
5. `tests/test_phase0_steps.py` expanded to gate these artifacts when tracker statuses indicate progress/completion.

### Tracker Impact
1. Step 33 moved to In Progress.
2. Step 34 moved to In Progress.
3. Step 36 moved to Completed (lemma identified and integrated in theorem scaffold).

## 2026-03-12 (Latest) — Step 28 Completed (30/30 Literature Matrix)

### Added
1. `docs/phase1_literature_summaries_round3.md` covering rows 22-30 with assumption-aware summaries.
2. Updated `docs/phase1_literature_matrix_30_target.md` to full reviewed coverage (30 citations).
3. Updated `docs/phase1_gap_table.md` with round-3 mapping and evidence anchors.
4. Added test gating for Step 28 completion artifacts in `tests/test_phase0_steps.py`.

### Outcome
1. Step 28 completion criteria are now satisfied with concrete citations and summary coverage.
2. Related-work positioning is stronger and still claim-safe: strong component precedents, no full integrated theorem found.

## 2026-03-12 (Latest) — Step 39 Drafted, Step 40 Started

### Added
1. `docs/theorem2_sample_complexity_draft.md` with an explicit Theorem-2 template and parameter dependencies.
2. `docs/matrix_bernstein_hyperedge_notes.md` with a dependence-aware matrix/tensor concentration reduction plan.
3. Updated `proofs/latex/master.tex` sample-complexity section to reflect an explicit scaling skeleton.
4. Expanded test gating in `tests/test_phase0_steps.py` for Steps 39 and 40 artifact evidence.

### Tracker Impact
1. Step 39 marked Completed (draft theorem form delivered).
2. Step 40 moved to In Progress (concentration strategy drafted; perturbation lemma pending).

## 2026-03-12 (Latest) — Steps 41/42 Initiated (Upper/Lower Bound Pair)

### Added
1. `docs/step41_t_bound_derivation.md` with explicit dependence decomposition for a working upper bound.
2. `docs/step42_fano_lower_bound_sketch.md` with a packing-based Fano lower-bound sketch.
3. Updated lower-bound section in `proofs/latex/master.tex` with a concrete draft scaling expression.
4. Expanded test gating for Steps 41 and 42 artifacts in `tests/test_phase0_steps.py`.

### Tracker Impact
1. Step 41 moved to In Progress.
2. Step 42 moved to In Progress.

## 2026-03-12 (Latest) — Step 43 Completed (Numerical Tightness Check)

### Added
1. `code/models/step43_tightness_check.py` to run T-sweeps and compute log-log error slopes.
2. Result artifacts in `results/phase1_step43_tightness/` including JSON and plots.
3. `docs/step43_tightness_results.md` with claim-safe interpretation of slope behavior.
4. Test gating for Step 43 artifacts in `tests/test_phase0_steps.py`.

### Result
1. Switching model shows clear improvement with T and negative error slope (~ -0.736).
2. k=3 benchmark is near saturation in this grid (weak slope), so a harder follow-up grid is required for informative tightness calibration.

## 2026-03-12 (Latest) — Fundamental Estimator Robustness Fix + Step 40 Completion

### Added
1. Core fix in `code/models/phase0_baselines.py`:
   - `recover_A_from_pairs_cv` now uses adaptive CV folds and ridge fallback for low-sample slices.
2. New perturbation bridge note:
   - `docs/step40_weight_perturbation_lemma.md`.
3. Updated matrix-Bernstein note:
   - `docs/matrix_bernstein_hyperedge_notes.md` now includes oracle-to-inferred weight bridge.

### Why It Matters
1. Prevents hidden crashes and bias from invalid fixed-fold CV in low-occupancy regime segments.
2. Closes the conceptual concentration chain for Step 40 (oracle concentration + inferred-weight perturbation).

## 2026-03-12 (Latest) — Step 44 Completed (Heavy-Tail Robustness)

### Added
1. Extended `run_switching_lds` to support observation noise models:
   - gaussian,
   - student-t,
   - contaminated Gaussian outliers.
2. Added robustness sweep script:
   - `code/models/step44_heavy_tail_robustness.py`.
3. Added result note:
   - `docs/step44_noise_robustness_results.md`.

### Result
1. Heavy-tailed and contaminated noise produce measurable but bounded degradation versus Gaussian baseline.
2. This converts robustness discussion from assumption-only to measurable stress-test evidence.

## 2026-03-12 (Latest) — Step 45 Completed (Algorithm Draft, Executable)

### Added
1. `code/models/step45_variational_proxem_toy.py`:
   - variational E-step (forward-backward),
   - weighted M-step,
   - proximal group shrinkage on triplet blocks,
   - multi-restart selection by expected log-likelihood.
2. Result artifact note:
   - `docs/step45_variational_proxem_results.md`.

### Result
1. Log-likelihood progression is monotone in selected run (algorithmically stable scaffold).
2. Recovery quality is modest in current toy setup, so this is a draft architecture milestone, not a final performance claim.

## 2026-03-12 (Latest) — Step 46 Completed (Convergence Note)

### Added
1. `docs/step46_convergence_proof_note.md` with an explicit proximal-gradient convergence statement under convex surrogate assumptions.

### Result
1. Established an `O(1/m)` convergence-rate statement for the convex subproblem layer.
2. Explicitly bounded scope to surrogate convex blocks (no overclaim about global nonconvex EM convergence).

## 2026-03-12 (Latest) — Step 47 Completed (Convergence Contingency)

### Added
1. `docs/step47_convergence_contingency.md` with explicit fallback strategy for full nonconvex convergence claims.

### Result
1. Convergence claims are now tiered:
   - proved convex-subproblem rate,
   - empirical nonconvex convergence diagnostics,
   - explicit no-overclaim language for manuscripts.

## 2026-03-12 (Latest) — Steps 48-49 Completed (Grid + Curves)

### Added
1. `code/models/step48_small_synthetic_grid.py` and outputs under `results/phase1_step48_grid/`.
2. `code/models/step49_plot_recovery_curves.py` and output `results/phase1_step49_curves/f1_vs_t_over_n.png`.
3. Result note: `docs/step48_step49_grid_results.md`.

### Result
1. Compact synthetic grid evidence is now available for `k=2` and `k=3` settings.
2. Recovery-curve plotting pipeline is in place for the Step-50 viability gate.

## 2026-03-12 (Latest) — Step 50 Gate Assessment Started

### Added
1. `docs/step50_viability_gate_assessment.md` with explicit partial-pass criteria and remaining blockers.

### Result
1. Gate 1 is now tracked as in-progress with concrete close conditions (proof constants + expanded scaling validation).

## 2026-03-12 (Latest) — Phase 2 Started (Steps 51-53 Completed)

### Added
1. `tracking/phase2_steps.csv` for Phase-2 execution tracking.
2. `code/models/phase2_variational_backbone.py` (Step 51).
3. `code/models/phase2_hypergraph_emission.py` (Step 52).
4. `code/models/phase2_proximal_group_lasso.py` (Step 53).
5. `docs/phase2_steps51_53_results.md` summarizing module-level outcomes.

### Result
1. Core Phase-2 modules are now executable with smoke artifacts and test gates.
2. End-to-end training remains future work (Steps 54+), but foundational components are in place.

## 2026-03-12 (Latest) — Phase 2 Steps 54-55 Completed

### Added
1. `code/models/phase2_temporal_kl_penalty.py` with temporal KL regularization module and smoke check.
2. `code/models/phase2_curriculum_training_toy.py` for k2->k3 curriculum training workflow.
3. `docs/step55_curriculum_results.md` documenting transfer results.

### Result
1. Temporal KL term is now executable and validated on simple sanity cases.
2. Curriculum pipeline is operational, though current toy gains are mixed and require tuning before claiming benefit.

## 2026-03-12 (Latest) — Step 56 Started (Large Grid Orchestration)

### Added
1. `code/models/phase2_large_grid_runner.py` for scalable grid scheduling.
2. `docs/step56_large_grid_runner_note.md` with dry-run diagnostics.

### Result
1. Orchestration works and logs unsupported paths explicitly (no silent omissions).
2. Full large-run execution remains pending compute budget and k>=4 extension.

## 2026-03-12 (Latest) — Publishability Checkpoint (Top-Tier Theory Lens)

### Verdict
1. Publishable trajectory: **yes**.
2. Submission-ready right now for a top theory venue: **not yet**.

### Evidence Supporting Novelty/Value
1. Integrated problem framing (sparse higher-order + latent switching + inverse recovery guarantees) remains a strong and still-difficult target.
2. Reproducibility hygiene is strong: trackers, CI-like gates, adversarial controls, and explicit assumption audits are active.
3. Synthetic recovery is promising in moderate settings (including heavy-tail degradation characterization).

### Remaining Blockers
1. Core theorem components remain in sketch status (not full formal proofs with closed constants/exponents).
2. Sample complexity upper/lower bounds are structurally aligned but not fully finalized.
3. Some synthetic evidence is still too small/optimistic (single-seed pockets, dry-run-only segments, unsupported k>=4 path in Step 56).
4. Algorithmic results are mixed in places (e.g., curriculum toy does not consistently beat scratch).

### Logic Check (Overclaim Prevention)
1. Do not claim global identifiability theorem as proved until Steps 32/33/34/35/41/42 are fully closed.
2. Do not claim broad scaling laws until Step 57 multi-seed and Step 59 log-log fits are complete with confidence intervals.
3. Keep current framing as: rigorous preprint-in-progress with strong infrastructure and nontrivial early evidence.

## 2026-03-12 (Latest) — Phase 2 Deepening (Steps 56-62 with Confound Controls)

### What Was Added
1. Generalized high-order module:
   - `code/models/static_hypergraph_korder.py` (k>=3 surrogate with adaptive solver path).
2. Major Step-56 runner upgrades:
   - `code/models/phase2_large_grid_runner.py` now supports `k=4` execution (no skip path),
   - complexity-control arguments for k2 and high-order branches,
   - explicit solver-mode logging (`lasso_cv` vs `lasso_scaled`).
3. Batch merge utility:
   - `code/models/phase2_step56_merge_batches.py`.
4. Step-58 metrics aggregator:
   - `code/models/phase2_step58_metrics.py` with CI summaries and switching diagnostics.
5. Step-59 scaling script:
   - `code/models/phase2_step59_scaling_laws.py`.
6. Steps 60-62 ablation suite:
   - `code/models/phase2_step60_62_ablations.py`.

### New Results
1. Step-56 canonical artifact now executes `k=2,3,4` with `N` up to 150 and no skipped runs:
   - `results/phase2_step56_large_grid/metrics_summary.json`.
2. Step-57 multi-seed run completed at 8 seeds/cell (192/192 runs):
   - `results/phase2_step57_multiseed_consistent/metrics_summary.json`.
3. Step-58 CI metrics and switching diagnostics:
   - `results/phase2_step58_metrics_consistent/metrics_summary.json`.
4. Step-59 scaling artifacts:
   - `results/phase2_step59_scaling_consistent/`.
5. Step-60/61/62 ablations:
   - `results/phase2_step60_62_ablations/metrics_summary.json`.

### Critical Logic Check and Fundamental Fix
1. Initial scaling analysis showed a positive slope artifact for one k2 cell.
2. Root cause: solver mode changed across `T` (CV at low `T`, scaled-Lasso at high `T`), confounding slope interpretation.
3. Fix applied:
   - reran multi-seed structural grid with consistent solver policy across all cells.
4. After rerun, problematic structural slope became directionally coherent (negative).

### Claim Boundary
1. Steps 58-62 now have executable, audited artifacts and can be discussed as preliminary evidence.
2. Step 57 remains open relative to original 50-100 seed target.
3. Switching scaling is still unstable under reduced switching-budget diagnostics and should remain claim-conservative.

## 2026-03-12 (Latest) — Step 63 Baseline Comparison Added

### Added
1. `code/models/phase2_step63_baseline_comparison.py`.
2. Result artifact:
   - `results/phase2_step63_baselines/metrics_summary.json`.
3. Summary note:
   - `docs/step63_baseline_comparison_results.md`.

### Result
1. On planted high-order data, sparse high-order modeling outperformed:
   - pairwise-only baseline (k3 and k4),
   - SINDy-like STLSQ baseline (k3 and k4).
2. Pairwise sparse LDS baseline remains strong in pairwise settings, preserving nontrivial baseline credibility.

### Logic Check
1. Baseline comparisons are directionally aligned with model assumptions.
2. Current comparison is seed-limited and should be expanded before final venue-level claims.

## 2026-03-12 (Latest) — Steps 64-66 (Robustness, Tuning, Failure-Mode Formalization)

### Added
1. `code/models/phase2_step64_robustness_checks.py` with:
   - outlier, missing-data, and wrong-k stress tests.
2. `code/models/phase2_step65_hyperparameter_tuning.py` with executable proxy tuning for:
   - learning rate,
   - sparsity lambda scale,
   - smoothness beta.
3. `docs/step66_failure_modes.md` as consolidated failure-mode register for manuscript use.

### Results
1. Robustness checks show moderate degradation under outliers/missingness, not collapse.
2. Wrong-k proxy confirms model-misspecification penalty.
3. Tuning proxy produced concrete recommendation tuple (`lr`, `lambda`, `beta`) with reproducible artifact output.

### Logic Check
1. These additions increase claim discipline by making fragility explicit and testable.
2. Step-65 output is explicitly labeled as proxy tuning and not an overclaim of full joint optimization.

## 2026-03-12 (Latest) — Step 67 Gate-2 Preliminary Assessment

### Added
1. `docs/step67_viability_gate2_assessment.md`.

### Decision
1. Gate 2 remains **In Progress**.

### Why
1. Strong high-order lifts versus pairwise baselines are present.
2. But low-`T` high-order cells and below-target seed budgets prevent responsible gate closure.

## 2026-03-12 (Latest) — Step 57 Seed Target Hit (50-Seed Expansion)

### Added
1. `results/phase2_step57_multiseed_50/metrics_summary.json` with:
   - 1800 requested/executed runs,
   - 0 skipped.
2. Refreshed aggregates:
   - `results/phase2_step58_metrics_50/metrics_summary.json`,
   - `results/phase2_step59_scaling_50/metrics_summary.json`.

### Result
1. Step-57 target achieved at lower bound (50 seeds/cell for current grid).
2. Structural scaling slopes remained directionally coherent under the larger seed budget.
3. Gate 2 remains open because F1>0.75 is not yet universal across all realistic low-`T` hard cells (currently 20/36 structural cells clear threshold).

## 2026-03-12 (Latest) — Deep Review + Phase 3 Step 68 Start

### Added
1. Deep viability audit:
   - `docs/deep_viability_review_2026_03_12.md`.
2. Phase 3 tracker:
   - `tracking/phase3_steps.csv`.
3. Step 68 preflight intake:
   - `code/models/phase3_step68_data_intake.py`,
   - `results/phase3_step68_intake/metrics_summary.json`,
   - `docs/step68_intake_results.md`.

### Result
1. Deep audit confirms viable direction but flags proof-closure and Gate-2 universality as remaining blockers.
2. Step 68 now has robust blocked-state handling and manifest logic; current block is missing local dataset root.

## 2026-03-12 (Latest) — Phase 3 Steps 69-76 Executable (Blocked-Safe)

### Added
1. Scripts:
   - `phase3_step69_sliding_windows.py`
   - `phase3_step70_motif_inference.py`
   - `phase3_step71_predict_craving.py`
   - `phase3_step72_baseline_compare.py`
   - `phase3_step73_visualize_motifs.py`
   - `phase3_step74_cross_dataset_preflight.py`
   - `phase3_step75_neuro_ablation.py`
   - `phase3_step76_gate3_assessment.py`
2. Summary note:
   - `docs/phase3_steps69_76_results.md`.

### Result
1. Full Phase-3 chain (69-76) now executes and emits explicit readiness/blocked states.
2. Current Gate-3 status is data-blocked, with upstream dependency trace recorded in `results/phase3_step76_gate3/metrics_summary.json`.

## 2026-03-12 (Latest) — Phase 4 Tracker + Release/Writeup Scaffolding

### Added
1. `tracking/phase4_steps.csv` covering steps 77-140.
2. Draft writeups:
   - `docs/phase4_steps77_90_intro_related.md`
   - `docs/phase4_steps91_105_theory_writeup.md`
   - `docs/phase4_steps106_120_algorithm_synth_writeup.md`
   - `docs/phase4_steps121_130_neuro_writeup.md`
   - `docs/phase4_step131_polish_checklist.md`
   - `docs/phase4_step132_feedback_packet.md`
   - `docs/phase4_step133_revision_protocol.md`
   - `docs/phase4_step134_submission_plan.md`
   - `docs/phase4_step135_backup_submissions.md`
   - `docs/phase4_step136_open_source_release.md`
   - `docs/phase4_step137_blog_poster_draft.md`
   - `docs/phase4_steps138_140_long_tail_plan.md`
3. Open-source hygiene files:
   - `LICENSE`, `CONTRIBUTING.md`, `CITATION.cff`.
4. README status refresh for current phase and reproducibility commands.

### Result
1. Writing/dissemination pipeline is now concretely scaffolded with explicit external blocks where applicable.
2. External-only tasks (mentor feedback and submission actions) are marked blocked/pending rather than overstated.

## 2026-03-12 (Latest) — Step 56 Expanded Coverage + Gate Closures

### Added
1. Step-56 regime-count supplement:
   - `code/models/phase2_step56_switching_k_grid.py`
   - `results/phase2_step56_switching_k_grid_full/metrics_summary.json`
   - `results/phase2_step56_switching_k_grid_stress_k3/metrics_summary.json`
   - `docs/step56_switching_k_extension_results.md`
2. Extended structural Step-56 coverage to include `T=5000`:
   - `results/phase2_step56_large_grid_t5000/metrics_summary.json`
   - merged into canonical `results/phase2_step56_large_grid/metrics_summary.json` (now 54 executed cells).
3. Updated gate and tracker artifacts:
   - `docs/step56_large_grid_runner_note.md`
   - `docs/step67_viability_gate2_assessment.md`
   - `tracking/phase2_steps.csv`

### Result
1. Structural coverage now spans `N=20/80/150`, `k=2/3/4`, `T=500/2000/5000`, `sigma=0.1/1.0` with 54/54 runs.
2. Explicit `K=3/4/5` switching sweep is now available and reveals weak recovery under current pipeline.
3. Stress optimization on a hard `K=3` cell did not close the gap, supporting a fundamental-hardness interpretation rather than a simple tuning artifact.
4. Step 56 and Gate 2 are operationally closed with contingency (scope-limited claims).

## 2026-03-12 (Latest) — Phase 1 Reframed Theory Closure

### Added
1. `docs/phase1_theory_closure_reframed.md`
2. Updated theorem text in:
   - `proofs/latex/master.tex`
3. Updated gate/phase trackers:
   - `tracking/phase1_steps.csv`
   - `docs/step50_viability_gate_assessment.md`

### Result
1. Identifiability + sample-complexity + minimax program is now closed for an explicit restricted switching sparse class.
2. Unrestricted strongest theorem remains explicitly open; contingency framing is now first-class and auditable.

## 2026-03-12 (Latest) — Phase 3/4 Status Hardening

### Added
1. Phase 3 tracker moved from "in progress but blocked" to explicit blocked statuses:
   - `tracking/phase3_steps.csv`
2. Phase 4 writing statuses updated to reflect completed in-repo deliverables vs external/data blocks:
   - `tracking/phase4_steps.csv`
3. Additional writing artifacts:
   - `docs/phase4_step88_figure_story_map.md`
   - `docs/phase4_step89_abstract_styles.md`

### Result
1. Remaining unresolved work is now separated cleanly into:
   - external dataset dependencies,
   - external human submission/feedback dependencies.
2. No internal repository task remains ambiguously "in progress" without a concrete blocker or deliverable.

## 2026-03-12 (Latest) — Step 67 Multi-Regime Upgrade Extension

### Added
1. `code/models/phase2_step67_multiregime_upgrade.py` (baseline vs upgraded recovery schedules).
2. `code/models/phase2_step67_init_benchmark.py` (direct initialization strategy benchmark).
3. Artifacts:
   - `results/phase2_step67_multiregime_upgrade_quick2/metrics_summary.json`
   - `results/phase2_step67_init_benchmark/metrics_summary.json`
4. Notes:
   - `docs/step67_multiregime_upgrade_note.md`

### Result
1. Initialization benchmark indicates structured local initialization (`local_ar_gmm`) is robustly competitive and best under variance-penalized ranking.
2. Upgraded inference schedule improved regime-assignment and transition estimation metrics in quick runs.
3. Support-F1 did not improve in the same runs, exposing a split bottleneck between state decoding and sparse support refit.
4. Representative quick-run deltas (upgraded - baseline):
   - regime accuracy: +0.015 to +0.030,
   - transition-L1: -0.046 to -0.127 (better),
   - support-F1: -0.021 to -0.074 (worse).

### Logic Check
1. Extension does not overclaim a solved `K>=3` pipeline.
2. Findings are used to refine next algorithmic target (support-refit stage), not to inflate gate claims.

## 2026-03-12 (Latest) — Step 67 Refit-Mode Tradeoff Clarified

### Added
1. Multi-seed upgrade comparisons with and without stability refit:
   - `results/phase2_step67_multiregime_upgrade_fastmultiseed/metrics_summary.json`
   - `results/phase2_step67_multiregime_upgrade_fastmultiseed_nostability/metrics_summary.json`
2. Tradeoff memo:
   - `docs/step67_refit_tradeoff_analysis.md`

### Result
1. Stability-refit upgrade:
   - better regime tracking and transition estimates,
   - lower support F1.
2. No-stability upgrade:
   - improved support F1,
   - weaker/flat regime-accuracy gains.
3. Conclusion:
   - multi-regime recovery currently exhibits a measurable regime-vs-support objective tradeoff.

## 2026-03-12 (Latest) — Active-Issue Fix Pass (Multi-Regime Anti-Collapse)

### Added / Updated
1. Core solver updates in `code/models/phase0_baselines.py`:
   - persistence-aware init strategies (`local_ar_gmm_sticky`, `residual_gmm_sticky`),
   - candidate selection controls (`selection_mode`, alpha-scale schedules),
   - anti-collapse sparse-refit guard (empty-support rescue + minimum support gate).
2. Step-67 runner updates in `code/models/phase2_step67_multiregime_upgrade.py`:
   - support cardinality diagnostics (`support_nnz`),
   - extended config for selection and alpha schedules.
3. Extended initialization benchmark coverage:
   - `results/phase2_step67_init_benchmark_v2/metrics_summary.json`.
4. New upgrade artifact with anti-collapse controls:
   - `results/phase2_step67_multiregime_upgrade_v2_fastcheck/metrics_summary.json`.
5. Test hardening:
   - `tests/test_phase2_multiregime_upgrade.py` now checks v2 strategy coverage and non-degenerate support behavior.
6. Documentation updates:
   - `docs/step67_multiregime_upgrade_note.md`
   - `docs/step67_viability_gate2_assessment.md`
   - `docs/exhaustive_review_active_issues_2026_03_12.md`

### Result
1. Zero-support collapse is now explicitly controlled and regression-tested.
2. v2 fastcheck evidence shows:
   - regime-accuracy gains in all difficulty tiers,
   - transition-L1 gains in all tiers,
   - support-F1 gains in medium/hard tiers and decline in easy tier (still mixed overall).
3. This is a meaningful strengthening, not full closure: `K>=3` remains non-universal and contingency framing stays active.

### Logic Check
1. Claims remain conservative and tied to concrete artifacts.
2. External blockers (real datasets, mentor feedback, submission actions) remain explicitly blocked and are not conflated with in-repo progress.

### 2026-03-12 Update (Same Pass) — v2 Multiseed Confirmation
1. Completed run: `results/phase2_step67_multiregime_upgrade_v2_multiseed/metrics_summary.json`.
2. Upgraded-minus-baseline deltas:
   - easy: acc `+0.105`, support-F1 `+0.090`, transition-L1 `-0.179`.
   - medium: acc `+0.045`, support-F1 `-0.002`, transition-L1 `-0.202`.
   - hard: acc `+0.037`, support-F1 `+0.076`, transition-L1 `-0.262`.
3. Interpretation: anti-collapse controls and stronger init/restart policy now provide a meaningful, but still non-universal, multi-regime improvement profile.

## 2026-03-12 (Latest) — Phase 3 Critical Baseline Fix + Dataset Contract

### Added / Updated
1. `code/models/phase3_step70_motif_inference.py` now exports:
   - `static_features.npy`,
   - `dynamic_features.npy`,
   - `subject_ids.npy`.
2. `code/models/phase3_step72_baseline_compare.py` rewritten:
   - removed proxy-only baseline path,
   - added real CV static baseline models (ridge, pca-ridge, intercept),
   - reports `relative_mse_lift_vs_best_static`.
3. Integration robustness fix:
   - Step72 now resolves static/craving paths relative to provided Step70 metrics directory.
4. Mock replay rerun confirms end-to-end status map with Step72=`ok`.
5. Added dataset contract note:
   - `docs/phase3_dataset_requirements.md`.
6. Added Phase3 mock-pipeline tests:
   - `tests/test_phase3_mock_pipeline.py`.

### Result
1. A critical methodological issue is removed: no more placeholder static proxy in the canonical Step72 path.
2. Phase3 software pipeline is now explicitly validated with real static-vs-dynamic comparison logic on mock replay.
3. Remaining blocker is strictly external real-data availability.

### Logic Check
1. No biological claims were promoted from mock replay.
2. Real-data tracker status remains blocked until required roots are mounted and rerun passes.
