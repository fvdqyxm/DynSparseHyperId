#!/usr/bin/env python3
"""Phase 2 Step 51: amortized variational backbone for q(z_t | y_{1:t})."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch import nn


class RegimeEncoderGRU(nn.Module):
    """Causal encoder producing regime logits for each time step."""

    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int, num_regimes: int) -> None:
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.head = nn.Linear(hidden_dim, num_regimes)

    def forward(self, y: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # y: [batch, time, input_dim]
        h, _ = self.gru(y)
        logits = self.head(h)
        probs = torch.softmax(logits, dim=-1)
        return logits, probs


def run_smoke(
    out_dir: Path,
    seed: int,
    batch_size: int,
    time_steps: int,
    input_dim: int,
    hidden_dim: int,
    num_layers: int,
    num_regimes: int,
) -> dict:
    torch.manual_seed(seed)

    model = RegimeEncoderGRU(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        num_regimes=num_regimes,
    )

    y = torch.randn(batch_size, time_steps, input_dim)
    logits, probs = model(y)

    # Lightweight sanity checks.
    probs_sum = probs.sum(dim=-1)
    max_dev = float(torch.max(torch.abs(probs_sum - 1.0)).item())

    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_dir / "encoder_gru_state.pt")

    report = {
        "seed": seed,
        "batch_size": batch_size,
        "time_steps": time_steps,
        "input_dim": input_dim,
        "hidden_dim": hidden_dim,
        "num_layers": num_layers,
        "num_regimes": num_regimes,
        "logits_shape": list(logits.shape),
        "probs_shape": list(probs.shape),
        "probability_simplex_max_deviation": max_dev,
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step51_backbone"))
    parser.add_argument("--seed", type=int, default=701)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--time-steps", type=int, default=120)
    parser.add_argument("--input-dim", type=int, default=20)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--num-regimes", type=int, default=3)
    args = parser.parse_args()

    report = run_smoke(
        out_dir=args.out_dir,
        seed=args.seed,
        batch_size=args.batch_size,
        time_steps=args.time_steps,
        input_dim=args.input_dim,
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        num_regimes=args.num_regimes,
    )
    print("Step 51 variational backbone smoke check complete.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
