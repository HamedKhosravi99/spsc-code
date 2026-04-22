"""
Experiment 4 (journal.tex): Identification Condition Necessity.

Each probe-side identification condition is individually necessary. We
violate one at a time and measure the subspace-recovery error
    ||P_hat - P^*||_op
as m grows. Subspace error is the clean theory-validation signal because
downstream regret is confounded by the r-sqrt(T) exploitation term that
the paper already tests separately.

Fixed d=10, r=2, single segment, probe count swept.

Ablations:
  (a) Variance misspecification (prop:biased_measurement):
      lifted estimator uses hat sigma^2 = delta * sigma_eps^2,
      delta in {0.2, 0.5, 1, 2, 5, 10}.

  (b) State-noise coupling (prop:biased_cross_correlation):
      eps_t = eps_t^0 + eps_x * (e_1^T theta_t / ||theta_t||),
      eps_x in {0, 0.1, 0.5, 1, 2, 5}.

  (c) Restricted probe coverage (thm:restricted_span_minimax_regret):
      probes drawn from a d'-dim subspace of R^d,
      d' in {2, 4, 6, 8, 10}.
      m growing from 100 to 5000.

Predictions (thm:closed_dynamic_regret_general):
  (a), (b) degrade gracefully — subspace error still decays as 1/sqrt(m).
  (c) fundamental barrier — subspace error floors at Omega(1) for d'<d and
      does NOT decay with m.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core import (stiefel, make_segments, K_inv_gaussian, projector_error)


def estimate_subspace(d, r, m, sigma_eps, rng,
                      *, sigma2_used=None, eps_cross=0.0, V_probe=None):
    """Run m probes under specified ablation, return ||P_hat - P^*||_op."""
    if sigma2_used is None:
        sigma2_used = sigma_eps**2

    B = stiefel(d, r, rng)
    theta_seg = make_segments([B], [m], rng, rho=0.5, sigma_eta=1.0)

    if V_probe is not None:
        dp = V_probe.shape[1]
        Z = rng.standard_normal((m, dp))
        U_probes = Z @ V_probe.T
    else:
        U_probes = rng.standard_normal((m, d))

    # Vectorized observation generation
    signal = np.einsum('ij,ij->i', U_probes, theta_seg)
    raw_noise = sigma_eps * rng.standard_normal(m)
    if eps_cross != 0.0:
        norms = np.linalg.norm(theta_seg, axis=1) + 1e-12
        extra = eps_cross * theta_seg[:, 0] / norms
    else:
        extra = 0.0
    Y = signal + raw_noise + extra

    s = Y**2 - sigma2_used
    M_raw = (U_probes.T * s) @ U_probes / m
    M_hat = K_inv_gaussian(M_raw, d)
    M_hat = 0.5 * (M_hat + M_hat.T)
    eigvals, eigvecs = np.linalg.eigh(M_hat)
    U_hat = eigvecs[:, -r:]
    return projector_error(U_hat, B)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=20)
    ap.add_argument('--out', type=str,
                    default=os.path.join(HERE, '..', '..', 'figs',
                                         'journal_exp4_identification.png'))
    args = ap.parse_args()

    d = 10
    r = 2
    sigma_eps = 1.0
    m_values = [100, 200, 500, 1000, 2000, 5000]

    t_start = time.time()

    # (a) Variance misspec
    deltas = [0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
    err_a = np.zeros((len(deltas), len(m_values), args.seeds))
    print("[exp4a] variance misspec")
    for di, delta in enumerate(deltas):
        for mi, m in enumerate(m_values):
            for s in range(args.seeds):
                rng = np.random.default_rng(100 * di + 7 * mi + s)
                err_a[di, mi, s] = estimate_subspace(
                    d, r, m, sigma_eps, rng,
                    sigma2_used=delta * sigma_eps**2)
        print(f"  delta={delta}: err at m=5000 = {err_a[di, -1].mean():.3f}",
              flush=True)

    # (b) State-noise coupling
    eps_xs = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0]
    err_b = np.zeros((len(eps_xs), len(m_values), args.seeds))
    print("[exp4b] state-noise coupling")
    for ei, eps_x in enumerate(eps_xs):
        for mi, m in enumerate(m_values):
            for s in range(args.seeds):
                rng = np.random.default_rng(3000 + 100 * ei + 7 * mi + s)
                err_b[ei, mi, s] = estimate_subspace(
                    d, r, m, sigma_eps, rng, eps_cross=eps_x)
        print(f"  eps_x={eps_x}: err at m=5000 = {err_b[ei, -1].mean():.3f}",
              flush=True)

    # (c) Restricted probe coverage
    dps = [2, 4, 6, 8, 10]
    err_c = np.zeros((len(dps), len(m_values), args.seeds))
    print("[exp4c] restricted coverage")
    for ci, dp in enumerate(dps):
        for mi, m in enumerate(m_values):
            for s in range(args.seeds):
                rng = np.random.default_rng(7000 + 100 * ci + 7 * mi + s)
                rng_V = np.random.default_rng(9000 + s)
                if dp == d:
                    V = np.eye(d)
                else:
                    V = stiefel(d, dp, rng_V)
                err_c[ci, mi, s] = estimate_subspace(
                    d, r, m, sigma_eps, rng, V_probe=V)
        print(f"  d'={dp}: err at m=5000 = {err_c[ci, -1].mean():.3f}",
              flush=True)

    print(f"[exp4] total elapsed {time.time() - t_start:.1f}s")

    # ---- Plot: 3 panels, each showing error vs m for varying ablation level ----
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    # (a)
    colors_a = plt.cm.coolwarm(np.linspace(0, 1, len(deltas)))
    for di, delta in enumerate(deltas):
        mean = err_a[di].mean(axis=1)
        se = err_a[di].std(axis=1, ddof=1) / np.sqrt(args.seeds)
        axes[0].errorbar(m_values, mean, yerr=se, marker='o',
                         color=colors_a[di], label=f'δ={delta}',
                         capsize=2, linewidth=1.2)
    axes[0].set_xscale('log'); axes[0].set_yscale('log')
    axes[0].set_xlabel('probes $m$'); axes[0].set_ylabel(r'$\|\hat P - P^\star\|_{op}$')
    axes[0].set_title('(a) Variance misspec — graceful')
    axes[0].legend(fontsize=8, ncol=2); axes[0].grid(True, which='both', alpha=0.3)

    # (b)
    colors_b = plt.cm.coolwarm(np.linspace(0, 1, len(eps_xs)))
    for ei, eps_x in enumerate(eps_xs):
        mean = err_b[ei].mean(axis=1)
        se = err_b[ei].std(axis=1, ddof=1) / np.sqrt(args.seeds)
        axes[1].errorbar(m_values, mean, yerr=se, marker='o',
                         color=colors_b[ei], label=f'ε$_\\times$={eps_x}',
                         capsize=2, linewidth=1.2)
    axes[1].set_xscale('log'); axes[1].set_yscale('log')
    axes[1].set_xlabel('probes $m$'); axes[1].set_ylabel(r'$\|\hat P - P^\star\|_{op}$')
    axes[1].set_title('(b) State-noise coupling — graceful')
    axes[1].legend(fontsize=8, ncol=2); axes[1].grid(True, which='both', alpha=0.3)

    # (c)
    colors_c = plt.cm.viridis(np.linspace(0, 0.9, len(dps)))
    for ci, dp in enumerate(dps):
        mean = err_c[ci].mean(axis=1)
        se = err_c[ci].std(axis=1, ddof=1) / np.sqrt(args.seeds)
        axes[2].errorbar(m_values, mean, yerr=se, marker='o',
                         color=colors_c[ci], label=f"d'={dp}",
                         capsize=2, linewidth=1.2)
    axes[2].set_xscale('log'); axes[2].set_yscale('log')
    axes[2].set_xlabel('probes $m$'); axes[2].set_ylabel(r'$\|\hat P - P^\star\|_{op}$')
    axes[2].set_title("(c) Restricted coverage — floors at Ω(1)")
    axes[2].legend(fontsize=8); axes[2].grid(True, which='both', alpha=0.3)

    fig.suptitle(f'Identification-condition ablations  (d={d}, r={r})', y=1.02)
    fig.tight_layout()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches='tight')
    print(f"[exp4] saved {args.out}")


if __name__ == '__main__':
    main()
