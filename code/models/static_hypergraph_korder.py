#!/usr/bin/env python3
"""Generic static sparse k-order interaction surrogate (k>=3)."""

from __future__ import annotations

import itertools
import math
from typing import Sequence

import numpy as np
from numpy.typing import NDArray
from sklearn.linear_model import Lasso, LassoCV


Array = NDArray[np.float64]


def _sample_index_tuples(
    n: int,
    order: int,
    max_features: int,
    rng: np.random.Generator,
) -> list[tuple[int, ...]]:
    if order <= 0:
        raise ValueError("order must be >=1")

    total = int(math.comb(n, order))
    if total <= max_features:
        return list(itertools.combinations(range(n), order))

    # Deterministic-size random candidate pool to keep high-order runs tractable.
    chosen: set[tuple[int, ...]] = set()
    while len(chosen) < max_features:
        idx = tuple(sorted(rng.choice(n, size=order, replace=False).tolist()))
        chosen.add(idx)
    return sorted(chosen)


def _build_features(x: Array, combos: Sequence[tuple[int, ...]]) -> Array:
    phi = np.empty((x.shape[0], len(combos)), dtype=np.float64)
    for col, combo in enumerate(combos):
        phi[:, col] = np.prod(x[:, combo], axis=1)
    return phi


def simulate_static_korder_regression(
    n: int,
    t: int,
    k: int,
    edge_prob: float,
    noise_sigma: float,
    seed: int,
    max_features: int = 2500,
    min_abs: float = 0.05,
    max_abs: float = 0.25,
) -> tuple[Array, Array, Array, Array, list[tuple[int, ...]]]:
    if k < 3:
        raise ValueError("k must be >=3")
    if max_features < 10:
        raise ValueError("max_features too small")

    rng = np.random.default_rng(seed)
    combos = _sample_index_tuples(n=n, order=k - 1, max_features=max_features, rng=rng)
    p = len(combos)

    h_true = np.zeros((n, p), dtype=np.float64)
    for target in range(n):
        mask = rng.random(p) < edge_prob
        signs = rng.choice(np.array([-1.0, 1.0]), size=p)
        mags = rng.uniform(min_abs, max_abs, size=p)
        h_true[target] = mask * signs * mags

    x = rng.normal(loc=0.0, scale=1.0, size=(t, n))
    phi = _build_features(x, combos=combos)
    y = phi @ h_true.T + rng.normal(scale=noise_sigma, size=(t, n))
    return x, phi, y, h_true, combos


def recover_hyperweights_korder(
    phi: Array,
    y: Array,
    seed: int,
    cv_folds: int = 5,
    cv_complexity_limit: int = 2_000_000,
    alpha_scale: float = 0.35,
) -> Array:
    n = y.shape[1]
    h_hat = np.zeros((n, phi.shape[1]), dtype=np.float64)
    sample_count = phi.shape[0]
    feature_count = phi.shape[1]
    use_cv = (sample_count * feature_count) <= cv_complexity_limit

    for target in range(n):
        if use_cv:
            # Fold cap avoids small-sample CV failures.
            folds = max(2, min(cv_folds, y.shape[0] // 2))
            reg = LassoCV(
                cv=folds,
                fit_intercept=False,
                random_state=seed + target,
                max_iter=20000,
                alphas=60,
                n_jobs=1,
            )
            reg.fit(phi, y[:, target])

            mse_mean = np.mean(reg.mse_path_, axis=1)
            mse_std = np.std(reg.mse_path_, axis=1, ddof=1) / np.sqrt(reg.mse_path_.shape[1])
            idx_min = int(np.argmin(mse_mean))
            mse_1se = mse_mean[idx_min] + mse_std[idx_min]
            idx_1se = int(np.min(np.where(mse_mean <= mse_1se)[0]))
            alpha_1se = float(reg.alphas_[idx_1se])
            alpha_min = float(reg.alpha_)
            alpha_mid = float(np.sqrt(alpha_min * alpha_1se))
        else:
            # High-dimensional fallback: theoretically motivated alpha scaling.
            response_scale = float(np.std(y[:, target]) + 1e-12)
            alpha_mid = float(alpha_scale * response_scale * np.sqrt(np.log(feature_count + 1.0) / sample_count))

        sparse = Lasso(alpha=alpha_mid, fit_intercept=False, max_iter=20000)
        sparse.fit(phi, y[:, target])
        h_hat[target] = sparse.coef_

    return h_hat


def support_metrics_hyper(true_h: Array, est_h: Array, threshold: float) -> dict[str, float | int]:
    true_mask = np.abs(true_h) > 1e-9
    pred_mask = np.abs(est_h) >= threshold

    tp = int(np.sum(true_mask & pred_mask))
    fp = int(np.sum(~true_mask & pred_mask))
    fn = int(np.sum(true_mask & ~pred_mask))
    tn = int(np.sum(~true_mask & ~pred_mask))

    precision = float(tp / (tp + fp + 1e-12))
    recall = float(tp / (tp + fn + 1e-12))
    f1 = float(2.0 * precision * recall / (precision + recall + 1e-12))

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }
