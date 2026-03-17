import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestPhase3MockPipeline(unittest.TestCase):
    def test_phase3_scripts_exist(self) -> None:
        paths = [
            ROOT / "code" / "models" / "phase3_step68_data_intake.py",
            ROOT / "code" / "models" / "phase3_step69_sliding_windows.py",
            ROOT / "code" / "models" / "phase3_step70_motif_inference.py",
            ROOT / "code" / "models" / "phase3_step71_predict_craving.py",
            ROOT / "code" / "models" / "phase3_step72_baseline_compare.py",
            ROOT / "code" / "models" / "phase3_step73_visualize_motifs.py",
            ROOT / "code" / "models" / "phase3_step74_cross_dataset_preflight.py",
            ROOT / "code" / "models" / "phase3_step75_neuro_ablation.py",
            ROOT / "code" / "models" / "phase3_step76_gate3_assessment.py",
            ROOT / "code" / "models" / "phase3_mock_dataset_replay.py",
        ]
        for p in paths:
            self.assertTrue(p.exists(), f"Missing Phase3 script: {p}")

    def test_mock_replay_status_map(self) -> None:
        path = ROOT / "results" / "phase3_mock_replay" / "metrics_summary.json"
        self.assertTrue(path.exists(), f"Missing mock replay summary: {path}")
        rep = json.loads(path.read_text())
        sm = rep.get("status_map", {})
        expected = {
            "step68": "ready_for_step69",
            "step69": "ready_for_step70",
            "step70": "ok",
            "step71": "ok",
            "step72": "ok",
            "step73": "ok",
            "step74": "ready",
            "step75": "ok",
            "step76": "provisional_pass",
        }
        self.assertEqual(sm, expected)

    def test_step70_feature_artifacts_exist(self) -> None:
        root = ROOT / "results" / "phase3_mock_replay" / "step70"
        for name in [
            "motif_basis.npy",
            "motif_scores.npy",
            "subject_craving.npy",
            "subject_ids.npy",
            "dynamic_features.npy",
            "static_features.npy",
            "metrics_summary.json",
        ]:
            self.assertTrue((root / name).exists(), f"Missing Step70 artifact: {root / name}")

    def test_step72_is_real_static_comparison(self) -> None:
        path = ROOT / "results" / "phase3_mock_replay" / "step72" / "metrics_summary.json"
        self.assertTrue(path.exists(), f"Missing Step72 summary: {path}")
        rep = json.loads(path.read_text())
        self.assertEqual(rep.get("status"), "ok")
        self.assertIn("dynamic_model", rep)
        self.assertIn("static_baselines", rep)
        self.assertIn("best_static_baseline", rep)
        self.assertIn("relative_mse_lift_vs_best_static", rep)
        self.assertTrue(len(rep["static_baselines"]) >= 2)
        self.assertNotEqual(rep.get("status"), "ok_proxy")

    def test_step76_gate_uses_ready_upstream(self) -> None:
        path = ROOT / "results" / "phase3_mock_replay" / "step76" / "metrics_summary.json"
        self.assertTrue(path.exists(), f"Missing Step76 summary: {path}")
        rep = json.loads(path.read_text())
        self.assertEqual(rep.get("status"), "provisional_pass")
        upstream = rep.get("upstream_statuses", {})
        self.assertEqual(upstream.get("step72"), "ok")


if __name__ == "__main__":
    unittest.main()
