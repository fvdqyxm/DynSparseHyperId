import csv
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "tracking" / "phase0_steps.csv"
PHASE1_TRACKER = ROOT / "tracking" / "phase1_steps.csv"
PHASE2_TRACKER = ROOT / "tracking" / "phase2_steps.csv"
PHASE3_TRACKER = ROOT / "tracking" / "phase3_steps.csv"
PHASE4_TRACKER = ROOT / "tracking" / "phase4_steps.csv"
METRICS = ROOT / "results" / "phase0" / "metrics_summary.json"
SWEEP_METRICS = ROOT / "results" / "phase0_switching_sweep" / "sweep_metrics.json"
WILSON_METRICS = ROOT / "results" / "phase0_wilson_cowan" / "metrics_summary.json"
HYPER_K3_METRICS = ROOT / "results" / "phase0_hypergraph_k3" / "metrics_summary.json"
RIGOR_METRICS = ROOT / "results" / "rigor_checks" / "metrics_summary.json"
SCHEMA_AUDIT = ROOT / "results" / "rigor_checks" / "schema_logic_audit.json"
ASSUMPTION_AUDIT = ROOT / "results" / "rigor_checks" / "assumption_literature_audit.json"


class TestPhase0Tracker(unittest.TestCase):
    def test_tracker_exists_and_has_all_steps(self) -> None:
        self.assertTrue(TRACKER.exists(), f"Missing tracker file: {TRACKER}")
        with TRACKER.open(newline="") as f:
            rows = list(csv.DictReader(f))
        step_ids = {int(r["Step #"]) for r in rows}
        self.assertEqual(step_ids, set(range(1, 23)))

    def test_tracker_statuses_are_valid(self) -> None:
        valid = {"Pending", "In Progress", "Completed", "Blocked"}
        with TRACKER.open(newline="") as f:
            for row in csv.DictReader(f):
                self.assertIn(row["Status"], valid, f"Bad status in step {row['Step #']}")
                self.assertTrue(row["Description"].strip(), f"Missing description in step {row['Step #']}")

    def test_phase1_tracker_exists_and_valid(self) -> None:
        self.assertTrue(PHASE1_TRACKER.exists(), f"Missing tracker file: {PHASE1_TRACKER}")
        with PHASE1_TRACKER.open(newline="") as f:
            rows = list(csv.DictReader(f))
        step_ids = {int(r["Step #"]) for r in rows}
        self.assertEqual(step_ids, set(range(23, 51)))
        valid = {"Pending", "In Progress", "Completed", "Blocked"}
        for row in rows:
            self.assertIn(row["Status"], valid, f"Bad phase1 status in step {row['Step #']}")
            self.assertTrue(row["Description"].strip(), f"Missing phase1 description in step {row['Step #']}")

    def test_phase2_tracker_exists_and_valid(self) -> None:
        self.assertTrue(PHASE2_TRACKER.exists(), f"Missing tracker file: {PHASE2_TRACKER}")
        with PHASE2_TRACKER.open(newline="") as f:
            rows = list(csv.DictReader(f))
        step_ids = {int(r["Step #"]) for r in rows}
        self.assertEqual(step_ids, set(range(51, 68)))
        valid = {"Pending", "In Progress", "Completed", "Blocked"}
        for row in rows:
            self.assertIn(row["Status"], valid, f"Bad phase2 status in step {row['Step #']}")
            self.assertTrue(row["Description"].strip(), f"Missing phase2 description in step {row['Step #']}")

    def test_phase3_tracker_exists_and_valid(self) -> None:
        self.assertTrue(PHASE3_TRACKER.exists(), f"Missing tracker file: {PHASE3_TRACKER}")
        with PHASE3_TRACKER.open(newline="") as f:
            rows = list(csv.DictReader(f))
        step_ids = {int(r["Step #"]) for r in rows}
        self.assertEqual(step_ids, set(range(68, 77)))
        valid = {"Pending", "In Progress", "Completed", "Blocked"}
        for row in rows:
            self.assertIn(row["Status"], valid, f"Bad phase3 status in step {row['Step #']}")
            self.assertTrue(row["Description"].strip(), f"Missing phase3 description in step {row['Step #']}")

    def test_phase4_tracker_exists_and_valid(self) -> None:
        self.assertTrue(PHASE4_TRACKER.exists(), f"Missing tracker file: {PHASE4_TRACKER}")
        with PHASE4_TRACKER.open(newline="") as f:
            rows = list(csv.DictReader(f))
        step_ids = {int(r["Step #"]) for r in rows}
        self.assertEqual(step_ids, set(range(77, 141)))
        valid = {"Pending", "In Progress", "Completed", "Blocked"}
        for row in rows:
            self.assertIn(row["Status"], valid, f"Bad phase4 status in step {row['Step #']}")
            self.assertTrue(row["Description"].strip(), f"Missing phase4 description in step {row['Step #']}")

    def test_phase1_completed_steps_have_model_artifacts(self) -> None:
        with PHASE1_TRACKER.open(newline="") as f:
            rows = {int(r["Step #"]): r for r in csv.DictReader(f)}
        tex = (ROOT / "proofs" / "latex" / "master.tex").read_text()

        if rows[23]["Status"] == "Completed":
            self.assertIn("z_1", tex)
            self.assertIn("z_t \\mid z_{t-1}", tex)
            self.assertIn("f_r(y_{t-1};\\Theta_r)", tex)
        if rows[24]["Status"] == "Completed":
            self.assertIn("H_r", tex)
            self.assertIn("M_3 = \\binom{N}{2}", tex)
        if rows[25]["Status"] == "Completed":
            self.assertIn("\\mathcal{L}_{\\text{ELBO}}", tex)
            self.assertIn("\\mathcal{R}_{\\text{sparse}}", tex)
            self.assertIn("\\mathcal{R}_{\\text{smooth}}", tex)
        if rows[27]["Status"] == "Completed":
            self.assertIn("A1: Controlled Sparsity", tex)
            self.assertIn("A6: Beta-Min", tex)
        if rows[28]["Status"] == "Completed":
            mat = ROOT / "docs" / "phase1_literature_matrix_30_target.md"
            self.assertTrue(mat.exists())
            mtxt = mat.read_text()
            self.assertIn("## Reviewed (30)", mtxt)
            self.assertIn("| 30 | Tensor Bernstein concentration tool", mtxt)
            round3 = ROOT / "docs" / "phase1_literature_summaries_round3.md"
            self.assertTrue(round3.exists())
            self.assertIn("Round-3 Logic Check", round3.read_text())
        if rows[29]["Status"] == "Completed":
            self.assertTrue((ROOT / "docs" / "phase1_gap_table.md").exists())
        if rows[30]["Status"] == "Completed":
            abs_text = (ROOT / "docs" / "phase1_intro_abstract_draft.md").read_text()
            self.assertIn("Draft Abstract", abs_text)
            self.assertIn("latent regime", abs_text.lower())
        if rows[33]["Status"] in {"In Progress", "Completed"}:
            p33 = ROOT / "docs" / "k3_identifiability_extension_notes.md"
            self.assertTrue(p33.exists())
            t33 = p33.read_text()
            self.assertIn("Extending Identifiability from k=2 to k=3", t33)
            self.assertIn("Non-Aliasing", t33)
        if rows[34]["Status"] in {"In Progress", "Completed"}:
            p34 = ROOT / "docs" / "regime_separation_eigengap_argument.md"
            self.assertTrue(p34.exists())
            t34 = p34.read_text()
            self.assertIn("eigenvalue-gap", t34.lower())
            self.assertIn("spectral gap", t34.lower())
        if rows[36]["Status"] == "Completed":
            p36 = ROOT / "docs" / "hyperedge_irrepresentable_lemma.md"
            self.assertTrue(p36.exists())
            t36 = p36.read_text()
            self.assertIn("group-irrepresentable", t36.lower())
            self.assertIn("key lemma", t36.lower())
            self.assertIn("Hyperedge group-irrepresentable condition", tex)
        if rows[39]["Status"] == "Completed":
            p39 = ROOT / "docs" / "theorem2_sample_complexity_draft.md"
            self.assertTrue(p39.exists())
            t39 = p39.read_text()
            self.assertIn("Draft Theorem 2 Statement", t39)
            self.assertIn("sample complexity", t39.lower())
            self.assertIn("Sample Complexity Statement (Draft)", tex)
        if rows[40]["Status"] in {"In Progress", "Completed"}:
            p40 = ROOT / "docs" / "matrix_bernstein_hyperedge_notes.md"
            self.assertTrue(p40.exists())
            t40 = p40.read_text()
            self.assertIn("Bernstein", t40)
            self.assertIn("dependent", t40.lower())
            if rows[40]["Status"] == "Completed":
                p40b = ROOT / "docs" / "step40_weight_perturbation_lemma.md"
                self.assertTrue(p40b.exists())
                self.assertIn("Oracle-to-Inferred", p40b.read_text())
        if rows[41]["Status"] in {"In Progress", "Completed"}:
            p41 = ROOT / "docs" / "step41_t_bound_derivation.md"
            self.assertTrue(p41.exists())
            t41 = p41.read_text()
            self.assertIn("Combined Working Upper Bound", t41)
            self.assertIn("tau_{\\mathrm{mix}}", t41)
        if rows[42]["Status"] in {"In Progress", "Completed"}:
            p42 = ROOT / "docs" / "step42_fano_lower_bound_sketch.md"
            self.assertTrue(p42.exists())
            t42 = p42.read_text()
            self.assertIn("Fano", t42)
            self.assertIn("minimax", t42.lower())
        if rows[43]["Status"] == "Completed":
            p43 = ROOT / "results" / "phase1_step43_tightness" / "metrics_summary.json"
            self.assertTrue(p43.exists())
            report = json.loads(p43.read_text())
            self.assertIn("tightness_logic", report)
            self.assertIn("switching_slope", report["tightness_logic"])
            self.assertIn("k3_slope", report["tightness_logic"])
            self.assertTrue((ROOT / "docs" / "step43_tightness_results.md").exists())
        if rows[44]["Status"] == "Completed":
            p44 = ROOT / "results" / "phase1_step44_noise_robustness" / "metrics_summary.json"
            self.assertTrue(p44.exists())
            report = json.loads(p44.read_text())
            self.assertIn("summary_by_noise_model", report)
            for model in ["gaussian", "student_t", "contaminated"]:
                self.assertIn(model, report["summary_by_noise_model"])
            self.assertTrue((ROOT / "docs" / "step44_noise_robustness_results.md").exists())
        if rows[45]["Status"] == "Completed":
            p45 = ROOT / "results" / "phase1_step45_proxem" / "metrics_summary.json"
            self.assertTrue(p45.exists())
            report = json.loads(p45.read_text())
            self.assertIn("loglik_monotone_fraction", report)
            self.assertIn("final_regime_accuracy", report)
            self.assertTrue((ROOT / "docs" / "step45_variational_proxem_results.md").exists())
        if rows[46]["Status"] == "Completed":
            p46 = ROOT / "docs" / "step46_convergence_proof_note.md"
            self.assertTrue(p46.exists())
            t46 = p46.read_text()
            self.assertIn("O(1/m)", t46)
            self.assertIn("convex surrogate", t46.lower())
        if rows[47]["Status"] == "Completed":
            p47 = ROOT / "docs" / "step47_convergence_contingency.md"
            self.assertTrue(p47.exists())
            t47 = p47.read_text()
            self.assertIn("nonconvex", t47.lower())
            self.assertIn("Claim-Safe Wording", t47)
        if rows[48]["Status"] == "Completed":
            p48 = ROOT / "results" / "phase1_step48_grid" / "metrics_summary.json"
            self.assertTrue(p48.exists())
            report = json.loads(p48.read_text())
            self.assertIn("summary", report)
            self.assertTrue((ROOT / "results" / "phase1_step48_grid" / "k2_grid_f1.png").exists())
        if rows[49]["Status"] == "Completed":
            p49 = ROOT / "results" / "phase1_step49_curves" / "metrics_summary.json"
            self.assertTrue(p49.exists())
            report = json.loads(p49.read_text())
            self.assertIn("curve_summary", report)
            self.assertTrue((ROOT / "results" / "phase1_step49_curves" / "f1_vs_t_over_n.png").exists())
        if rows[50]["Status"] in {"In Progress", "Completed"}:
            p50 = ROOT / "docs" / "step50_viability_gate_assessment.md"
            self.assertTrue(p50.exists())
            self.assertIn("Viability Gate 1 Assessment", p50.read_text())

        with PHASE2_TRACKER.open(newline="") as f:
            rows2 = {int(r["Step #"]): r for r in csv.DictReader(f)}
        if rows2[51]["Status"] == "Completed":
            p51 = ROOT / "results" / "phase2_step51_backbone" / "metrics_summary.json"
            self.assertTrue(p51.exists())
            self.assertIn("probability_simplex_max_deviation", json.loads(p51.read_text()))
        if rows2[52]["Status"] == "Completed":
            p52 = ROOT / "results" / "phase2_step52_hypergraph_emission" / "metrics_summary.json"
            self.assertTrue(p52.exists())
            self.assertIn("output_shape", json.loads(p52.read_text()))
        if rows2[53]["Status"] == "Completed":
            p53 = ROOT / "results" / "phase2_step53_proximal" / "metrics_summary.json"
            self.assertTrue(p53.exists())
            self.assertIn("objective_monotone_fraction", json.loads(p53.read_text()))
        if rows2[54]["Status"] == "Completed":
            p54 = ROOT / "results" / "phase2_step54_temporal_kl" / "metrics_summary.json"
            self.assertTrue(p54.exists())
            rep54 = json.loads(p54.read_text())
            self.assertIn("penalty_random", rep54)
            self.assertIn("penalty_identical", rep54)
        if rows2[55]["Status"] == "Completed":
            p55 = ROOT / "results" / "phase2_step55_curriculum" / "metrics_summary.json"
            self.assertTrue(p55.exists())
            rep55 = json.loads(p55.read_text())
            self.assertIn("curriculum_gain", rep55)
            self.assertTrue((ROOT / "docs" / "step55_curriculum_results.md").exists())
        if rows2[56]["Status"] in {"In Progress", "Completed"}:
            p56 = ROOT / "results" / "phase2_step56_large_grid" / "metrics_summary.json"
            self.assertTrue(p56.exists())
            rep56 = json.loads(p56.read_text())
            self.assertIn("requested_total", rep56)
            self.assertIn("executed", rep56)
            self.assertTrue((ROOT / "docs" / "step56_large_grid_runner_note.md").exists())
        if rows2[57]["Status"] in {"In Progress", "Completed"}:
            p57 = ROOT / "results" / "phase2_step57_multiseed_50" / "metrics_summary.json"
            if not p57.exists():
                p57 = ROOT / "results" / "phase2_step57_multiseed_consistent" / "metrics_summary.json"
            self.assertTrue(p57.exists())
            rep57 = json.loads(p57.read_text())
            self.assertIn("runs", rep57)
            self.assertTrue((ROOT / "docs" / "step57_multiseed_results.md").exists())
        if rows2[58]["Status"] == "Completed":
            p58 = ROOT / "results" / "phase2_step58_metrics_50" / "metrics_summary.json"
            if not p58.exists():
                p58 = ROOT / "results" / "phase2_step58_metrics_consistent" / "metrics_summary.json"
            self.assertTrue(p58.exists())
            rep58 = json.loads(p58.read_text())
            self.assertIn("structural", rep58)
            self.assertIn("switching", rep58)
            self.assertTrue((ROOT / "docs" / "step58_metrics_results.md").exists())
        if rows2[59]["Status"] == "Completed":
            p59 = ROOT / "results" / "phase2_step59_scaling_50" / "metrics_summary.json"
            if not p59.exists():
                p59 = ROOT / "results" / "phase2_step59_scaling_consistent" / "metrics_summary.json"
            self.assertTrue(p59.exists())
            rep59 = json.loads(p59.read_text())
            self.assertIn("structural_slopes_loglog", rep59)
            self.assertIn("switching_slopes_loglog", rep59)
            fig59 = ROOT / "results" / "phase2_step59_scaling_50" / "structural_scaling_loglog.png"
            if not fig59.exists():
                fig59 = ROOT / "results" / "phase2_step59_scaling_consistent" / "structural_scaling_loglog.png"
            self.assertTrue(fig59.exists())
            self.assertTrue((ROOT / "docs" / "step59_scaling_results.md").exists())
        if rows2[60]["Status"] == "Completed":
            p60 = ROOT / "results" / "phase2_step60_62_ablations" / "metrics_summary.json"
            self.assertTrue(p60.exists())
            rep60 = json.loads(p60.read_text())
            self.assertIn("step60_sparsity_ablation", rep60)
            self.assertTrue((ROOT / "docs" / "step60_62_ablation_results.md").exists())
        if rows2[61]["Status"] == "Completed":
            p61 = ROOT / "results" / "phase2_step60_62_ablations" / "metrics_summary.json"
            self.assertTrue(p61.exists())
            rep61 = json.loads(p61.read_text())
            self.assertIn("step61_regime_ablation", rep61)
        if rows2[62]["Status"] == "Completed":
            p62 = ROOT / "results" / "phase2_step60_62_ablations" / "metrics_summary.json"
            self.assertTrue(p62.exists())
            rep62 = json.loads(p62.read_text())
            self.assertIn("step62_highorder_ablation", rep62)
        if rows2[63]["Status"] == "Completed":
            p63 = ROOT / "results" / "phase2_step63_baselines" / "metrics_summary.json"
            self.assertTrue(p63.exists())
            rep63 = json.loads(p63.read_text())
            self.assertIn("pairwise_sparse_lds", rep63)
            self.assertIn("highorder_baseline_comparison", rep63)
            self.assertTrue((ROOT / "docs" / "step63_baseline_comparison_results.md").exists())
        if rows2[64]["Status"] == "Completed":
            p64 = ROOT / "results" / "phase2_step64_robustness" / "metrics_summary.json"
            self.assertTrue(p64.exists())
            rep64 = json.loads(p64.read_text())
            self.assertIn("outlier", rep64)
            self.assertIn("missing_data", rep64)
            self.assertTrue((ROOT / "docs" / "step64_robustness_results.md").exists())
        if rows2[65]["Status"] == "Completed":
            p65 = ROOT / "results" / "phase2_step65_tuning" / "metrics_summary.json"
            self.assertTrue(p65.exists())
            rep65 = json.loads(p65.read_text())
            self.assertIn("recommended", rep65)
            self.assertTrue((ROOT / "docs" / "step65_tuning_results.md").exists())
        if rows2[66]["Status"] == "Completed":
            p66 = ROOT / "docs" / "step66_failure_modes.md"
            self.assertTrue(p66.exists())
            t66 = p66.read_text()
            self.assertIn("Failure Mode 1", t66)
            self.assertIn("White-Paper Usage", t66)
        if rows2[67]["Status"] in {"In Progress", "Completed"}:
            p67 = ROOT / "docs" / "step67_viability_gate2_assessment.md"
            self.assertTrue(p67.exists())
            t67 = p67.read_text()
            self.assertIn("Viability Gate 2 Assessment", t67)

        with PHASE3_TRACKER.open(newline="") as f:
            rows3 = {int(r["Step #"]): r for r in csv.DictReader(f)}
        if rows3[68]["Status"] in {"In Progress", "Completed"}:
            p68 = ROOT / "code" / "models" / "phase3_step68_data_intake.py"
            self.assertTrue(p68.exists())
            r68 = ROOT / "results" / "phase3_step68_intake" / "metrics_summary.json"
            self.assertTrue(r68.exists())
            rep68 = json.loads(r68.read_text())
            self.assertIn("status", rep68)
            self.assertTrue((ROOT / "docs" / "step68_intake_results.md").exists())
        if rows3[69]["Status"] in {"In Progress", "Completed"}:
            p69 = ROOT / "code" / "models" / "phase3_step69_sliding_windows.py"
            self.assertTrue(p69.exists())
            r69 = ROOT / "results" / "phase3_step69_windows" / "metrics_summary.json"
            self.assertTrue(r69.exists())
            self.assertIn("status", json.loads(r69.read_text()))
        if rows3[70]["Status"] in {"In Progress", "Completed"}:
            p70 = ROOT / "code" / "models" / "phase3_step70_motif_inference.py"
            self.assertTrue(p70.exists())
            r70 = ROOT / "results" / "phase3_step70_motifs" / "metrics_summary.json"
            self.assertTrue(r70.exists())
            self.assertIn("status", json.loads(r70.read_text()))
        if rows3[71]["Status"] in {"In Progress", "Completed"}:
            p71 = ROOT / "code" / "models" / "phase3_step71_predict_craving.py"
            self.assertTrue(p71.exists())
            r71 = ROOT / "results" / "phase3_step71_prediction" / "metrics_summary.json"
            self.assertTrue(r71.exists())
            self.assertIn("status", json.loads(r71.read_text()))
        if rows3[72]["Status"] in {"In Progress", "Completed"}:
            p72 = ROOT / "code" / "models" / "phase3_step72_baseline_compare.py"
            self.assertTrue(p72.exists())
            r72 = ROOT / "results" / "phase3_step72_baseline_compare" / "metrics_summary.json"
            self.assertTrue(r72.exists())
            self.assertIn("status", json.loads(r72.read_text()))
        if rows3[73]["Status"] in {"In Progress", "Completed"}:
            p73 = ROOT / "code" / "models" / "phase3_step73_visualize_motifs.py"
            self.assertTrue(p73.exists())
            r73 = ROOT / "results" / "phase3_step73_visuals" / "metrics_summary.json"
            self.assertTrue(r73.exists())
            self.assertIn("status", json.loads(r73.read_text()))
        if rows3[74]["Status"] in {"In Progress", "Completed"}:
            p74 = ROOT / "code" / "models" / "phase3_step74_cross_dataset_preflight.py"
            self.assertTrue(p74.exists())
            r74 = ROOT / "results" / "phase3_step74_cross_dataset" / "metrics_summary.json"
            self.assertTrue(r74.exists())
            self.assertIn("status", json.loads(r74.read_text()))
        if rows3[75]["Status"] in {"In Progress", "Completed"}:
            p75 = ROOT / "code" / "models" / "phase3_step75_neuro_ablation.py"
            self.assertTrue(p75.exists())
            r75 = ROOT / "results" / "phase3_step75_ablation" / "metrics_summary.json"
            self.assertTrue(r75.exists())
            self.assertIn("status", json.loads(r75.read_text()))
        if rows3[76]["Status"] in {"In Progress", "Completed"}:
            p76 = ROOT / "code" / "models" / "phase3_step76_gate3_assessment.py"
            self.assertTrue(p76.exists())
            r76 = ROOT / "results" / "phase3_step76_gate3" / "metrics_summary.json"
            self.assertTrue(r76.exists())
            rep76 = json.loads(r76.read_text())
            self.assertIn("status", rep76)
            self.assertTrue((ROOT / "docs" / "phase3_steps69_76_results.md").exists())

        with PHASE4_TRACKER.open(newline="") as f:
            rows4 = {int(r["Step #"]): r for r in csv.DictReader(f)}
        if rows4[77]["Status"] == "Completed":
            self.assertTrue((ROOT / "docs" / "phase4_steps77_90_intro_related.md").exists())
        if rows4[91]["Status"] in {"Completed", "In Progress"}:
            self.assertTrue((ROOT / "docs" / "phase4_steps91_105_theory_writeup.md").exists())
        if rows4[106]["Status"] == "Completed":
            self.assertTrue((ROOT / "docs" / "phase4_steps106_120_algorithm_synth_writeup.md").exists())
        if rows4[121]["Status"] in {"Completed", "In Progress"}:
            self.assertTrue((ROOT / "docs" / "phase4_steps121_130_neuro_writeup.md").exists())
        if rows4[131]["Status"] == "Completed":
            self.assertTrue((ROOT / "docs" / "phase4_step131_polish_checklist.md").exists())
        if rows4[135]["Status"] == "Completed":
            self.assertTrue((ROOT / "docs" / "phase4_step135_backup_submissions.md").exists())
        if rows4[136]["Status"] == "Completed":
            self.assertTrue((ROOT / "docs" / "phase4_step136_open_source_release.md").exists())
            self.assertTrue((ROOT / "LICENSE").exists())
            self.assertTrue((ROOT / "CONTRIBUTING.md").exists())
            self.assertTrue((ROOT / "CITATION.cff").exists())
        if rows4[137]["Status"] == "Completed":
            self.assertTrue((ROOT / "docs" / "phase4_step137_blog_poster_draft.md").exists())
        if rows4[138]["Status"] == "Completed":
            self.assertTrue((ROOT / "docs" / "phase4_steps138_140_long_tail_plan.md").exists())


