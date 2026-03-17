#!/usr/bin/env python3
"""Phase 2 Step 55: curriculum training toy (k=2 pretrain -> k=3 fine-tune)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from phase0_baselines import sample_markov_chain
from phase2_variational_backbone import RegimeEncoderGRU


def simulate_sequence_batch(
    batch: int,
    time_steps: int,
    input_dim: int,
    k: int,
    seed: int,
    sigma: float,
    nonlinear: bool,
) -> tuple[torch.Tensor, torch.Tensor]:
    rng = np.random.default_rng(seed)

    # Regime-specific linear maps.
    a_list = []
    for _ in range(k):
        a = rng.normal(scale=0.12, size=(input_dim, input_dim))
        np.fill_diagonal(a, rng.uniform(0.05, 0.25, size=input_dim))
        a_list.append(a)

    transition = np.full((k, k), 0.04 / max(k - 1, 1), dtype=np.float64)
    np.fill_diagonal(transition, 0.96)
    init = np.full(k, 1.0 / k, dtype=np.float64)

    ys = np.zeros((batch, time_steps, input_dim), dtype=np.float32)
    zs = np.zeros((batch, time_steps), dtype=np.int64)

    for b in range(batch):
        z = sample_markov_chain(time_steps, transition=transition, init_probs=init, rng=rng)
        y = np.zeros((time_steps, input_dim), dtype=np.float64)
        y[0] = rng.normal(scale=0.5, size=input_dim)
        for t in range(1, time_steps):
            pred = a_list[z[t]] @ y[t - 1]
            if nonlinear:
                pred += 0.05 * np.tanh(y[t - 1] ** 2)
            y[t] = pred + rng.normal(scale=sigma, size=input_dim)
        ys[b] = y.astype(np.float32)
        zs[b] = z

    return torch.from_numpy(ys), torch.from_numpy(zs)


def train_encoder(
    model: RegimeEncoderGRU,
    x_train: torch.Tensor,
    z_train: torch.Tensor,
    x_val: torch.Tensor,
    z_val: torch.Tensor,
    epochs: int,
    lr: float,
) -> dict:
    device = torch.device("cpu")
    model = model.to(device)
    x_train = x_train.to(device)
    z_train = z_train.to(device)
    x_val = x_val.to(device)
    z_val = z_val.to(device)

    opt = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    train_loss_hist = []
    val_loss_hist = []
    val_acc_hist = []

    for _ in range(epochs):
        model.train()
        opt.zero_grad(set_to_none=True)
        logits, _ = model(x_train)
        loss = criterion(logits.reshape(-1, logits.size(-1)), z_train.reshape(-1))
        loss.backward()
        opt.step()

        model.eval()
        with torch.no_grad():
            logits_val, _ = model(x_val)
            val_loss = criterion(logits_val.reshape(-1, logits_val.size(-1)), z_val.reshape(-1))
            pred = torch.argmax(logits_val, dim=-1)
            val_acc = torch.mean((pred == z_val).float())

        train_loss_hist.append(float(loss.item()))
        val_loss_hist.append(float(val_loss.item()))
        val_acc_hist.append(float(val_acc.item()))

    return {
        "train_loss_history": train_loss_hist,
        "val_loss_history": val_loss_hist,
        "val_acc_history": val_acc_hist,
        "final_val_loss": val_loss_hist[-1],
        "final_val_acc": val_acc_hist[-1],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step55_curriculum"))
    parser.add_argument("--seed", type=int, default=705)
    parser.add_argument("--input-dim", type=int, default=20)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--time-steps", type=int, default=80)
    parser.add_argument("--train-batch", type=int, default=32)
    parser.add_argument("--val-batch", type=int, default=16)
    parser.add_argument("--epochs-pretrain", type=int, default=12)
    parser.add_argument("--epochs-finetune", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--num-layers", type=int, default=2)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    x_k2_train, z_k2_train = simulate_sequence_batch(
        batch=args.train_batch,
        time_steps=args.time_steps,
        input_dim=args.input_dim,
        k=args.k,
        seed=args.seed,
        sigma=0.35,
        nonlinear=False,
    )
    x_k2_val, z_k2_val = simulate_sequence_batch(
        batch=args.val_batch,
        time_steps=args.time_steps,
        input_dim=args.input_dim,
        k=args.k,
        seed=args.seed + 1,
        sigma=0.35,
        nonlinear=False,
    )

    x_k3_train, z_k3_train = simulate_sequence_batch(
        batch=args.train_batch,
        time_steps=args.time_steps,
        input_dim=args.input_dim,
        k=args.k,
        seed=args.seed + 2,
        sigma=0.40,
        nonlinear=True,
    )
    x_k3_val, z_k3_val = simulate_sequence_batch(
        batch=args.val_batch,
        time_steps=args.time_steps,
        input_dim=args.input_dim,
        k=args.k,
        seed=args.seed + 3,
        sigma=0.40,
        nonlinear=True,
    )

    # Curriculum path: pretrain on simpler k=2-like linear dynamics, then fine-tune on harder nonlinear data.
    model_curr = RegimeEncoderGRU(
        input_dim=args.input_dim,
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        num_regimes=args.k,
    )
    pre = train_encoder(
        model=model_curr,
        x_train=x_k2_train,
        z_train=z_k2_train,
        x_val=x_k2_val,
        z_val=z_k2_val,
        epochs=args.epochs_pretrain,
        lr=args.lr,
    )
    finetune = train_encoder(
        model=model_curr,
        x_train=x_k3_train,
        z_train=z_k3_train,
        x_val=x_k3_val,
        z_val=z_k3_val,
        epochs=args.epochs_finetune,
        lr=args.lr,
    )

    # Scratch path on harder data only.
    model_scratch = RegimeEncoderGRU(
        input_dim=args.input_dim,
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        num_regimes=args.k,
    )
    scratch = train_encoder(
        model=model_scratch,
        x_train=x_k3_train,
        z_train=z_k3_train,
        x_val=x_k3_val,
        z_val=z_k3_val,
        epochs=args.epochs_finetune,
        lr=args.lr,
    )

    report = {
        "config": {
            "seed": args.seed,
            "input_dim": args.input_dim,
            "k": args.k,
            "time_steps": args.time_steps,
            "train_batch": args.train_batch,
            "val_batch": args.val_batch,
            "epochs_pretrain": args.epochs_pretrain,
            "epochs_finetune": args.epochs_finetune,
            "lr": args.lr,
        },
        "pretrain_k2": pre,
        "finetune_k3_from_curriculum": finetune,
        "scratch_k3": scratch,
        "curriculum_gain": {
            "val_loss_delta": float(scratch["final_val_loss"] - finetune["final_val_loss"]),
            "val_acc_delta": float(finetune["final_val_acc"] - scratch["final_val_acc"]),
        },
    }

    (out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    print("Step 55 curriculum toy complete.")
    print(json.dumps(report["curriculum_gain"], indent=2))


if __name__ == "__main__":
    main()
