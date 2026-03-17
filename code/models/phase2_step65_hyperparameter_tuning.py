#!/usr/bin/env python3
"""Step 65: hyperparameter tuning proxies (lr, sparsity lambda, smoothness beta)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from phase2_curriculum_training_toy import RegimeEncoderGRU, simulate_sequence_batch, train_encoder
from phase2_temporal_kl_penalty import temporal_kl_penalty
from static_hypergraph_korder import recover_hyperweights_korder, simulate_static_korder_regression, support_metrics_hyper


def tune_learning_rate(seed: int, lrs: list[float]) -> dict:
    x_train, z_train = simulate_sequence_batch(
        batch=32,
        time_steps=80,
        input_dim=20,
        k=3,
        seed=seed,
        sigma=0.40,
        nonlinear=True,
    )
    x_val, z_val = simulate_sequence_batch(
        batch=16,
        time_steps=80,
        input_dim=20,
        k=3,
        seed=seed + 1,
        sigma=0.40,
        nonlinear=True,
    )

    rows = []
    for lr in lrs:
        model = RegimeEncoderGRU(input_dim=20, hidden_dim=64, num_layers=2, num_regimes=3)
        r = train_encoder(
            model=model,
            x_train=x_train,
            z_train=z_train,
            x_val=x_val,
            z_val=z_val,
            epochs=10,
            lr=lr,
        )
        rows.append({"lr": lr, "final_val_loss": float(r["final_val_loss"]), "final_val_acc": float(r["final_val_acc"])})
    best = min(rows, key=lambda x: x["final_val_loss"])
    return {"rows": rows, "best": best}


def tune_lambda(seed: int, alpha_scales: list[float]) -> dict:
    _, phi, y, h_true, _ = simulate_static_korder_regression(
        n=20,
        t=1600,
        k=3,
        edge_prob=0.1,
        noise_sigma=0.35,
        seed=seed,
        max_features=900,
    )
    split = int(0.8 * phi.shape[0])
    phi_tr, y_tr = phi[:split], y[:split]
    phi_te, y_te = phi[split:], y[split:]

    rows = []
    for alpha in alpha_scales:
        h_hat = recover_hyperweights_korder(
            phi=phi_tr,
            y=y_tr,
            seed=seed + int(alpha * 1000),
            cv_complexity_limit=1,  # keep consistent sparse solver during tuning.
            alpha_scale=alpha,
        )
        m = support_metrics_hyper(h_true, h_hat, threshold=0.08)
        mse = float(np.mean((phi_te @ h_hat.T - y_te) ** 2))
        rows.append(
            {
                "lambda_alpha_scale": alpha,
                "support_f1": float(m["f1"]),
                "val_mse": mse,
            }
        )
    best = min(rows, key=lambda x: x["val_mse"])
    return {"rows": rows, "best": best}


def tune_beta(seed: int, betas: list[float]) -> dict:
    rng = np.random.default_rng(seed)
    t = 40
    d = 20
    mu_true = np.cumsum(rng.normal(scale=0.08, size=(t, d)), axis=0)
    mu_noisy = mu_true + rng.normal(scale=0.15, size=(t, d))
    logvars = [np.full((d,), -1.0, dtype=np.float64) for _ in range(t)]

    rows = []
    for beta in betas:
        # Simple beta-dependent smoother proxy.
        alpha = 1.0 / (1.0 + beta)
        mu_s = np.zeros_like(mu_noisy)
        mu_s[0] = mu_noisy[0]
        for i in range(1, t):
            mu_s[i] = alpha * mu_noisy[i] + (1.0 - alpha) * mu_s[i - 1]

        recon_mse = float(np.mean((mu_s - mu_true) ** 2))
        kl_pen = temporal_kl_penalty(
            mus=[mu_s[i] for i in range(t)],
            logvars=logvars,
            beta=beta,
        )
        # Proxy validation objective for smoothness tradeoff.
        val_obj = recon_mse + 1e-3 * kl_pen
        rows.append({"beta_smoothness": beta, "recon_mse": recon_mse, "temporal_kl_penalty": float(kl_pen), "val_obj": val_obj})

    best = min(rows, key=lambda x: x["val_obj"])
    return {"rows": rows, "best": best}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step65_tuning"))
    parser.add_argument("--seed", type=int, default=2301)
    parser.add_argument("--lrs", type=str, default="0.0003,0.001,0.003")
    parser.add_argument("--lambda-scales", type=str, default="0.15,0.25,0.35,0.5,0.7")
    parser.add_argument("--betas", type=str, default="0.01,0.03,0.1,0.3,1.0")
    args = parser.parse_args()

    lrs = [float(x.strip()) for x in args.lrs.split(",") if x.strip()]
    lambdas = [float(x.strip()) for x in args.lambda_scales.split(",") if x.strip()]
    betas = [float(x.strip()) for x in args.betas.split(",") if x.strip()]

    lr_tune = tune_learning_rate(seed=args.seed, lrs=lrs)
    lam_tune = tune_lambda(seed=args.seed + 100, alpha_scales=lambdas)
    beta_tune = tune_beta(seed=args.seed + 200, betas=betas)

    report = {
        "seed": args.seed,
        "learning_rate_tuning": lr_tune,
        "lambda_tuning": lam_tune,
        "beta_tuning": beta_tune,
        "recommended": {
            "lr": lr_tune["best"]["lr"],
            "lambda_alpha_scale": lam_tune["best"]["lambda_alpha_scale"],
            "beta_smoothness": beta_tune["best"]["beta_smoothness"],
        },
        "note": "Step-65 tuning uses executable proxies; full end-to-end joint tuning remains future work.",
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["recommended"], indent=2))


if __name__ == "__main__":
    main()
