#!/usr/bin/env python3
"""Phase 3 Step 73: visualize recovered motifs/network-style summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step70-metrics", type=Path, default=Path("results/phase3_step70_motifs/metrics_summary.json"))
    parser.add_argument("--motif-basis", type=Path, default=Path("results/phase3_step70_motifs/motif_basis.npy"))
    parser.add_argument("--motif-scores", type=Path, default=Path("results/phase3_step70_motifs/motif_scores.npy"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase3_step73_visuals"))
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.step70_metrics.exists() or not args.motif_basis.exists() or not args.motif_scores.exists():
        report = {
            "status": "blocked_missing_step70_outputs",
            "issues": ["Missing motif artifacts from Step70."],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    m70 = json.loads(args.step70_metrics.read_text())
    if m70.get("status") != "ok":
        report = {
            "status": "blocked_step70_not_ready",
            "step70_status": m70.get("status"),
            "issues": ["Step70 not in ready state."],
        }
        (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    basis = np.load(args.motif_basis)
    scores = np.load(args.motif_scores)

    fig1, ax1 = plt.subplots(1, 1, figsize=(8, 4))
    im = ax1.imshow(basis, aspect="auto", cmap="coolwarm")
    ax1.set_title("Motif Basis (Components x Features)")
    ax1.set_xlabel("Feature Index")
    ax1.set_ylabel("Component")
    fig1.colorbar(im, ax=ax1, shrink=0.8)
    fig1.tight_layout()
    fig1.savefig(out_dir / "motif_basis_heatmap.png", dpi=170)
    plt.close(fig1)

    fig2, ax2 = plt.subplots(1, 1, figsize=(8, 4))
    for j in range(min(5, scores.shape[1])):
        ax2.plot(scores[:, j], label=f"motif_{j}")
    ax2.set_title("Subject-Level Motif Scores")
    ax2.set_xlabel("Subject Index")
    ax2.set_ylabel("Score")
    ax2.legend(loc="best", fontsize=8)
    ax2.grid(alpha=0.25)
    fig2.tight_layout()
    fig2.savefig(out_dir / "motif_scores_lines.png", dpi=170)
    plt.close(fig2)

    report = {
        "status": "ok",
        "n_subjects": int(scores.shape[0]),
        "n_motifs": int(scores.shape[1]),
        "figures": [
            str(out_dir / "motif_basis_heatmap.png"),
            str(out_dir / "motif_scores_lines.png"),
        ],
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"status": "ok", "n_motifs": scores.shape[1]}, indent=2))


if __name__ == "__main__":
    main()
