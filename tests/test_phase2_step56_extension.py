import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestStep56Extension(unittest.TestCase):
    def test_structural_step56_has_t5000_coverage(self) -> None:
        metrics = ROOT / "results" / "phase2_step56_large_grid" / "metrics_summary.json"
        self.assertTrue(metrics.exists(), f"Missing metrics: {metrics}")
        rep = json.loads(metrics.read_text())
        self.assertGreaterEqual(int(rep.get("requested_total", 0)), 54)
        self.assertEqual(int(rep.get("executed", -1)), int(rep.get("requested_total", -2)))
        self.assertEqual(int(rep.get("skipped", -1)), 0)

        runs = rep.get("runs", [])
        self.assertTrue(runs, "No runs found in step56 structural artifact.")
        t_values = {int(r["t"]) for r in runs}
        self.assertIn(5000, t_values)

    def test_switching_k_supplement_exists_and_has_k_sweep(self) -> None:
        metrics = ROOT / "results" / "phase2_step56_switching_k_grid_full" / "metrics_summary.json"
        self.assertTrue(metrics.exists(), f"Missing switching-k supplement metrics: {metrics}")
        rep = json.loads(metrics.read_text())
        self.assertEqual(int(rep.get("requested_total", -1)), 18)
        self.assertEqual(int(rep.get("executed", -1)), 18)
        self.assertEqual(int(rep.get("failed", -1)), 0)

        cfg = rep.get("config", {})
        self.assertEqual(set(cfg.get("k_values", [])), {3, 4, 5})
        self.assertIn(5000, set(cfg.get("t_values", [])))
        self.assertIn(1.0, set(cfg.get("obs_noise_values", [])))

    def test_switching_stress_artifact_exists(self) -> None:
        metrics = ROOT / "results" / "phase2_step56_switching_k_grid_stress_k3" / "metrics_summary.json"
        self.assertTrue(metrics.exists(), f"Missing stress artifact: {metrics}")
        rep = json.loads(metrics.read_text())
        self.assertEqual(int(rep.get("requested_total", -1)), 1)
        self.assertEqual(int(rep.get("executed", -1)), 1)
        runs = rep.get("runs", [])
        self.assertEqual(len(runs), 1)
        self.assertIn("regime_accuracy", runs[0])
        self.assertIn("support_f1_mean", runs[0])


if __name__ == "__main__":
    unittest.main()
