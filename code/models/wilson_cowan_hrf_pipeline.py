#!/usr/bin/env python3
"""Phase 0 Steps 16-19: Wilson-Cowan + HRF + switching + pairwise recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
from numpy.typing import NDArray
from scipy.stats import gamma

from phase0_baselines import recover_A_from_pairs_cv, support_metrics

# Force a headless-safe backend for CI/terminal execution.
matplotlib.use("Agg")
import matplotlib.pyplot as plt


Array = NDArray[np.float64]


def sigmoid(x: Array, a: float = 1.2, theta: float = 2.5) -> Array:
    return 1.0 / (1.0 + np.exp(-a * (x - theta)))


def sigmoid_prime(x: Array, a: float = 1.2, theta: float = 2.5) -> Array:
    s = sigmoid(x, a=a, theta=theta)
    return a * s * (1.0 - s)


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


def make_sparse_coupling(
    n: int,
    edge_prob: float,
    rng: np.random.Generator,
    low: float = 0.06,
    high: float = 0.20,
) -> Array:
    mask = rng.random((n, n)) < edge_prob
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n, n))
    mags = rng.uniform(low, high, size=(n, n))
    c = mask * signs * mags
    np.fill_diagonal(c, 0.0)
    return c


def canonical_hrf(tr: float, duration_s: float = 32.0) -> Array:
    t = np.arange(0, duration_s, tr, dtype=np.float64)
    h = gamma.pdf(t, a=6) - 0.5 * gamma.pdf(t, a=12)
    h = h / np.sum(np.abs(h))
    return h


def convolve_hrf(signal: Array, hrf: Array) -> Array:
    t, n = signal.shape
    out = np.zeros_like(signal)
    for i in range(n):
        full = np.convolve(signal[:, i], hrf, mode="full")
        out[:, i] = full[:t]
    return out


def add_bold_artifacts(
    bold: Array,
    tr: float,
    rng: np.random.Generator,
    motion_spike_prob: float = 0.005,
    motion_scale: float = 1.5,
    physio_amp: float = 0.06,
    drift_amp: float = 0.08,
    obs_noise_sigma: float = 0.04,
) -> Array:
    t, n = bold.shape
    out = bold.copy()
    tt = np.arange(t, dtype=np.float64) * tr

    # Low-frequency drift.
    drift = drift_amp * np.sin(2.0 * np.pi * tt / (t * tr))
    out += drift[:, None]

    # Physiological oscillations.
    physio = physio_amp * (
        np.sin(2.0 * np.pi * 0.3 * tt) + 0.7 * np.sin(2.0 * np.pi * 0.1 * tt + 0.5)
    )
    out += physio[:, None]

    # Motion-like sparse spikes.
    spikes = rng.random((t, n)) < motion_spike_prob
    out += spikes * rng.normal(scale=motion_scale, size=(t, n))

    # Sensor noise.
    out += rng.normal(scale=obs_noise_sigma, size=(t, n))
    return out


def simulate_wilson_cowan_switching(
    n: int,
    t: int,
    dt: float,
    seed: int,
    edge_prob: float,
) -> tuple[Array, Array, NDArray[np.int64], list[Array], dict[str, float]]:
    rng = np.random.default_rng(seed)
    transition = np.array([[0.985, 0.015], [0.02, 0.98]], dtype=np.float64)
    init = np.array([0.5, 0.5], dtype=np.float64)
    burn_in = 250

    c0 = make_sparse_coupling(n=n, edge_prob=edge_prob, rng=rng, low=0.08, high=0.22)
    c1 = make_sparse_coupling(n=n, edge_prob=edge_prob, rng=rng, low=0.08, high=0.22)
    for _ in range(60):
        diff = np.mean((np.abs(c0) > 1e-9) != (np.abs(c1) > 1e-9))
        if diff >= 0.18:
            break
        c1 = make_sparse_coupling(n=n, edge_prob=edge_prob, rng=rng, low=0.08, high=0.22)

    z_full = sample_markov_chain(t=t + burn_in, transition=transition, init_probs=init, rng=rng)

    e = np.zeros((t + burn_in, n), dtype=np.float64)
    i = np.zeros((t + burn_in, n), dtype=np.float64)
    e[0] = rng.uniform(0.05, 0.2, size=n)
    i[0] = rng.uniform(0.05, 0.2, size=n)

    wc = {
        "w_ee": 12.0,
        "w_ei": 10.0,
        "w_ie": 10.0,
        "w_ii": 2.0,
        "p_base": 1.3,
        "q_base": 0.6,
        "tau_e": 1.0,
        "tau_i": 2.0,
        "coupling_gain": 1.0,
        "sigmoid_a": 1.2,
        "sigmoid_theta": 2.5,
        "process_noise": 0.02,
    }

    for t_idx in range(1, t + burn_in):
        reg = z_full[t_idx]
        coupling = c0 if reg == 0 else c1

        input_e = (
            wc["w_ee"] * e[t_idx - 1]
            - wc["w_ei"] * i[t_idx - 1]
            + wc["p_base"]
            + wc["coupling_gain"] * (coupling @ e[t_idx - 1])
        )
        input_i = wc["w_ie"] * e[t_idx - 1] - wc["w_ii"] * i[t_idx - 1] + wc["q_base"]

        de = (
            -e[t_idx - 1] + sigmoid(input_e, a=wc["sigmoid_a"], theta=wc["sigmoid_theta"])
        ) / wc["tau_e"]
        di = (
            -i[t_idx - 1] + sigmoid(input_i, a=wc["sigmoid_a"], theta=wc["sigmoid_theta"])
        ) / wc["tau_i"]

        e[t_idx] = e[t_idx - 1] + dt * de + rng.normal(scale=wc["process_noise"], size=n)
        i[t_idx] = i[t_idx - 1] + dt * di + rng.normal(scale=wc["process_noise"], size=n)

        e[t_idx] = np.clip(e[t_idx], 0.0, 1.0)
        i[t_idx] = np.clip(i[t_idx], 0.0, 1.0)

    return e[burn_in:], i[burn_in:], z_full[burn_in:], [c0, c1], wc


def recover_regime_pairwise_from_signal(
    signal: Array,
    z: NDArray[np.int64],
    targets: list[Array],
    support_threshold: float,
    seed: int,
) -> dict:
    x_prev = signal[:-1]
    x_next = signal[1:]
    labels = z[1:]
    n = signal.shape[1]

    metrics = {}
    a_hat_list: list[Array] = []
    for reg in [0, 1]:
        idx = np.where(labels == reg)[0]
        if idx.size < max(5 * n, 120):
            a_hat = recover_A_from_pairs_cv(x_prev=x_prev, x_next=x_next, seed=seed + 900 + reg)
        else:
            a_hat = recover_A_from_pairs_cv(
                x_prev=x_prev[idx],
                x_next=x_next[idx],
                seed=seed + 1000 + reg,
            )
        a_hat_list.append(a_hat)
        m = support_metrics(targets[reg], a_hat, threshold=support_threshold, include_diagonal=False)
        metrics[f"regime_{reg}"] = {
            "precision": m.precision,
            "recall": m.recall,
            "f1": m.f1,
            "tp": m.tp,
            "fp": m.fp,
            "fn": m.fn,
            "tn": m.tn,
            "samples_used": int(np.sum(labels == reg)),
        }

    metrics["support_f1_mean"] = float(
        0.5 * (metrics["regime_0"]["f1"] + metrics["regime_1"]["f1"])
    )
    return {"metrics": metrics, "a_hat_list": a_hat_list}


def compute_effective_jacobians(
    e: Array,
    i: Array,
    z: NDArray[np.int64],
    true_c: list[Array],
    dt: float,
    wc: dict[str, float],
) -> tuple[list[Array], dict[str, float]]:
    n = e.shape[1]
    x_prev = e[:-1]
    i_prev = i[:-1]
    labels = z[1:]
    identity = np.eye(n, dtype=np.float64)
    a_eff_regimes: list[Array] = []
    mean_sigmoid_prime: dict[str, float] = {}

    for reg in [0, 1]:
        idx = np.where(labels == reg)[0]
        mats: list[Array] = []
        sig_primes: list[float] = []
        for t_idx in idx:
            inp_e = (
                wc["w_ee"] * x_prev[t_idx]
                - wc["w_ei"] * i_prev[t_idx]
                + wc["p_base"]
                + wc["coupling_gain"] * (true_c[reg] @ x_prev[t_idx])
            )
            s_prime = sigmoid_prime(inp_e, a=wc["sigmoid_a"], theta=wc["sigmoid_theta"])
            sig_primes.append(float(np.mean(s_prime)))
            d = np.diag(s_prime)
            jac = identity + (dt / wc["tau_e"]) * (
                -identity + d @ (wc["w_ee"] * identity + wc["coupling_gain"] * true_c[reg])
            )
            mats.append(jac)
        a_eff = np.mean(mats, axis=0)
        a_eff_regimes.append(a_eff)
        mean_sigmoid_prime[f"regime_{reg}"] = float(np.mean(sig_primes))

    off_diag = np.ones((n, n), dtype=bool)
    np.fill_diagonal(off_diag, False)
    off_max = float(np.mean([np.max(np.abs(a_eff[off_diag])) for a_eff in a_eff_regimes]))
    off_mean = float(np.mean([np.mean(np.abs(a_eff[off_diag])) for a_eff in a_eff_regimes]))

    diagnostics = {
        "mean_sigmoid_prime_regime_0": mean_sigmoid_prime["regime_0"],
        "mean_sigmoid_prime_regime_1": mean_sigmoid_prime["regime_1"],
        "effective_offdiag_abs_max_mean": off_max,
        "effective_offdiag_abs_mean_mean": off_mean,
        # If this is tiny, recovering structural C from pairwise AR is effectively underpowered.
        "low_observability_flag": bool(off_max < 0.01),
    }
    return a_eff_regimes, diagnostics


def regime_support_hamming(true_c: list[Array]) -> float:
    m0 = np.abs(true_c[0]) > 1e-9
    m1 = np.abs(true_c[1]) > 1e-9
    return float(np.mean(m0 != m1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase0_wilson_cowan"))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--t", type=int, default=2400)
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--tr", type=float, default=0.8)
    parser.add_argument("--edge-prob", type=float, default=0.1)
    parser.add_argument("--support-threshold", type=float, default=0.05)
    parser.add_argument("--effective-threshold", type=float, default=5e-4)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    e, i, z, true_c, wc = simulate_wilson_cowan_switching(
        n=args.n,
        t=args.t,
        dt=args.dt,
        seed=args.seed,
        edge_prob=args.edge_prob,
    )
    hrf = canonical_hrf(tr=args.tr)
    bold_clean = convolve_hrf(e, hrf)
    rng = np.random.default_rng(args.seed + 111)
    bold_noisy = add_bold_artifacts(bold_clean, tr=args.tr, rng=rng)

    # Pairwise AR recovery, evaluated against structural coupling C.
    rec_neural_vs_c = recover_regime_pairwise_from_signal(
        signal=e,
        z=z,
        targets=true_c,
        support_threshold=args.support_threshold,
        seed=args.seed + 400,
    )
    rec_bold_vs_c = recover_regime_pairwise_from_signal(
        signal=bold_noisy,
        z=z,
        targets=true_c,
        support_threshold=args.support_threshold,
        seed=args.seed + 500,
    )

    # Effective local linearization of Wilson-Cowan dynamics for logic checks.
    a_eff, dyn_diag = compute_effective_jacobians(e=e, i=i, z=z, true_c=true_c, dt=args.dt, wc=wc)
    rec_neural_vs_aeff = recover_regime_pairwise_from_signal(
        signal=e,
        z=z,
        targets=a_eff,
        support_threshold=args.effective_threshold,
        seed=args.seed + 600,
    )
    rec_bold_vs_aeff = recover_regime_pairwise_from_signal(
        signal=bold_noisy,
        z=z,
        targets=a_eff,
        support_threshold=args.effective_threshold,
        seed=args.seed + 700,
    )

    np.save(args.out_dir / "E_timeseries.npy", e)
    np.save(args.out_dir / "I_timeseries.npy", i)
    np.save(args.out_dir / "z_regimes.npy", z)
    np.save(args.out_dir / "bold_clean.npy", bold_clean)
    np.save(args.out_dir / "bold_noisy.npy", bold_noisy)
    np.save(args.out_dir / "C_true_regime0.npy", true_c[0])
    np.save(args.out_dir / "C_true_regime1.npy", true_c[1])
    np.save(args.out_dir / "A_eff_regime0.npy", a_eff[0])
    np.save(args.out_dir / "A_eff_regime1.npy", a_eff[1])
    np.save(args.out_dir / "A_hat_neural_regime0.npy", rec_neural_vs_c["a_hat_list"][0])
    np.save(args.out_dir / "A_hat_neural_regime1.npy", rec_neural_vs_c["a_hat_list"][1])
    np.save(args.out_dir / "A_hat_bold_regime0.npy", rec_bold_vs_c["a_hat_list"][0])
    np.save(args.out_dir / "A_hat_bold_regime1.npy", rec_bold_vs_c["a_hat_list"][1])

    report = {
        "seed": args.seed,
        "n": args.n,
        "t": args.t,
        "dt": args.dt,
        "tr": args.tr,
        "edge_prob": args.edge_prob,
        "support_threshold_structural": args.support_threshold,
        "support_threshold_effective": args.effective_threshold,
        "regime_support_hamming": regime_support_hamming(true_c),
        "recovery_vs_structural_coupling": {
            "neural_pairwise": rec_neural_vs_c["metrics"],
            "bold_pairwise": rec_bold_vs_c["metrics"],
        },
        "recovery_vs_effective_linearization": {
            "neural_pairwise": rec_neural_vs_aeff["metrics"],
            "bold_pairwise": rec_bold_vs_aeff["metrics"],
        },
        "dynamics_diagnostics": dyn_diag,
        "claim_guardrail": (
            "Pairwise AR support on BOLD is a stress test only; low scores are expected when "
            "sigmoid derivatives are small and effective off-diagonal couplings are weak."
        ),
    }
    (args.out_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2))

    # Plots.
    fig, ax = plt.subplots(1, 1, figsize=(11, 2.2))
    ax.plot(z, lw=1.0)
    ax.set_title("True Regime Sequence")
    ax.set_xlabel("Time")
    ax.set_ylabel("Regime")
    ax.set_yticks([0, 1])
    fig.tight_layout()
    fig.savefig(args.out_dir / "regime_sequence.png", dpi=160)
    plt.close(fig)

    fig2, axes2 = plt.subplots(2, 1, figsize=(11, 5), sharex=True)
    axes2[0].plot(e[:800, :3], lw=0.8)
    axes2[0].set_title("Wilson-Cowan Excitatory Activity (first 3 nodes)")
    axes2[1].plot(bold_noisy[:800, :3], lw=0.8)
    axes2[1].set_title("BOLD-like (HRF + artifacts) (first 3 nodes)")
    axes2[1].set_xlabel("Time")
    fig2.tight_layout()
    fig2.savefig(args.out_dir / "timeseries_preview.png", dpi=160)
    plt.close(fig2)

    fig3, axes3 = plt.subplots(3, 2, figsize=(10, 10))
    vmax = max(
        np.max(np.abs(true_c[0])),
        np.max(np.abs(true_c[1])),
        np.max(np.abs(rec_neural_vs_c["a_hat_list"][0])),
        np.max(np.abs(rec_neural_vs_c["a_hat_list"][1])),
        np.max(np.abs(rec_bold_vs_c["a_hat_list"][0])),
        np.max(np.abs(rec_bold_vs_c["a_hat_list"][1])),
    )
    axes3[0, 0].imshow(true_c[0], cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes3[0, 0].set_title("True Coupling R0")
    axes3[0, 1].imshow(true_c[1], cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes3[0, 1].set_title("True Coupling R1")
    axes3[1, 0].imshow(rec_neural_vs_c["a_hat_list"][0], cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes3[1, 0].set_title("Recovered Pairwise from E (R0)")
    axes3[1, 1].imshow(rec_neural_vs_c["a_hat_list"][1], cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes3[1, 1].set_title("Recovered Pairwise from E (R1)")
    axes3[2, 0].imshow(rec_bold_vs_c["a_hat_list"][0], cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes3[2, 0].set_title("Recovered Pairwise from BOLD (R0)")
    axes3[2, 1].imshow(rec_bold_vs_c["a_hat_list"][1], cmap="coolwarm", vmin=-vmax, vmax=vmax)
    axes3[2, 1].set_title("Recovered Pairwise from BOLD (R1)")
    for ax in axes3.reshape(-1):
        ax.set_xlabel("Source")
        ax.set_ylabel("Target")
    fig3.tight_layout()
    fig3.savefig(args.out_dir / "recovery_heatmaps.png", dpi=160)
    plt.close(fig3)

    print("Wilson-Cowan/HRF pipeline complete.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
