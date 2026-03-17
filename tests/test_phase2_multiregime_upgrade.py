import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestPhase2MultiregimeUpgrade(unittest.TestCase):
    def test_upgrade_scripts_exist(self) -> None:
        self.assertTrue((ROOT / "code" / "models" / "phase2_step67_multiregime_upgrade.py").exists())
        self.assertTrue((ROOT / "code" / "models" / "phase2_step67_init_benchmark.py").exists())

    def test_init_benchmark_artifact_schema(self) -> None:
        path = ROOT / "results" / "phase2_step67_init_benchmark" / "metrics_summary.json"
        self.assertTrue(path.exists(), f"Missing init benchmark artifact: {path}")
        rep = json.loads(path.read_text())
        self.assertIn("summary", rep)
        self.assertIn("best_strategy_by_mean_accuracy", rep)
        self.assertIn("best_strategy_by_robust_score", rep)
        self.assertIn("local_ar_gmm", rep["summary"])
        self.assertIn("random_blocks", rep["summary"])

    def test_upgrade_quick_artifact_schema(self) -> None:
        path = ROOT / "results" / "phase2_step67_multiregime_upgrade_quick2" / "metrics_summary.json"
        self.assertTrue(path.exists(), f"Missing upgrade quick artifact: {path}")
        rep = json.loads(path.read_text())
        self.assertIn("summary", rep)
        for key in ["easy_delta", "medium_delta", "hard_delta"]:
            self.assertIn(key, rep["summary"])
            self.assertIn("regime_accuracy_delta", rep["summary"][key])
            self.assertIn("support_f1_delta", rep["summary"][key])

    def test_upgrade_multiseed_tradeoff_artifacts(self) -> None:
        p_stab = ROOT / "results" / "phase2_step67_multiregime_upgrade_fastmultiseed" / "metrics_summary.json"
        p_nostab = ROOT / "results" / "phase2_step67_multiregime_upgrade_fastmultiseed_nostability" / "metrics_summary.json"
        self.assertTrue(p_stab.exists(), f"Missing stability multiseed artifact: {p_stab}")
        self.assertTrue(p_nostab.exists(), f"Missing no-stability multiseed artifact: {p_nostab}")

        r_stab = json.loads(p_stab.read_text())
        r_nostab = json.loads(p_nostab.read_text())
        for rep in [r_stab, r_nostab]:
            for key in ["easy_delta", "medium_delta", "hard_delta"]:
                self.assertIn(key, rep["summary"])
                self.assertIn("transition_l1_delta", rep["summary"][key])

    def test_v2_init_benchmark_has_sticky_strategies(self) -> None:
        path = ROOT / "results" / "phase2_step67_init_benchmark_v2" / "metrics_summary.json"
        self.assertTrue(path.exists(), f"Missing v2 init benchmark artifact: {path}")
        rep = json.loads(path.read_text())
        summary = rep.get("summary", {})
        for key in ["window_ar_cluster", "local_ar_gmm_sticky", "residual_gmm_sticky"]:
            self.assertIn(key, summary, f"Expected strategy missing in v2 init benchmark: {key}")

    def test_v2_fastcheck_prevents_zero_support_collapse(self) -> None:
        path = ROOT / "results" / "phase2_step67_multiregime_upgrade_v2_fastcheck" / "metrics_summary.json"
        self.assertTrue(path.exists(), f"Missing v2 fastcheck artifact: {path}")
        rep = json.loads(path.read_text())
        summary = rep.get("summary", {})
        positive_support_delta = 0
        for difficulty in ["easy", "medium", "hard"]:
            up_key = f"{difficulty}_upgraded"
            delta_key = f"{difficulty}_delta"
            self.assertIn(up_key, summary)
            self.assertIn(delta_key, summary)
            self.assertIn("support_nnz_mean", summary[up_key])
            self.assertGreaterEqual(
                summary[up_key]["support_nnz_mean"],
                2.0,
                f"{up_key} support_nnz_mean too small; potential degeneracy",
            )
            if summary[delta_key].get("support_f1_delta", 0.0) > 0:
                positive_support_delta += 1
        self.assertGreaterEqual(
            positive_support_delta,
            2,
            "Expected support-F1 improvements in at least two difficulty tiers for v2 fastcheck.",
        )

    def test_v2_multiseed_upgrade_profile(self) -> None:
        path = ROOT / "results" / "phase2_step67_multiregime_upgrade_v2_multiseed" / "metrics_summary.json"
        self.assertTrue(path.exists(), f"Missing v2 multiseed artifact: {path}")
        rep = json.loads(path.read_text())
        summary = rep.get("summary", {})
        positive_acc_delta = 0
        nontrivial_support_delta = 0
        for difficulty in ["easy", "medium", "hard"]:
            delta_key = f"{difficulty}_delta"
            self.assertIn(delta_key, summary)
            self.assertIn("support_nnz_delta", summary[delta_key])
            if summary[delta_key].get("regime_accuracy_delta", 0.0) > 0:
                positive_acc_delta += 1
            if summary[delta_key].get("support_f1_delta", 0.0) > 0:
                nontrivial_support_delta += 1
        self.assertGreaterEqual(positive_acc_delta, 3, "Expected positive regime-accuracy delta in all tiers.")
        self.assertGreaterEqual(
            nontrivial_support_delta,
            2,
            "Expected support-F1 gains in at least two tiers for v2 multiseed.",
        )


if __name__ == "__main__":
    unittest.main()
