#!/usr/bin/env python3
"""Phase 2 Step 52: HypergraphConv emission scaffold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch import nn
from torch_geometric.nn import HypergraphConv


class HypergraphEmissionModel(nn.Module):
    """Minimal hypergraph-convolutional emission block."""

    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int) -> None:
        super().__init__()
        self.conv1 = HypergraphConv(in_dim, hidden_dim)
        self.act = nn.ReLU()
        self.conv2 = HypergraphConv(hidden_dim, out_dim)

    def forward(self, x: torch.Tensor, hyperedge_index: torch.Tensor) -> torch.Tensor:
        h = self.conv1(x, hyperedge_index)
        h = self.act(h)
        y = self.conv2(h, hyperedge_index)
        return y


def build_simple_triplet_hypergraph(n: int) -> torch.Tensor:
    """Construct a simple 3-uniform-style hyperedge incidence index.

    Uses sliding triplets (i, i+1, i+2) modulo n as a small smoke-test hypergraph.
    """
    rows = []
    cols = []
    edge_id = 0
    for i in range(n):
        nodes = [i, (i + 1) % n, (i + 2) % n]
        for node in nodes:
            rows.append(node)
            cols.append(edge_id)
        edge_id += 1

    return torch.tensor([rows, cols], dtype=torch.long)


def run_smoke(
    out_dir: Path,
    seed: int,
    n_nodes: int,
    in_dim: int,
    hidden_dim: int,
    out_dim: int,
) -> dict:
    torch.manual_seed(seed)

    model = HypergraphEmissionModel(in_dim=in_dim, hidden_dim=hidden_dim, out_dim=out_dim)
    x = torch.randn(n_nodes, in_dim)
    hidx = build_simple_triplet_hypergraph(n_nodes)

    y = model(x, hidx)

    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_dir / "hypergraph_emission_state.pt")

    report = {
        "seed": seed,
        "n_nodes": n_nodes,
        "in_dim": in_dim,
        "hidden_dim": hidden_dim,
        "out_dim": out_dim,
        "num_hyperedge_connections": int(hidx.shape[1]),
        "output_shape": list(y.shape),
        "output_mean_abs": float(torch.mean(torch.abs(y)).item()),
    }
    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step52_hypergraph_emission"))
    parser.add_argument("--seed", type=int, default=702)
    parser.add_argument("--n-nodes", type=int, default=20)
    parser.add_argument("--in-dim", type=int, default=16)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--out-dim", type=int, default=16)
    args = parser.parse_args()

    report = run_smoke(
        out_dir=args.out_dir,
        seed=args.seed,
        n_nodes=args.n_nodes,
        in_dim=args.in_dim,
        hidden_dim=args.hidden_dim,
        out_dim=args.out_dim,
    )
    print("Step 52 hypergraph emission smoke check complete.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
