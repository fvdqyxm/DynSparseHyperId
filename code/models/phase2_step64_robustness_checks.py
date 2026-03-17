#!/usr/bin/env python3
"""Step 64: robustness checks (outliers, missing data, wrong-k assumption)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from static_hypergraph_korder import (
    recover_hyperweights_korder,
    simulate_static_korder_regression,
    support_metrics_hyper,
)


def _train_val_split(phi: np.ndarray, y: np.ndarray, frac: float = 0.8) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = phi.shape[0]
    split = max(int(frac * n), 2)
    return phi[:split], y[:split], phi[split:], y[split:]


def _fit_eval(phi_tr: np.ndarray, y_tr: np.ndarray, phi_te: np.ndarray, y_te: np.ndarray, h_true: np.ndarray, seed: int) -> dict:
    h_hat = recover_hyperweights_korder(
        phi=phi_tr,
        y=y_tr,
        seed=seed,
        cv_complexity_limit=50_000,
        alpha_scale=0.35,
    )
    m = support_metrics_hyper(h_true, h_hat, threshold=0.08)
    mse = float(np.mean((phi_te @ h_hat.T - y_te) ** 2))
    return {"support_f1": float(m["f1"]), "precision": float(m["precision"]), "recall": float(m["recall"]), "val_mse": mse}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase2_step64_robustness"))
    parser.add_argument("--seed", type=int, default=2101)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    _, phi, y, h_true, _ = simulate_static_korder_regression(
        n=20,
        t=1800,
        k=3,
        edge_prob=0.1,
        noise_sigma=0.30,
        seed=args.seed,
        max_features=900,
    )
    phi_tr, y_tr, phi_te, y_te = _train_val_split(phi, y)

    base = _fit_eval(phi_tr, y_tr, phi_te, y_te, h_true=h_true, seed=args.seed + 1)

    # Outlier corruption on responses.
    y_out = y.copy()
    mask = rng.random(size=y_out.shape) < 0.02
    y_out[mask] += rng.normal(scale=4.0, size=int(np.sum(mask)))
    phi_tr_o, y_tr_o, phi_te_o, y_te_o = _train_val_split(phi, y_out)
    outlier = _fit_eval(phi_tr_o, y_tr_o, phi_te_o, y_te_o, h_true=h_true, seed=args.seed + 2)

    # Missing-data corruption in feature library with mean imputation.
    phi_miss = phi.copy()
    miss_mask = rng.random(size=phi_miss.shape) < 0.10
    phi_miss[miss_mask] = np.nan
    col_means = np.nanmean(phi_miss, axis=0)
    inds = np.where(np.isnan(phi_miss))
    phi_miss[inds] = np.take(col_means, inds[1])
    phi_tr_m, y_tr_m, phi_te_m, y_te_m = _train_val_split(phi_miss, y)
    missing = _fit_eval(phi_tr_m, y_tr_m, phi_te_m, y_te_m, h_true=h_true, seed=args.seed + 3)

    # Wrong-k assumption: generate k=4 but fit k=3-like library by truncating features.
    _, phi4, y4, h4_true, _ = simulate_static_korder_regression(
        n=20,
        t=1800,
        k=4,
        edge_prob=0.1,
        noise_sigma=0.30,
        seed=args.seed + 50,
        max_features=900,
    )
    phi4_tr, y4_tr, phi4_te, y4_te = _train_val_split(phi4, y4)
    wrongk_true = _fit_eval(phi4_tr, y4_tr, phi4_te, y4_te, h_true=h4_true, seed=args.seed + 4)
    # Mimic wrong-order assumption by aggressively shrinking dictionary.
    keep = min(180, phi4.shape[1])
    phi_wrong = phi4[:, :keep]
    h4_true_wrong = h4_true[:, :keep]
    phiw_tr, yw_tr, phiw_te, yw_te = _train_val_split(phi_wrong, y4)
    wrongk_fit = _fit_eval(phiw_tr, yw_tr, phiw_te, yw_te, h_true=h4_true_wrong, seed=args.seed + 5)

    report = {
        "seed": args.seed,
        "base": base,
        "outlier": outlier,
        "missing_data": missing,
        "wrong_k_true_library": wrongk_true,
        "wrong_k_restricted_library": wrongk_fit,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"base_f1": base["support_f1"], "outlier_f1": outlier["support_f1"], "missing_f1": missing["support_f1"]}, indent=2))


if __name__ == "__main__":
    main()
