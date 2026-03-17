#!/usr/bin/env python3
"""Phase 0 reproducible baselines for DynSparseHyperId.

This script covers:
1. Sparse Graphical Lasso recovery on toy Gaussian data (Step 12/13).
2. Sparse linear dynamical system recovery with L1 regression (Step 14/15).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from itertools import permutations
from pathlib import Path
from typing import Iterable

import numpy as np
from numpy.typing import NDArray
from scipy.special import logsumexp
from sklearn.cluster import KMeans
from sklearn.covariance import GraphicalLasso
from sklearn.decomposition import PCA
from sklearn.linear_model import Lasso, LassoCV
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler


Array = NDArray[np.float64]


@dataclass
class SupportMetrics:
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int
    tn: int


def _off_diagonal_mask(n: int) -> NDArray[np.bool_]:
    mask = np.ones((n, n), dtype=bool)
    np.fill_diagonal(mask, False)
    return mask


def support_metrics(
    truth: Array,
    estimate: Array,
    threshold: float = 1e-6,
    include_diagonal: bool = False,
) -> SupportMetrics:
    true_support = np.abs(truth) > threshold
    est_support = np.abs(estimate) > threshold

    if not include_diagonal:
        mask = _off_diagonal_mask(truth.shape[0])
        true_support = true_support[mask]
        est_support = est_support[mask]
    else:
        true_support = true_support.reshape(-1)
        est_support = est_support.reshape(-1)

    tp = int(np.sum(true_support & est_support))
    fp = int(np.sum(~true_support & est_support))
    fn = int(np.sum(true_support & ~est_support))
    tn = int(np.sum(~true_support & ~est_support))

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2.0 * precision * recall / max(precision + recall, 1e-12)
    return SupportMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
    )


def make_sparse_precision(
    n: int,
    edge_prob: float,
    rng: np.random.Generator,
    weight_low: float = 0.2,
    weight_high: float = 0.6,
    min_diag_margin: float = 0.5,
) -> Array:
    upper_mask = rng.random((n, n)) < edge_prob
    upper_mask = np.triu(upper_mask, k=1)

    weights = rng.uniform(weight_low, weight_high, size=(n, n))
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n, n))
    upper = upper_mask * weights * signs
    precision = upper + upper.T

    row_sums = np.sum(np.abs(precision), axis=1)
    np.fill_diagonal(precision, row_sums + min_diag_margin)
    return precision


def run_graphical_lasso(
    n: int,
    t: int,
    edge_prob: float,
    alpha_grid: Iterable[float],
    seed: int,
    out_dir: Path,
    support_threshold: float,
) -> dict:
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(seed)
    precision_true = make_sparse_precision(n=n, edge_prob=edge_prob, rng=rng)
    covariance_true = np.linalg.inv(precision_true)
    x = rng.multivariate_normal(
        mean=np.zeros(n),
        cov=covariance_true,
        size=t,
    )

    split = int(0.7 * t)
    x_train = x[:split]
    x_val = x[split:]

    best_alpha = None
    best_ll = -np.inf
    best_ebic = np.inf
    best_model = None
    train_size = x_train.shape[0]
    for alpha in alpha_grid:
        model = GraphicalLasso(alpha=alpha, max_iter=500)
        model.fit(x_train)
        ll_train = float(model.score(x_train)) * train_size
        ll_val = float(model.score(x_val))
        nonzero_offdiag = int(
            np.sum(np.abs(np.triu(model.precision_, k=1)) > support_threshold)
        )
        k_params = n + nonzero_offdiag
        bic = -2.0 * ll_train + k_params * np.log(train_size)
        gamma = 0.5
        ebic = bic + 4.0 * gamma * nonzero_offdiag * np.log(n)

        if ebic < best_ebic:
            best_ebic = ebic
            best_ll = ll_val
            best_alpha = alpha
            best_model = model

    assert best_model is not None
    precision_hat = best_model.precision_
    metrics = support_metrics(precision_true, precision_hat, threshold=support_threshold)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "precision_true.npy", precision_true)
    np.save(out_dir / "precision_hat.npy", precision_hat)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    vmax = max(np.max(np.abs(precision_true)), np.max(np.abs(precision_hat)))
    axes[0].imshow(precision_true, cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes[0].set_title("True Precision")
    axes[1].imshow(precision_hat, cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes[1].set_title("Recovered Precision")
    for ax in axes:
        ax.set_xlabel("Node")
        ax.set_ylabel("Node")
    plt.tight_layout()
    fig.savefig(out_dir / "precision_recovery.png", dpi=160)
    plt.close(fig)

    return {
        "n": n,
        "t": t,
        "edge_prob": edge_prob,
        "best_alpha": best_alpha,
        "best_ebic": best_ebic,
        "best_val_log_likelihood": best_ll,
        "support_threshold": support_threshold,
        "support_metrics": asdict(metrics),
    }


def make_sparse_stable_A(
    n: int,
    edge_prob: float,
    rng: np.random.Generator,
    scale: float = 0.35,
    target_radius: float = 0.85,
    min_abs_weight: float | None = None,
) -> Array:
    if min_abs_weight is None:
        min_abs_weight = 0.35 * scale
    if min_abs_weight <= 0 or min_abs_weight > scale:
        raise ValueError("min_abs_weight must satisfy 0 < min_abs_weight <= scale")

    mask = rng.random((n, n)) < edge_prob
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n, n))
    magnitudes = rng.uniform(min_abs_weight, scale, size=(n, n))
    weights = signs * magnitudes
    a = mask * weights
    np.fill_diagonal(a, rng.uniform(0.1, 0.3, size=n))

    eigvals = np.linalg.eigvals(a)
    radius = float(np.max(np.abs(eigvals)))
    if radius > target_radius:
        a *= target_radius / radius
    return a


def simulate_lds(
    a: Array,
    t: int,
    sigma: float,
    burn_in: int,
    rng: np.random.Generator,
) -> Array:
    n = a.shape[0]
    x = np.zeros((t + burn_in, n), dtype=np.float64)
    # Keep initial state scale fixed so sigma controls process noise/SNR.
    x[0] = rng.normal(scale=1.0, size=n)
    for i in range(1, t + burn_in):
        noise = rng.normal(scale=sigma, size=n)
        x[i] = a @ x[i - 1] + noise
    return x[burn_in:]


def recover_A_lasso_cv_1se(
    x: Array,
    seed: int,
    cv_complexity_limit: int = 2_000_000,
    alpha_scale: float = 0.35,
) -> Array:
    x_prev = x[:-1]
    x_next = x[1:]
    return recover_A_from_pairs_cv(
        x_prev=x_prev,
        x_next=x_next,
        seed=seed,
        cv_complexity_limit=cv_complexity_limit,
        alpha_scale=alpha_scale,
    )


def recover_A_from_pairs_cv(
    x_prev: Array,
    x_next: Array,
    seed: int,
    cv_complexity_limit: int = 2_000_000,
    alpha_scale: float = 0.35,
) -> Array:
    n = x_prev.shape[1]
    n_samples = x_prev.shape[0]

    # Fundamental guard: low-occupancy regime slices cannot support 5-fold CV.
    # Use a stable ridge fallback instead of crashing or overfitting tiny folds.
    if n_samples < 6:
        return fit_A_ridge(x_prev=x_prev, x_next=x_next, ridge_lambda=1e-2)

    use_cv = (n_samples * n) <= cv_complexity_limit
    cv_folds = min(5, max(2, n_samples // 2))
    a_hat = np.zeros((n, n), dtype=np.float64)

    for target_idx in range(n):
        if use_cv:
            reg = LassoCV(
                cv=cv_folds,
                fit_intercept=False,
                random_state=seed + target_idx,
                max_iter=10000,
                alphas=100,
                n_jobs=1,
            )
            reg.fit(x_prev, x_next[:, target_idx])
            mse_mean = np.mean(reg.mse_path_, axis=1)
            mse_std = np.std(reg.mse_path_, axis=1, ddof=1) / np.sqrt(reg.mse_path_.shape[1])
            idx_min = int(np.argmin(mse_mean))
            mse_1se = mse_mean[idx_min] + mse_std[idx_min]

            candidate = np.where(mse_mean <= mse_1se)[0]
            # reg.alphas_ is descending; choose highest alpha within 1SE for sparsity.
            idx_1se = int(np.min(candidate))
            alpha_1se = float(reg.alphas_[idx_1se])

            alpha_min = float(reg.alpha_)
            alpha_mid = float(np.sqrt(alpha_min * alpha_1se))
        else:
            response_scale = float(np.std(x_next[:, target_idx]) + 1e-12)
            alpha_mid = float(alpha_scale * response_scale * np.sqrt(np.log(n + 1.0) / n_samples))

        sparse_reg = Lasso(alpha=alpha_mid, fit_intercept=False, max_iter=10000)
        sparse_reg.fit(x_prev, x_next[:, target_idx])
        a_hat[target_idx, :] = sparse_reg.coef_
    return a_hat


def fit_sparse_A_fixed_alpha(
    x_prev: Array,
    x_next: Array,
    alpha: float,
) -> Array:
    n = x_prev.shape[1]
    a_hat = np.zeros((n, n), dtype=np.float64)
    for target_idx in range(n):
        reg = Lasso(alpha=alpha, fit_intercept=False, max_iter=10000)
        reg.fit(x_prev, x_next[:, target_idx])
        a_hat[target_idx, :] = reg.coef_
    return a_hat


def fit_A_ridge(
    x_prev: Array,
    x_next: Array,
    ridge_lambda: float = 1e-2,
) -> Array:
    n = x_prev.shape[1]
    xtx = x_prev.T @ x_prev + ridge_lambda * np.eye(n)
    xty = x_prev.T @ x_next
    beta = np.linalg.solve(xtx, xty)  # features x targets
    return beta.T


def run_sparse_lds(
    n: int,
    t: int,
    edge_prob: float,
    sigma: float,
    seed: int,
    out_dir: Path,
    support_threshold: float,
    cv_complexity_limit: int = 2_000_000,
    alpha_scale: float = 0.35,
) -> dict:
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(seed)
    a_true = make_sparse_stable_A(n=n, edge_prob=edge_prob, rng=rng)
    x = simulate_lds(a=a_true, t=t, sigma=sigma, burn_in=200, rng=rng)

    split = int(0.8 * t)
    x_train = x[:split]
    x_val = x[split - 1 :]

    a_hat = recover_A_lasso_cv_1se(
        x_train,
        seed=seed + 17,
        cv_complexity_limit=cv_complexity_limit,
        alpha_scale=alpha_scale,
    )
    metrics = support_metrics(
        a_true,
        a_hat,
        threshold=support_threshold,
        include_diagonal=False,
    )

    pred = (a_hat @ x_val[:-1].T).T
    mse = float(np.mean((pred - x_val[1:]) ** 2))

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "A_true.npy", a_true)
    np.save(out_dir / "A_hat.npy", a_hat)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    vmax = max(np.max(np.abs(a_true)), np.max(np.abs(a_hat)))
    axes[0].imshow(a_true, cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes[0].set_title("True A")
    axes[1].imshow(a_hat, cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes[1].set_title("Recovered A")
    for ax in axes:
        ax.set_xlabel("Source")
        ax.set_ylabel("Target")
    plt.tight_layout()
    fig.savefig(out_dir / "A_recovery.png", dpi=160)
    plt.close(fig)

    return {
        "n": n,
        "t": t,
        "edge_prob": edge_prob,
        "sigma": sigma,
        "validation_one_step_mse": mse,
        "support_threshold": support_threshold,
        "support_metrics": asdict(metrics),
    }


def sample_markov_chain(
    t: int,
    transition: Array,
    init_probs: Array,
    rng: np.random.Generator,
) -> NDArray[np.int64]:
    k = transition.shape[0]
    z = np.zeros(t, dtype=np.int64)
    z[0] = rng.choice(k, p=init_probs)
    for i in range(1, t):
        z[i] = rng.choice(k, p=transition[z[i - 1]])
    return z


def simulate_switching_lds(
    a_list: list[Array],
    z: NDArray[np.int64],
    sigma: float,
    rng: np.random.Generator,
) -> Array:
    n = a_list[0].shape[0]
    t = len(z)
    x = np.zeros((t, n), dtype=np.float64)
    # Keep initial state scale fixed so sigma controls process noise/SNR.
    x[0] = rng.normal(scale=1.0, size=n)
    for i in range(1, t):
        regime = z[i]
        x[i] = a_list[regime] @ x[i - 1] + rng.normal(scale=sigma, size=n)
    return x


def estimate_transition_matrix(
    labels: NDArray[np.int64],
    k: int,
    smoothing: float = 1.0,
) -> Array:
    counts = np.full((k, k), smoothing, dtype=np.float64)
    for i in range(1, len(labels)):
        counts[labels[i - 1], labels[i]] += 1.0
    counts /= counts.sum(axis=1, keepdims=True)
    return counts


def viterbi_decode(
    log_emission: Array,
    log_transition: Array,
    log_init: Array,
) -> NDArray[np.int64]:
    t_len, k = log_emission.shape
    dp = np.full((t_len, k), -np.inf, dtype=np.float64)
    back = np.zeros((t_len, k), dtype=np.int64)

    dp[0] = log_init + log_emission[0]
    for t in range(1, t_len):
        for curr in range(k):
            vals = dp[t - 1] + log_transition[:, curr]
            prev = int(np.argmax(vals))
            dp[t, curr] = vals[prev] + log_emission[t, curr]
            back[t, curr] = prev

    labels = np.zeros(t_len, dtype=np.int64)
    labels[-1] = int(np.argmax(dp[-1]))
    for t in range(t_len - 2, -1, -1):
        labels[t] = back[t + 1, labels[t + 1]]
    return labels


def compute_log_emission(
    x_prev: Array,
    x_next: Array,
    a_list: list[Array],
    sigma2: float,
) -> Array:
    m = x_prev.shape[0]
    k = len(a_list)
    n = x_prev.shape[1]
    sigma2 = max(sigma2, 1e-8)
    const = -0.5 * n * np.log(2.0 * np.pi * sigma2)
    out = np.zeros((m, k), dtype=np.float64)
    for regime in range(k):
        residual = x_next - x_prev @ a_list[regime].T
        sq_err = np.sum(residual**2, axis=1)
        out[:, regime] = const - 0.5 * sq_err / sigma2
    return out


def forward_backward_hmm(
    log_emission: Array,
    transition: Array,
    init: Array,
) -> tuple[Array, Array, float]:
    t_len, k = log_emission.shape
    eps = 1e-12
    log_transition = np.log(transition + eps)
    log_init = np.log(init + eps)

    log_alpha = np.full((t_len, k), -np.inf, dtype=np.float64)
    log_alpha[0] = log_init + log_emission[0]
    for t in range(1, t_len):
        for curr in range(k):
            log_alpha[t, curr] = log_emission[t, curr] + logsumexp(
                log_alpha[t - 1] + log_transition[:, curr]
            )

    log_beta = np.zeros((t_len, k), dtype=np.float64)
    for t in range(t_len - 2, -1, -1):
        for prev in range(k):
            log_beta[t, prev] = logsumexp(
                log_transition[prev] + log_emission[t + 1] + log_beta[t + 1]
            )

    loglik = float(logsumexp(log_alpha[-1]))
    log_gamma = log_alpha + log_beta - loglik
    gamma = np.exp(log_gamma)
    gamma /= np.maximum(gamma.sum(axis=1, keepdims=True), 1e-12)

    xi_sum = np.zeros((k, k), dtype=np.float64)
    for t in range(t_len - 1):
        log_xi_t = (
            log_alpha[t][:, None]
            + log_transition
            + log_emission[t + 1][None, :]
            + log_beta[t + 1][None, :]
            - loglik
        )
        xi_sum += np.exp(log_xi_t)

    return gamma, xi_sum, loglik


def fit_A_weighted_ridge(
    x_prev: Array,
    x_next: Array,
    weights: Array,
    ridge_lambda: float,
    fallback: Array,
) -> Array:
    n = x_prev.shape[1]
    eff_n = float(np.sum(weights))
    if eff_n < max(4 * n, 80):
        return fallback.copy()
    sw = np.sqrt(np.clip(weights, 1e-12, None))
    xw = x_prev * sw[:, None]
    yw = x_next * sw[:, None]
    xtx = xw.T @ xw + ridge_lambda * np.eye(n)
    xty = xw.T @ yw
    beta = np.linalg.solve(xtx, xty)  # features x targets
    return beta.T


def _local_ar_features(
    x_prev: Array,
    x_next: Array,
    window: int,
) -> Array:
    m, n = x_prev.shape
    min_samples = max(4 * n, 20)
    base_a = fit_A_ridge(x_prev, x_next, ridge_lambda=1e-2)
    local_features = np.zeros((m, n * n), dtype=np.float64)
    for t in range(m):
        s = max(0, t - window // 2)
        e = min(m, s + window)
        if e - s < min_samples:
            local_a = base_a
        else:
            local_a = fit_A_ridge(x_prev[s:e], x_next[s:e], ridge_lambda=1e-2)
        local_features[t] = local_a.reshape(-1)
    return local_features


def _sticky_distance_decode(
    distance: Array,
    switch_penalty: float,
) -> NDArray[np.int64]:
    t_len, k = distance.shape
    dp = np.full((t_len, k), np.inf, dtype=np.float64)
    back = np.zeros((t_len, k), dtype=np.int64)
    dp[0] = distance[0]
    for t in range(1, t_len):
        prev_cost = dp[t - 1][:, None] + switch_penalty
        np.fill_diagonal(prev_cost, dp[t - 1])
        back[t] = np.argmin(prev_cost, axis=0)
        dp[t] = distance[t] + np.min(prev_cost, axis=0)
    labels = np.zeros(t_len, dtype=np.int64)
    labels[-1] = int(np.argmin(dp[-1]))
    for t in range(t_len - 2, -1, -1):
        labels[t] = back[t + 1, labels[t + 1]]
    return labels


def _project_features(features: Array, seed: int) -> Array:
    standardized = StandardScaler(with_mean=True, with_std=True).fit_transform(features)
    pca_dim = max(2, min(12, standardized.shape[1], standardized.shape[0] - 1))
    return PCA(n_components=pca_dim, random_state=seed).fit_transform(standardized)


def _count_offdiag_nonzeros(a_list: list[Array], threshold: float) -> int:
    total = 0
    for a in a_list:
        mask = np.abs(a) > threshold
        np.fill_diagonal(mask, False)
        total += int(np.sum(mask))
    return total


def _candidate_selection_score(
    *,
    selection_mode: str,
    selection_penalty: float,
    selection_gamma: float,
    ll_sparse: float,
    a_sparse: list[Array],
    support_threshold: float,
    m: int,
    n: int,
    k: int,
) -> float:
    if selection_mode == "loglik":
        return float(ll_sparse)

    support_df = _count_offdiag_nonzeros(a_sparse, threshold=support_threshold)
    # Free-parameter proxy: off-diagonal AR support + diagonal AR terms + transition/init terms + noise variance.
    df = support_df + (k * n) + (k * (k - 1)) + (k - 1) + 1
    bic_penalty = 0.5 * np.log(max(m, 2)) * df
    score = float(ll_sparse - selection_penalty * bic_penalty)
    if selection_mode == "bic":
        return score
    if selection_mode == "ebic":
        graph_dim = max(n * n * k, 2)
        ebic_extra = selection_gamma * np.log(graph_dim) * support_df
        return float(score - selection_penalty * ebic_extra)
    raise ValueError(f"Unknown selection_mode: {selection_mode}")


def _init_labels_strategy(
    x_prev: Array,
    x_next: Array,
    k: int,
    strategy: str,
    seed: int,
) -> NDArray[np.int64]:
    if strategy == "kmeans_full":
        feats = np.hstack([x_prev, x_next])
        labels = KMeans(n_clusters=k, random_state=seed, n_init=20).fit_predict(feats)
    elif strategy == "kmeans_delta":
        feats = np.hstack([x_next - x_prev, x_prev])
        labels = KMeans(n_clusters=k, random_state=seed, n_init=20).fit_predict(feats)
    elif strategy == "residual_split":
        a_global = fit_A_ridge(x_prev, x_next, ridge_lambda=1e-2)
        residual = x_next - x_prev @ a_global.T
        feats = np.hstack([residual, x_prev])
        labels = KMeans(n_clusters=k, random_state=seed, n_init=20).fit_predict(feats)
    elif strategy == "window_ar_cluster":
        m = x_prev.shape[0]
        window = max(40, min(100, m // 20))
        local_features = _local_ar_features(x_prev=x_prev, x_next=x_next, window=window)
        labels = KMeans(n_clusters=k, random_state=seed, n_init=20).fit_predict(local_features)
    elif strategy == "local_ar_gmm":
        m = x_prev.shape[0]
        window = max(60, min(180, m // 12))
        local_features = _local_ar_features(x_prev=x_prev, x_next=x_next, window=window)
        projected = _project_features(local_features, seed=seed)
        gmm = GaussianMixture(
            n_components=k,
            covariance_type="full",
            random_state=seed,
            n_init=5,
            reg_covar=1e-4,
        )
        labels = gmm.fit_predict(projected)
    elif strategy == "local_ar_gmm_sticky":
        m = x_prev.shape[0]
        window = max(60, min(220, m // 10))
        local_features = _local_ar_features(x_prev=x_prev, x_next=x_next, window=window)
        projected = _project_features(local_features, seed=seed)
        gmm = GaussianMixture(
            n_components=k,
            covariance_type="full",
            random_state=seed,
            n_init=5,
            reg_covar=1e-4,
        )
        post = gmm.fit(projected).predict_proba(projected)
        distance = -np.log(np.clip(post, 1e-8, 1.0))
        switch_penalty = max(0.5, 0.45 * np.log(max(m / max(k, 1), 2.0)))
        labels = _sticky_distance_decode(distance=distance, switch_penalty=switch_penalty)
    elif strategy == "residual_gmm_sticky":
        m = x_prev.shape[0]
        a_global = fit_A_ridge(x_prev, x_next, ridge_lambda=1e-2)
        residual = x_next - x_prev @ a_global.T
        feats = np.hstack([x_prev, x_next - x_prev, residual])
        projected = _project_features(feats, seed=seed)
        gmm = GaussianMixture(
            n_components=k,
            covariance_type="diag",
            random_state=seed,
            n_init=6,
            reg_covar=1e-4,
        )
        post = gmm.fit(projected).predict_proba(projected)
        distance = -np.log(np.clip(post, 1e-8, 1.0))
        switch_penalty = max(0.5, 0.55 * np.log(max(m / max(k, 1), 2.0)))
        labels = _sticky_distance_decode(distance=distance, switch_penalty=switch_penalty)
    elif strategy == "random_blocks":
        rng = np.random.default_rng(seed)
        labels = np.zeros(x_prev.shape[0], dtype=np.int64)
        current = int(rng.integers(low=0, high=k))
        switch_prob = 0.03
        for i in range(labels.size):
            if i > 0 and rng.random() < switch_prob:
                current = int(rng.integers(low=0, high=k))
            labels[i] = current
    elif strategy == "random":
        rng = np.random.default_rng(seed)
        labels = rng.integers(low=0, high=k, size=x_prev.shape[0], dtype=np.int64)
    else:
        raise ValueError(f"Unknown init strategy: {strategy}")
    return labels.astype(np.int64)


def fit_sparse_As_from_labels(
    x_prev: Array,
    x_next: Array,
    labels: NDArray[np.int64],
    k: int,
    lasso_alpha: float,
    seed: int,
    cv_complexity_limit: int = 2_000_000,
    alpha_scale: float = 0.35,
) -> list[Array]:
    n = x_prev.shape[1]
    a_global_sparse = recover_A_from_pairs_cv(
        x_prev=x_prev,
        x_next=x_next,
        seed=seed,
        cv_complexity_limit=cv_complexity_limit,
        alpha_scale=alpha_scale,
    )
    a_list: list[Array] = []
    for regime in range(k):
        idx = np.where(labels == regime)[0]
        if idx.size < max(4 * n, 80):
            a_list.append(a_global_sparse.copy())
        else:
            a_list.append(
                recover_A_from_pairs_cv(
                    x_prev=x_prev[idx],
                    x_next=x_next[idx],
                    seed=seed + 97 * (regime + 1),
                    cv_complexity_limit=cv_complexity_limit,
                    alpha_scale=alpha_scale,
                )
            )
    return a_list


def refit_on_support(
    x_prev: Array,
    x_next: Array,
    support_mask: NDArray[np.bool_],
    ridge_lambda: float = 1e-3,
) -> Array:
    n = x_prev.shape[1]
    a_hat = np.zeros((n, n), dtype=np.float64)
    for target in range(n):
        sel = np.where(support_mask[target])[0]
        if sel.size == 0:
            continue
        xs = x_prev[:, sel]
        ys = x_next[:, target]
        xtx = xs.T @ xs + ridge_lambda * np.eye(sel.size)
        xty = xs.T @ ys
        coef = np.linalg.solve(xtx, xty)
        a_hat[target, sel] = coef
    np.fill_diagonal(a_hat, np.maximum(np.diag(a_hat), 0.05))
    return a_hat


def fit_sparse_As_with_stability(
    x_prev: Array,
    x_next: Array,
    labels: NDArray[np.int64],
    k: int,
    seed: int,
    support_threshold: float,
    bootstrap_runs: int = 20,
    subsample_frac: float = 0.7,
    freq_threshold: float = 0.55,
    cv_complexity_limit: int = 2_000_000,
    alpha_scale: float = 0.35,
) -> list[Array]:
    n = x_prev.shape[1]
    rng = np.random.default_rng(seed)
    out: list[Array] = []

    for regime in range(k):
        idx = np.where(labels == regime)[0]
        if idx.size < max(5 * n, 120):
            # Too few samples for stable bootstrapping; fallback.
            out.append(
                recover_A_from_pairs_cv(
                    x_prev=x_prev[idx] if idx.size > 2 else x_prev,
                    x_next=x_next[idx] if idx.size > 2 else x_next,
                    seed=seed + 1000 + regime,
                    cv_complexity_limit=cv_complexity_limit,
                    alpha_scale=alpha_scale,
                )
            )
            continue

        m = idx.size
        b_size = max(int(subsample_frac * m), 4 * n)
        support_counts = np.zeros((n, n), dtype=np.float64)
        for b in range(bootstrap_runs):
            chosen = rng.choice(idx, size=b_size, replace=False)
            a_b = recover_A_from_pairs_cv(
                x_prev=x_prev[chosen],
                x_next=x_next[chosen],
                seed=seed + 10000 + regime * 503 + b,
                cv_complexity_limit=cv_complexity_limit,
                alpha_scale=alpha_scale,
            )
            support_counts += (np.abs(a_b) > support_threshold).astype(np.float64)

        support_freq = support_counts / bootstrap_runs
        support_mask = support_freq >= freq_threshold
        np.fill_diagonal(support_mask, True)

        a_refit = refit_on_support(
            x_prev=x_prev[idx],
            x_next=x_next[idx],
            support_mask=support_mask,
            ridge_lambda=1e-3,
        )
        out.append(a_refit)

    return out


def recover_switching_lds_hard(
    x: Array,
    k: int,
    seed: int,
    em_iterations: int,
    lasso_alpha: float,
) -> tuple[list[Array], NDArray[np.int64], Array, float, float]:
    x_prev = x[:-1]
    x_next = x[1:]
    n = x_prev.shape[1]
    labels = _init_labels_strategy(x_prev, x_next, k, strategy="kmeans_full", seed=seed)

    a_global = fit_A_ridge(x_prev, x_next, ridge_lambda=1e-2)
    a_list = [a_global.copy() for _ in range(k)]
    transition = estimate_transition_matrix(labels, k=k, smoothing=1.0)
    init = np.bincount(labels[:10], minlength=k).astype(np.float64) + 1.0
    init /= init.sum()
    sigma2 = max(float(np.mean((x_next - x_prev @ a_global.T) ** 2)), 1e-4)
    final_loglik = -np.inf

    for _ in range(em_iterations):
        for regime in range(k):
            idx = np.where(labels == regime)[0]
            if idx.size < max(4 * n, 80):
                a_list[regime] = a_global.copy()
            else:
                a_list[regime] = fit_A_ridge(
                    x_prev=x_prev[idx],
                    x_next=x_next[idx],
                    ridge_lambda=1e-2,
                )

        log_emission = compute_log_emission(x_prev, x_next, a_list, sigma2)
        _, _, final_loglik = forward_backward_hmm(log_emission, transition, init)
        labels_new = viterbi_decode(
            log_emission=log_emission,
            log_transition=np.log(transition + 1e-12),
            log_init=np.log(init + 1e-12),
        )
        transition = estimate_transition_matrix(labels_new, k=k, smoothing=1.0)
        init = np.bincount(labels_new[:10], minlength=k).astype(np.float64) + 1.0
        init /= init.sum()

        pred = np.zeros_like(x_next)
        for i in range(labels_new.size):
            pred[i] = x_prev[i] @ a_list[labels_new[i]].T
        sigma2 = max(float(np.mean((x_next - pred) ** 2)), 1e-4)

        if np.array_equal(labels_new, labels):
            labels = labels_new
            break
        labels = labels_new

    a_sparse = fit_sparse_As_from_labels(
        x_prev=x_prev,
        x_next=x_next,
        labels=labels,
        k=k,
        lasso_alpha=lasso_alpha,
        seed=seed + 13,
    )
    return a_sparse, labels, transition, sigma2, final_loglik


def recover_switching_lds_soft(
    x: Array,
    k: int,
    seed: int,
    em_iterations: int,
    restarts: int,
    ridge_lambda: float,
    lasso_alpha: float,
    sticky_kappa: float,
    temp_start: float,
    init_strategies: list[str] | None = None,
    sparse_cv_complexity_limit: int = 2_000_000,
    sparse_alpha_scale: float = 0.35,
    sparse_alpha_scales: list[float] | None = None,
    use_stability_refit: bool = False,
    support_threshold: float = 0.05,
    stability_bootstrap_runs: int = 12,
    stability_subsample_frac: float = 0.7,
    stability_freq_threshold: float = 0.55,
    selection_mode: str = "loglik",
    selection_penalty: float = 1.0,
    selection_gamma: float = 0.5,
    min_support_nnz: int = 1,
) -> tuple[list[Array], NDArray[np.int64], Array, float, float, str]:
    x_prev = x[:-1]
    x_next = x[1:]
    n = x_prev.shape[1]
    if init_strategies is None:
        strategies = [
            "kmeans_full",
            "kmeans_delta",
            "residual_split",
            "window_ar_cluster",
            "local_ar_gmm",
            "local_ar_gmm_sticky",
            "residual_gmm_sticky",
            "random_blocks",
            "random",
        ]
    else:
        strategies = list(init_strategies)
    if len(strategies) == 0:
        raise ValueError("init_strategies must be non-empty")
    if sparse_alpha_scales is None or len(sparse_alpha_scales) == 0:
        alpha_scales = [float(sparse_alpha_scale)]
    else:
        alpha_scales = [float(v) for v in sparse_alpha_scales if float(v) > 0]
        if len(alpha_scales) == 0:
            raise ValueError("sparse_alpha_scales must contain positive values")
    if selection_mode not in {"loglik", "bic", "ebic"}:
        raise ValueError("selection_mode must be one of: loglik, bic, ebic")
    if min_support_nnz < 0:
        raise ValueError("min_support_nnz must be non-negative")

    a_global = fit_A_ridge(x_prev, x_next, ridge_lambda=ridge_lambda)
    sigma2_global = max(float(np.mean((x_next - x_prev @ a_global.T) ** 2)), 1e-4)
    best: dict | None = None

    for restart in range(restarts):
        strategy = strategies[restart % len(strategies)]
        restart_alpha_scale = alpha_scales[restart % len(alpha_scales)]
        labels = _init_labels_strategy(
            x_prev=x_prev,
            x_next=x_next,
            k=k,
            strategy=strategy,
            seed=seed + 31 * restart,
        )
        transition = estimate_transition_matrix(labels, k=k, smoothing=1.0)
        init = np.bincount(labels[:10], minlength=k).astype(np.float64) + 1.0
        init /= init.sum()
        sigma2 = sigma2_global
        a_list = [a_global.copy() for _ in range(k)]
        prev_ll = -np.inf
        gamma = np.full((x_prev.shape[0], k), 1.0 / k)

        for iter_idx in range(em_iterations):
            temp = max(1.0, temp_start - (temp_start - 1.0) * (iter_idx / max(em_iterations - 1, 1)))
            log_emission = compute_log_emission(x_prev, x_next, a_list, sigma2) / temp
            gamma, xi_sum, ll = forward_backward_hmm(log_emission, transition, init)

            init = gamma[0] + 1e-6
            init /= init.sum()
            transition = xi_sum + 1e-3 + sticky_kappa * np.eye(k)
            transition /= transition.sum(axis=1, keepdims=True)

            for regime in range(k):
                a_list[regime] = fit_A_weighted_ridge(
                    x_prev=x_prev,
                    x_next=x_next,
                    weights=gamma[:, regime],
                    ridge_lambda=ridge_lambda,
                    fallback=a_global,
                )

            weighted_sq = 0.0
            for regime in range(k):
                residual = x_next - x_prev @ a_list[regime].T
                weighted_sq += float(
                    np.sum(gamma[:, regime][:, None] * (residual**2))
                )
            sigma2 = max(weighted_sq / (x_prev.shape[0] * n), 1e-4)

            if ll - prev_ll < 1e-5 and prev_ll > -np.inf:
                prev_ll = ll
                break
            prev_ll = ll

        final_log_emission = compute_log_emission(x_prev, x_next, a_list, sigma2)
        labels_vit = viterbi_decode(
            log_emission=final_log_emission,
            log_transition=np.log(transition + 1e-12),
            log_init=np.log(init + 1e-12),
        )
        if use_stability_refit:
            a_sparse = fit_sparse_As_with_stability(
                x_prev=x_prev,
                x_next=x_next,
                labels=labels_vit,
                k=k,
                seed=seed + 997 * (restart + 1),
                support_threshold=support_threshold,
                bootstrap_runs=stability_bootstrap_runs,
                subsample_frac=stability_subsample_frac,
                freq_threshold=stability_freq_threshold,
                cv_complexity_limit=sparse_cv_complexity_limit,
                alpha_scale=restart_alpha_scale,
            )
        else:
            a_sparse = fit_sparse_As_from_labels(
                x_prev=x_prev,
                x_next=x_next,
                labels=labels_vit,
                k=k,
                lasso_alpha=lasso_alpha,
                seed=seed + 997 * (restart + 1),
                cv_complexity_limit=sparse_cv_complexity_limit,
                alpha_scale=restart_alpha_scale,
            )
        support_nnz = _count_offdiag_nonzeros(a_sparse, threshold=support_threshold)
        if support_nnz == 0:
            # Degenerate all-zero support is usually a regularization artifact.
            rescue_scale = max(0.05, 0.55 * restart_alpha_scale)
            a_rescue = fit_sparse_As_from_labels(
                x_prev=x_prev,
                x_next=x_next,
                labels=labels_vit,
                k=k,
                lasso_alpha=lasso_alpha,
                seed=seed + 1997 * (restart + 1),
                cv_complexity_limit=sparse_cv_complexity_limit,
                alpha_scale=rescue_scale,
            )
            rescue_nnz = _count_offdiag_nonzeros(a_rescue, threshold=support_threshold)
            if rescue_nnz > support_nnz:
                a_sparse = a_rescue
                support_nnz = rescue_nnz
        sparse_log_emission = compute_log_emission(x_prev, x_next, a_sparse, sigma2)
        _, _, ll_sparse = forward_backward_hmm(sparse_log_emission, transition, init)
        selection_score = _candidate_selection_score(
            selection_mode=selection_mode,
            selection_penalty=selection_penalty,
            selection_gamma=selection_gamma,
            ll_sparse=float(ll_sparse),
            a_sparse=a_sparse,
            support_threshold=support_threshold,
            m=x_prev.shape[0],
            n=n,
            k=k,
        )
        if support_nnz < min_support_nnz:
            selection_score -= selection_penalty * 1e3 * (min_support_nnz - support_nnz)

        candidate = {
            "a_list": a_sparse,
            "labels": labels_vit,
            "transition": transition,
            "sigma2": sigma2,
            "loglik": ll_sparse,
            "strategy": strategy,
            "selection_score": selection_score,
            "support_nnz": support_nnz,
        }
        if best is None or candidate["selection_score"] > best["selection_score"]:
            best = candidate

    assert best is not None
    return (
        best["a_list"],
        best["labels"],
        best["transition"],
        float(best["sigma2"]),
        float(best["loglik"]),
        str(best["strategy"]),
    )


def recover_switching_lds_oracle(
    x: Array,
    z_true: NDArray[np.int64],
    k: int,
    lasso_alpha: float,
) -> tuple[list[Array], NDArray[np.int64], Array, float]:
    x_prev = x[:-1]
    x_next = x[1:]
    labels = z_true[1:].astype(np.int64)
    transition = estimate_transition_matrix(labels, k=k, smoothing=1.0)
    a_sparse = fit_sparse_As_from_labels(
        x_prev=x_prev,
        x_next=x_next,
        labels=labels,
        k=k,
        lasso_alpha=lasso_alpha,
        seed=17,
    )
    pred = np.zeros_like(x_next)
    for i in range(labels.size):
        pred[i] = x_prev[i] @ a_sparse[labels[i]].T
    sigma2 = max(float(np.mean((x_next - pred) ** 2)), 1e-4)
    return a_sparse, labels, transition, sigma2


def evaluate_switching_solution(
    a_true: list[Array],
    a_hat: list[Array],
    z_true_transitions: NDArray[np.int64],
    z_hat_transitions: NDArray[np.int64],
    support_threshold: float,
) -> dict:
    k = len(a_true)
    best = None
    for perm in permutations(range(k)):
        mapping = {est: true for est, true in enumerate(perm)}
        mapped_labels = np.array([mapping[z] for z in z_hat_transitions], dtype=np.int64)
        acc = float(np.mean(mapped_labels == z_true_transitions))

        f1s: list[float] = []
        for true_regime in range(k):
            est_regime = perm.index(true_regime)
            m = support_metrics(
                truth=a_true[true_regime],
                estimate=a_hat[est_regime],
                threshold=support_threshold,
                include_diagonal=False,
            )
            f1s.append(m.f1)
        mean_f1 = float(np.mean(f1s))
        score = (acc, mean_f1)
        if best is None or score > best["score"]:
            best = {
                "score": score,
                "perm": perm,
                "acc": acc,
                "mean_f1": mean_f1,
                "mapped_labels": mapped_labels,
                "f1s": f1s,
            }
    assert best is not None
    return best


def run_switching_lds(
    n: int,
    t: int,
    edge_prob: float,
    sigma: float,
    seed: int,
    out_dir: Path,
    support_threshold: float,
    obs_noise_sigma: float = 0.0,
    obs_noise_model: str = "gaussian",
    obs_noise_df: float = 3.0,
    outlier_prob: float = 0.02,
    outlier_scale: float = 6.0,
    stability_bootstrap_runs: int = 24,
    stability_subsample_frac: float = 0.75,
    stability_freq_threshold: float = 0.55,
) -> dict:
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(seed)
    k = 2

    a0 = make_sparse_stable_A(
        n=n,
        edge_prob=edge_prob,
        rng=rng,
        scale=0.35,
        target_radius=0.85,
    )
    a1 = make_sparse_stable_A(
        n=n,
        edge_prob=edge_prob,
        rng=rng,
        scale=0.35,
        target_radius=0.85,
    )
    for _ in range(100):
        support_diff = float(
            np.mean((np.abs(a0) > support_threshold) != (np.abs(a1) > support_threshold))
        )
        fro_ratio = float(
            np.linalg.norm(a0 - a1) / max(np.linalg.norm(a0), 1e-12)
        )
        if support_diff >= 0.18 and fro_ratio >= 0.70:
            break
        a1 = make_sparse_stable_A(
            n=n,
            edge_prob=edge_prob,
            rng=rng,
            scale=0.35,
            target_radius=0.85,
        )

    transition_true = np.array([[0.97, 0.03], [0.03, 0.97]], dtype=np.float64)
    init_true = np.array([0.5, 0.5], dtype=np.float64)
    burn_in = 200
    z_full = sample_markov_chain(
        t=t + burn_in,
        transition=transition_true,
        init_probs=init_true,
        rng=rng,
    )
    x_full = simulate_switching_lds(
        a_list=[a0, a1],
        z=z_full,
        sigma=sigma,
        rng=rng,
    )
    z_true = z_full[burn_in:]
    x = x_full[burn_in:]
    if obs_noise_sigma > 0:
        if obs_noise_model == "gaussian":
            noise = rng.normal(scale=obs_noise_sigma, size=x.shape)
        elif obs_noise_model == "student_t":
            if obs_noise_df <= 2.0:
                raise ValueError("obs_noise_df must be > 2 for finite-variance Student-t noise")
            raw = rng.standard_t(df=obs_noise_df, size=x.shape)
            # Normalize to unit variance, then scale to requested sigma.
            raw /= np.sqrt(obs_noise_df / (obs_noise_df - 2.0))
            noise = obs_noise_sigma * raw
        elif obs_noise_model == "contaminated":
            noise = rng.normal(scale=obs_noise_sigma, size=x.shape)
            mask = rng.random(size=x.shape) < outlier_prob
            if np.any(mask):
                noise[mask] += rng.normal(
                    scale=outlier_scale * obs_noise_sigma,
                    size=int(np.sum(mask)),
                )
        else:
            raise ValueError(f"Unknown obs_noise_model: {obs_noise_model}")
        y = x + noise
    else:
        y = x.copy()
    z_true_transitions = z_true[1:]

    hard_a, hard_z, hard_t, hard_sigma2, hard_ll = recover_switching_lds_hard(
        x=y,
        k=k,
        seed=seed + 77,
        em_iterations=14,
        lasso_alpha=0.01,
    )
    soft_a, soft_z, soft_t, soft_sigma2, soft_ll, soft_init = recover_switching_lds_soft(
        x=y,
        k=k,
        seed=seed + 181,
        em_iterations=35,
        restarts=12,
        ridge_lambda=1e-2,
        lasso_alpha=0.01,
        sticky_kappa=30.0,
        temp_start=2.5,
    )
    oracle_a, oracle_z, oracle_t, oracle_sigma2 = recover_switching_lds_oracle(
        x=y,
        z_true=z_true,
        k=k,
        lasso_alpha=0.01,
    )

    hard_a_stable = fit_sparse_As_with_stability(
        x_prev=y[:-1],
        x_next=y[1:],
        labels=hard_z,
        k=k,
        seed=seed + 3001,
        support_threshold=support_threshold,
        bootstrap_runs=stability_bootstrap_runs,
        subsample_frac=stability_subsample_frac,
        freq_threshold=stability_freq_threshold,
    )
    soft_a_stable = fit_sparse_As_with_stability(
        x_prev=y[:-1],
        x_next=y[1:],
        labels=soft_z,
        k=k,
        seed=seed + 4001,
        support_threshold=support_threshold,
        bootstrap_runs=stability_bootstrap_runs,
        subsample_frac=stability_subsample_frac,
        freq_threshold=stability_freq_threshold,
    )
    oracle_a_stable = fit_sparse_As_with_stability(
        x_prev=y[:-1],
        x_next=y[1:],
        labels=oracle_z,
        k=k,
        seed=seed + 5001,
        support_threshold=support_threshold,
        bootstrap_runs=stability_bootstrap_runs,
        subsample_frac=stability_subsample_frac,
        freq_threshold=stability_freq_threshold,
    )

    eval_hard = evaluate_switching_solution(
        a_true=[a0, a1],
        a_hat=hard_a,
        z_true_transitions=z_true_transitions,
        z_hat_transitions=hard_z,
        support_threshold=support_threshold,
    )
    eval_soft = evaluate_switching_solution(
        a_true=[a0, a1],
        a_hat=soft_a,
        z_true_transitions=z_true_transitions,
        z_hat_transitions=soft_z,
        support_threshold=support_threshold,
    )
    eval_oracle = evaluate_switching_solution(
        a_true=[a0, a1],
        a_hat=oracle_a,
        z_true_transitions=z_true_transitions,
        z_hat_transitions=oracle_z,
        support_threshold=support_threshold,
    )
    eval_hard_stable = evaluate_switching_solution(
        a_true=[a0, a1],
        a_hat=hard_a_stable,
        z_true_transitions=z_true_transitions,
        z_hat_transitions=hard_z,
        support_threshold=support_threshold,
    )
    eval_soft_stable = evaluate_switching_solution(
        a_true=[a0, a1],
        a_hat=soft_a_stable,
        z_true_transitions=z_true_transitions,
        z_hat_transitions=soft_z,
        support_threshold=support_threshold,
    )
    eval_oracle_stable = evaluate_switching_solution(
        a_true=[a0, a1],
        a_hat=oracle_a_stable,
        z_true_transitions=z_true_transitions,
        z_hat_transitions=oracle_z,
        support_threshold=support_threshold,
    )

    method_results = {
        "hard_em": {
            "regime_accuracy": eval_hard["acc"],
            "support_f1_mean": eval_hard["mean_f1"],
            "support_f1_regime0": eval_hard["f1s"][0],
            "support_f1_regime1": eval_hard["f1s"][1],
            "sigma2_hat": hard_sigma2,
            "loglik": hard_ll,
        },
        "hard_em_stability": {
            "regime_accuracy": eval_hard_stable["acc"],
            "support_f1_mean": eval_hard_stable["mean_f1"],
            "support_f1_regime0": eval_hard_stable["f1s"][0],
            "support_f1_regime1": eval_hard_stable["f1s"][1],
            "sigma2_hat": hard_sigma2,
            "loglik": hard_ll,
        },
        "soft_em_hmm": {
            "regime_accuracy": eval_soft["acc"],
            "support_f1_mean": eval_soft["mean_f1"],
            "support_f1_regime0": eval_soft["f1s"][0],
            "support_f1_regime1": eval_soft["f1s"][1],
            "sigma2_hat": soft_sigma2,
            "loglik": soft_ll,
            "best_init_strategy": soft_init,
        },
        "soft_em_hmm_stability": {
            "regime_accuracy": eval_soft_stable["acc"],
            "support_f1_mean": eval_soft_stable["mean_f1"],
            "support_f1_regime0": eval_soft_stable["f1s"][0],
            "support_f1_regime1": eval_soft_stable["f1s"][1],
            "sigma2_hat": soft_sigma2,
            "loglik": soft_ll,
            "best_init_strategy": soft_init,
        },
        "oracle_labels_ceiling": {
            "regime_accuracy": eval_oracle["acc"],
            "support_f1_mean": eval_oracle["mean_f1"],
            "support_f1_regime0": eval_oracle["f1s"][0],
            "support_f1_regime1": eval_oracle["f1s"][1],
            "sigma2_hat": oracle_sigma2,
        },
        "oracle_labels_ceiling_stability": {
            "regime_accuracy": eval_oracle_stable["acc"],
            "support_f1_mean": eval_oracle_stable["mean_f1"],
            "support_f1_regime0": eval_oracle_stable["f1s"][0],
            "support_f1_regime1": eval_oracle_stable["f1s"][1],
            "sigma2_hat": oracle_sigma2,
        },
    }

    # Select by data-fit criterion (not truth metrics): highest likelihood among non-oracle methods.
    candidate_map = {
        "hard_em": (eval_hard, hard_a, hard_t, hard_ll),
        "hard_em_stability": (eval_hard_stable, hard_a_stable, hard_t, hard_ll),
        "soft_em_hmm": (eval_soft, soft_a, soft_t, soft_ll),
        "soft_em_hmm_stability": (eval_soft_stable, soft_a_stable, soft_t, soft_ll),
    }
    selected_method = max(candidate_map, key=lambda m: candidate_map[m][3])
    selected_eval, selected_a, selected_t, _ = candidate_map[selected_method]

    perm = selected_eval["perm"]
    mapped_hat = [selected_a[perm.index(r)] for r in range(k)]

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "A_true_regime0.npy", a0)
    np.save(out_dir / "A_true_regime1.npy", a1)
    np.save(out_dir / "A_hat_regime0.npy", mapped_hat[0])
    np.save(out_dir / "A_hat_regime1.npy", mapped_hat[1])
    np.save(out_dir / "z_true.npy", z_true_transitions)
    np.save(out_dir / "z_hat.npy", selected_eval["mapped_labels"])
    np.save(out_dir / "transition_true.npy", transition_true)
    np.save(out_dir / "transition_hat.npy", selected_t)

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    vmax = max(np.max(np.abs(a0)), np.max(np.abs(a1)), np.max(np.abs(mapped_hat[0])), np.max(np.abs(mapped_hat[1])))
    axes[0, 0].imshow(a0, cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes[0, 0].set_title("True A (Regime 0)")
    axes[0, 1].imshow(mapped_hat[0], cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes[0, 1].set_title("Recovered A (Regime 0)")
    axes[1, 0].imshow(a1, cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes[1, 0].set_title("True A (Regime 1)")
    axes[1, 1].imshow(mapped_hat[1], cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes[1, 1].set_title("Recovered A (Regime 1)")
    for ax in axes.reshape(-1):
        ax.set_xlabel("Source")
        ax.set_ylabel("Target")
    plt.tight_layout()
    fig.savefig(out_dir / "A_regime_recovery.png", dpi=160)
    plt.close(fig)

    fig2, ax2 = plt.subplots(1, 1, figsize=(10, 2.5))
    ax2.plot(z_true_transitions, label="True regime", linewidth=1.4)
    ax2.plot(selected_eval["mapped_labels"], label="Recovered regime", linewidth=1.0, alpha=0.85)
    ax2.set_xlabel("Time index")
    ax2.set_ylabel("Regime")
    ax2.set_yticks([0, 1])
    ax2.legend(loc="upper right")
    plt.tight_layout()
    fig2.savefig(out_dir / "regime_sequence_recovery.png", dpi=160)
    plt.close(fig2)

    # One-step predictive MSE under selected decoded regime path.
    y_prev = y[:-1]
    y_next = y[1:]
    pred = np.zeros_like(y_next)
    mapped_labels = selected_eval["mapped_labels"]
    for idx in range(y_prev.shape[0]):
        pred[idx] = y_prev[idx] @ mapped_hat[mapped_labels[idx]].T
    state_estimation_mse = float(np.mean((y_next - pred) ** 2))

    return {
        "n": n,
        "t": t,
        "k": k,
        "edge_prob": edge_prob,
        "sigma": sigma,
        "obs_noise_sigma": obs_noise_sigma,
        "obs_noise_model": obs_noise_model,
        "support_threshold": support_threshold,
        "regime_contrast_fro_ratio": float(
            np.linalg.norm(a0 - a1) / max(np.linalg.norm(a0), 1e-12)
        ),
        "regime_support_diff_rate": float(
            np.mean((np.abs(a0) > support_threshold) != (np.abs(a1) > support_threshold))
        ),
        "selected_method": selected_method,
        "regime_accuracy": selected_eval["acc"],
        "support_f1_mean": selected_eval["mean_f1"],
        "support_f1_regime0": selected_eval["f1s"][0],
        "support_f1_regime1": selected_eval["f1s"][1],
        "state_estimation_mse": state_estimation_mse,
        "methods": method_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase0"))
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--t", type=int, default=1000)
    parser.add_argument("--sparsity", type=float, default=0.10)
    parser.add_argument("--sigma", type=float, default=0.5)
    parser.add_argument("--support-threshold", type=float, default=0.05)
    parser.add_argument("--switching-t", type=int, default=1400)
    parser.add_argument("--switching-n", type=int, default=10)
    parser.add_argument("--switching-obs-noise", type=float, default=0.15)
    args = parser.parse_args()

    glasso_dir = args.out_dir / "graphical_lasso"
    lds_dir = args.out_dir / "sparse_lds"
    switching_dir = args.out_dir / "switching_lds"

    glasso = run_graphical_lasso(
        n=args.n,
        t=args.t,
        edge_prob=args.sparsity,
        alpha_grid=(0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40),
        seed=args.seed,
        out_dir=glasso_dir,
        support_threshold=args.support_threshold,
    )
    lds = run_sparse_lds(
        n=args.n,
        t=args.t,
        edge_prob=args.sparsity,
        sigma=args.sigma,
        seed=args.seed + 101,
        out_dir=lds_dir,
        support_threshold=args.support_threshold,
    )
    switching = run_switching_lds(
        n=args.switching_n,
        t=args.switching_t,
        edge_prob=args.sparsity,
        sigma=args.sigma,
        seed=args.seed + 211,
        out_dir=switching_dir,
        support_threshold=args.support_threshold,
        obs_noise_sigma=args.switching_obs_noise,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "seed": args.seed,
        "graphical_lasso": glasso,
        "sparse_lds": lds,
        "switching_lds": switching,
    }
    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    print("Phase 0 baselines complete.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