class TestPhase0Artifacts(unittest.TestCase):
    def test_readme_is_not_placeholder(self) -> None:
        text = (ROOT / "README.md").read_text()
        self.assertNotIn("[Insert the full Core Idea Description here", text)
        self.assertIn("Core Idea Summary", text)

    def test_required_directories_exist(self) -> None:
        required = [
            ROOT / "code" / "models",
            ROOT / "notebooks" / "experiments",
            ROOT / "proofs" / "latex",
            ROOT / "data" / "synth",
            ROOT / "data" / "real",
            ROOT / "literature" / "summaries",
            ROOT / "tracking",
            ROOT / "docs",
            ROOT / "tests",
        ]
        for path in required:
            self.assertTrue(path.exists(), f"Missing required path: {path}")

    def test_master_tex_scaffold_exists(self) -> None:
        tex = (ROOT / "proofs" / "latex" / "master.tex").read_text()
        self.assertIn("\\section{Model Formulation}", tex)
        self.assertIn("\\section{Identifiability Framework}", tex)
        self.assertIn("\\section{Finite-Sample Recovery}", tex)

    def test_master_pdf_interim_exists(self) -> None:
        pdf = ROOT / "proofs" / "latex" / "master.pdf"
        self.assertTrue(pdf.exists(), "Missing compiled interim PDF proofs/latex/master.pdf")
        self.assertGreater(pdf.stat().st_size, 10_000, "Compiled PDF appears unexpectedly small")

    def test_literature_summaries_exist(self) -> None:
        summaries = [
            ROOT / "literature" / "summaries" / "friedman_graphical_lasso_2008_summary.md",
            ROOT / "literature" / "summaries" / "chandrasekaran_latent_graphical_2012_summary.md",
            ROOT / "literature" / "summaries" / "turnbull_latent_hypergraph_summary.md",
        ]
        for summary in summaries:
            self.assertTrue(summary.exists(), f"Missing summary: {summary}")
            txt = summary.read_text()
            self.assertIn("Logic Checks", txt)
            self.assertIn("Action Items", txt)

    def test_wandb_script_is_python_file(self) -> None:
        script = ROOT / "notebooks" / "experiments" / "test_wandb_logging.py"
        self.assertTrue(script.exists(), "W&B script missing after notebook integrity fix")
        self.assertIn("wandb.init", script.read_text())

    def test_assumption_literature_matrix_exists_and_complete(self) -> None:
        matrix = ROOT / "docs" / "assumption_literature_matrix.csv"
        self.assertTrue(matrix.exists(), f"Missing assumption matrix: {matrix}")
        with matrix.open(newline="") as f:
            rows = list(csv.DictReader(f))
        ids = {r["Assumption ID"] for r in rows}
        self.assertEqual(ids, {"A1", "A2", "A3", "A4", "A5", "A6"})
        for row in rows:
            self.assertTrue(row["Primary Source 1"].startswith("http"))
            self.assertTrue(row["Primary Source 2"].startswith("http"))
            self.assertIn("open", row["Status"].lower())

    def test_python_env_version_and_core_imports(self) -> None:
        code = (
            "import sys, importlib.util\n"
            "assert sys.version_info >= (3, 11)\n"
            "mods=['torch','torch_geometric','pyro','numpy','scipy','matplotlib',"
            "'seaborn','sympy','tqdm','wandb','sklearn']\n"
            "missing=[m for m in mods if importlib.util.find_spec(m) is None]\n"
            "assert not missing, missing\n"
            "print('ok')\n"
        )
        out = subprocess.run(
            [str(ROOT / "venv" / "bin" / "python"), "-c", code],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("ok", out.stdout)


class TestBaselineEvidence(unittest.TestCase):
    def test_phase0_baseline_script_exists(self) -> None:
        script = ROOT / "code" / "models" / "phase0_baselines.py"
        self.assertTrue(script.exists(), f"Missing baseline script: {script}")

    def test_metrics_file_exists(self) -> None:
        self.assertTrue(
            METRICS.exists(),
            "Missing results/phase0/metrics_summary.json. Run code/models/phase0_baselines.py first.",
        )

    def test_metrics_schema_and_gate_thresholds(self) -> None:
        self.assertTrue(METRICS.exists(), f"Missing metrics file: {METRICS}")
        report = json.loads(METRICS.read_text())

        self.assertIn("graphical_lasso", report)
        self.assertIn("sparse_lds", report)
        self.assertIn("switching_lds", report)

        g = report["graphical_lasso"]["support_metrics"]["f1"]
        l = report["sparse_lds"]["support_metrics"]["f1"]
        self.assertGreaterEqual(g, 0.75, f"Graphical Lasso F1 below gate threshold: {g}")
        self.assertGreaterEqual(l, 0.75, f"Sparse LDS F1 below gate threshold: {l}")

        with TRACKER.open(newline="") as f:
            rows = {int(r["Step #"]): r for r in csv.DictReader(f)}
        step15_status = rows[15]["Status"]
        switching = report["switching_lds"]
        self.assertIn("regime_accuracy", switching)
        self.assertIn("support_f1_mean", switching)

        # Prevent overclaiming: only enforce hard switching thresholds if step 15 is marked complete.
        if step15_status == "Completed":
            self.assertGreaterEqual(
                switching["regime_accuracy"],
                0.75,
                f"Step 15 marked completed but regime accuracy is weak: {switching['regime_accuracy']}",
            )
            self.assertGreaterEqual(
                switching["support_f1_mean"],
                0.75,
                f"Step 15 marked completed but support F1 is weak: {switching['support_f1_mean']}",
            )
        else:
            self.assertIn(step15_status, {"Pending", "In Progress", "Blocked"})

    def test_completed_tracker_steps_have_artifact_evidence(self) -> None:
        with TRACKER.open(newline="") as f:
            rows = {int(r["Step #"]): r for r in csv.DictReader(f)}

        # For every completed step, enforce at least one concrete artifact check.
        self.assertEqual(rows[1]["Status"], "Completed")
        self.assertTrue((ROOT / ".git").exists())

        self.assertEqual(rows[2]["Status"], "Completed")
        self.assertNotIn("[Insert the full Core Idea Description here", (ROOT / "README.md").read_text())

        self.assertEqual(rows[6]["Status"], "Completed")
        self.assertTrue((ROOT / "proofs" / "latex" / "master.tex").exists())

        self.assertEqual(rows[7]["Status"], "Completed")
        self.assertTrue((ROOT / "notebooks" / "experiments" / "test_wandb_logging.py").exists())

        self.assertEqual(rows[11]["Status"], "Completed")
        self.assertTrue((ROOT / "code" / "models" / "phase0_baselines.py").exists())

        self.assertEqual(rows[12]["Status"], "Completed")
        self.assertTrue((ROOT / "results" / "phase0" / "graphical_lasso" / "precision_recovery.png").exists())

        self.assertEqual(rows[13]["Status"], "Completed")
        self.assertTrue((ROOT / "results" / "phase0" / "sparse_lds" / "A_true.npy").exists())

        self.assertEqual(rows[14]["Status"], "Completed")
        self.assertTrue((ROOT / "results" / "phase0" / "sparse_lds" / "A_recovery.png").exists())

        # Step 15 artifacts must exist if implementation work has started.
        if rows[15]["Status"] in {"In Progress", "Completed"}:
            self.assertTrue((ROOT / "results" / "phase0" / "switching_lds" / "A_regime_recovery.png").exists())
            self.assertTrue((ROOT / "results" / "phase0" / "switching_lds" / "regime_sequence_recovery.png").exists())

        # Steps 16-19 artifacts, guarded by status to avoid overclaiming.
        if rows[16]["Status"] in {"In Progress", "Completed"}:
            self.assertTrue((ROOT / "results" / "phase0_wilson_cowan" / "E_timeseries.npy").exists())
            self.assertTrue((ROOT / "results" / "phase0_wilson_cowan" / "I_timeseries.npy").exists())

        if rows[17]["Status"] in {"In Progress", "Completed"}:
            self.assertTrue((ROOT / "results" / "phase0_wilson_cowan" / "bold_clean.npy").exists())
            self.assertTrue((ROOT / "results" / "phase0_wilson_cowan" / "bold_noisy.npy").exists())

        if rows[18]["Status"] in {"In Progress", "Completed"}:
            self.assertTrue((ROOT / "results" / "phase0_wilson_cowan" / "z_regimes.npy").exists())

        if rows[19]["Status"] in {"In Progress", "Completed"}:
            self.assertTrue(WILSON_METRICS.exists())

        if rows[20]["Status"] in {"In Progress", "Completed"}:
            self.assertTrue((ROOT / "results" / "phase0_hypergraph_k3" / "H_true.npy").exists())
            self.assertTrue((ROOT / "results" / "phase0_hypergraph_k3" / "H_hat.npy").exists())
            self.assertTrue(HYPER_K3_METRICS.exists())

        self.assertEqual(rows[21]["Status"], "Completed")
        report = json.loads(METRICS.read_text())
        self.assertGreaterEqual(report["sparse_lds"]["support_metrics"]["f1"], 0.75)

    def test_switching_sweep_gate_when_step15_completed(self) -> None:
        with TRACKER.open(newline="") as f:
            rows = {int(r["Step #"]): r for r in csv.DictReader(f)}
        if rows[15]["Status"] != "Completed":
            return

        self.assertTrue(
            SWEEP_METRICS.exists(),
            "Step 15 marked completed but switching sweep metrics are missing.",
        )
        sweep = json.loads(SWEEP_METRICS.read_text())
        summary = sweep.get("summary_by_obs_noise", {})
        # Moderate-noise checkpoint at obs noise 0.15.
        self.assertIn("0.15", summary, "Expected moderate-noise bucket 0.15 in sweep summary.")
        self.assertGreaterEqual(
            summary["0.15"]["regime_accuracy_mean"],
            0.75,
            f"Moderate-noise regime accuracy too low: {summary['0.15']['regime_accuracy_mean']}",
        )
        self.assertGreaterEqual(
            summary["0.15"]["support_f1_mean_mean"],
            0.75,
            f"Moderate-noise support F1 too low: {summary['0.15']['support_f1_mean_mean']}",
        )

    def test_wilson_pipeline_logic_gate_when_step19_completed(self) -> None:
        with TRACKER.open(newline="") as f:
            rows = {int(r["Step #"]): r for r in csv.DictReader(f)}
        if rows[19]["Status"] != "Completed":
            return

        self.assertTrue(
            WILSON_METRICS.exists(),
            "Step 19 marked completed but Wilson-Cowan metrics are missing.",
        )
        report = json.loads(WILSON_METRICS.read_text())

        self.assertIn("recovery_vs_structural_coupling", report)
        self.assertIn("recovery_vs_effective_linearization", report)
        self.assertIn("dynamics_diagnostics", report)
        self.assertIn("claim_guardrail", report)

        self.assertGreaterEqual(
            report["regime_support_hamming"],
            0.15,
            f"Regime couplings are not sufficiently distinct: {report['regime_support_hamming']}",
        )

        diag = report["dynamics_diagnostics"]
        self.assertIn("low_observability_flag", diag)
        # Guardrail check: if observability is low, we must not report strong structural recovery.
        if diag["low_observability_flag"]:
            bold_f1 = report["recovery_vs_structural_coupling"]["bold_pairwise"]["support_f1_mean"]
            self.assertLessEqual(
                bold_f1,
                0.30,
                f"Low observability flagged but bold structural F1 is unexpectedly high: {bold_f1}",
            )
            self.assertIn("stress test", report["claim_guardrail"])

    def test_static_hypergraph_k3_gate_when_step20_completed(self) -> None:
        with TRACKER.open(newline="") as f:
            rows = {int(r["Step #"]): r for r in csv.DictReader(f)}
        if rows[20]["Status"] != "Completed":
            return

        self.assertTrue(
            HYPER_K3_METRICS.exists(),
            "Step 20 marked completed but static hypergraph metrics are missing.",
        )
        report = json.loads(HYPER_K3_METRICS.read_text())
        self.assertIn("single_run_support", report)
        self.assertIn("noise_sweep", report)

        single = report["single_run_support"]["f1"]
        self.assertGreaterEqual(single, 0.80, f"Step 20 completed but single-run F1 too low: {single}")
        # Non-triviality guard to catch accidental leakage/easy-mode degeneration.
        self.assertLess(single, 0.98, f"Single-run F1 suspiciously perfect; audit setup: {single}")

        sweep = report["noise_sweep"]
        self.assertIn("0.15", sweep)
        self.assertIn("0.50", sweep)
        self.assertGreaterEqual(
            sweep["0.15"]["f1_mean"],
            0.80,
            f"Low-noise sweep F1 unexpectedly weak: {sweep['0.15']['f1_mean']}",
        )
        self.assertLessEqual(
            sweep["0.50"]["f1_mean"],
            sweep["0.15"]["f1_mean"] + 1e-6,
            "High-noise F1 should not exceed low-noise F1 in this benchmark.",
        )

    def test_adversarial_rigor_controls(self) -> None:
        self.assertTrue(
            RIGOR_METRICS.exists(),
            "Missing adversarial rigor metrics. Run code/models/rigor_adversarial_checks.py.",
        )
        report = json.loads(RIGOR_METRICS.read_text())
        self.assertIn("guardrails", report)
        self.assertIn("all_passed", report)
        self.assertTrue(report["all_passed"], f"Adversarial guardrails failed: {report['guardrails']}")

    def test_schema_logic_audit_controls(self) -> None:
        self.assertTrue(
            SCHEMA_AUDIT.exists(),
            "Missing schema/logic audit metrics. Run code/models/schema_logic_audit.py.",
        )
        report = json.loads(SCHEMA_AUDIT.read_text())
        self.assertIn("checks", report)
        self.assertIn("all_passed", report)
        self.assertTrue(report["all_passed"], f"Schema/logic audit failed: {report['checks']}")

    def test_assumption_literature_audit_controls(self) -> None:
        self.assertTrue(
            ASSUMPTION_AUDIT.exists(),
            "Missing assumption-literature audit metrics. Run code/models/assumption_literature_audit.py.",
        )
        report = json.loads(ASSUMPTION_AUDIT.read_text())
        self.assertIn("checks", report)
        self.assertIn("all_passed", report)
        self.assertTrue(report["all_passed"], f"Assumption-literature audit failed: {report['checks']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
