"""
Experiment 5 (journal.tex): Optimal Probe Allocation.

Verifies Theorems thm:optimal_allocation and thm:regret_allocation:
    m_k^* \\propto ell_k^{2/3}   minimizes the probe-plus-subspace penalty

Setup
-----
d = 10, r = 2, T = 10000, c = 1, K = 4 with heterogeneous lengths
(ell_1, ell_2, ell_3, ell_4) = (500, 1500, 3000, 5000).

Primary metric: the theoretical dominant penalty term
    R_proxy(m_1,...,m_K) = c * sum_k m_k  +  sum_k ell_k * ||P_hat_k - P_k^*||_op
which captures both probe cost and subspace-mismatch-induced exploitation
regret. Secondary metric: full bandit dynamic regret.

Sweep total budget m in {100, 200, 400, 800, 1600}, compare:
  (i)   uniform      m_k = m / K
  (ii)  proportional m_k \\propto ell_k
  (iii) optimal      m_k \\propto ell_k^{2/3}   (Thm regret_allocation)
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

from core import (stiefel, make_segments, K_inv_gaussian, projector_error,
                  run_segment_projected)


def allocate(total_m, seg_lengths, mode):
    K = len(seg_lengths)
    ell = np.asarray(seg_lengths, dtype=float)
    if mode == 'uniform':
        weights = np.ones(K)
    elif mode == 'proportional':
        weights = ell
    elif mode == 'optimal':
        weights = ell ** (2.0 / 3.0)
    else:
        raise ValueError(mode)
    w = weights / weights.sum()
    m_k = np.round(total_m * w).astype(int)
    m_k = np.maximum(m_k, 2)
    return m_k.tolist()


def run_one(seg_lengths, m_k_list, d, r, sigma_eps, c, seed):
    """
    For each segment, probe m_k rounds, estimate subspace, record
    ||P_hat_k - P_k^*||_op. Return:
        proxy_regret = c * sum m_k + sum ell_k * subspace_err_k
    """
    rng = np.random.default_rng(seed)
    K = len(seg_lengths)
    B_list = [stiefel(d, r, rng) for _ in range(K)]
    theta_all = make_segments(B_list, seg_lengths, rng,
                              rho=0.5, sigma_eta=1.0)

    proxy = c * float(sum(m_k_list))
    t0 = 0
    for k, (L, m_k) in enumerate(zip(seg_lengths, m_k_list)):
        theta_seg = theta_all[t0:t0 + L]
        m_used = min(m_k, L - 2)
        U_probes = rng.standard_normal((m_used, d))
        signal = np.einsum('ij,ij->i', U_probes, theta_seg[:m_used])
        Y = signal + sigma_eps * rng.standard_normal(m_used)
        s = Y**2 - sigma_eps**2
        M_raw = (U_probes.T * s) @ U_probes / m_used
        M_hat = 0.5 * (K_inv_gaussian(M_raw, d)
                       + K_inv_gaussian(M_raw, d).T)
        eigvals, eigvecs = np.linalg.eigh(M_hat)
        U_hat = eigvecs[:, -r:]
        sub_err = projector_error(U_hat, B_list[k])
        proxy += L * sub_err
        t0 += L
    return proxy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=20)
    ap.add_argument('--out', type=str,
                    default=os.path.join(HERE, '..', '..', 'figs',
                                         'journal_exp5_allocation.png'))
    args = ap.parse_args()

    d = 10
    r = 2
    T = 10_000
    c = 1.0
    sigma_eps = 1.0
    seg_lengths = [500, 1500, 3000, 5000]
    assert sum(seg_lengths) == T
    m_totals = [100, 200, 400, 800, 1600, 3200]
    modes = ['uniform', 'proportional', 'optimal']

    proxy = np.full((len(modes), len(m_totals), args.seeds), np.nan)
    t_start = time.time()
    for mi, mode in enumerate(modes):
        for ti, total_m in enumerate(m_totals):
            alloc = allocate(total_m, seg_lengths, mode)
            for s in range(args.seeds):
                proxy[mi, ti, s] = run_one(
                    seg_lengths, alloc, d, r, sigma_eps, c, seed=s)
            print(f"{mode:12s}  m={total_m:4d}  alloc={alloc}  "
                  f"proxy={proxy[mi, ti].mean():.1f}", flush=True)
    print(f"[exp5] elapsed {time.time() - t_start:.1f}s")

    # ---- Plot ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    colors = {'uniform': 'C0', 'proportional': 'C1', 'optimal': 'C2'}
    for mi, mode in enumerate(modes):
        mean = proxy[mi].mean(axis=1)
        se = proxy[mi].std(axis=1, ddof=1) / np.sqrt(args.seeds)
        ax1.errorbar(m_totals, mean, yerr=se, marker='o',
                     color=colors[mode], label=mode,
                     capsize=3, linewidth=1.5)
    ax1.set_xlabel('Total probe budget $m$')
    ax1.set_ylabel(r'$R_{\mathrm{proxy}} = c\sum m_k + \sum \ell_k\|\hat P_k - P_k^\star\|$')
    ax1.set_xscale('log'); ax1.set_yscale('log')
    ax1.set_title(f'Probe-cost + subspace-mismatch proxy  '
                  f'($T={T}$, segs {tuple(seg_lengths)})')
    ax1.grid(True, which='both', alpha=0.3); ax1.legend()

    # Ratio plot
    opt = proxy[modes.index('optimal')].mean(axis=1)
    for mi, mode in enumerate(modes):
        if mode == 'optimal':
            continue
        mean = proxy[mi].mean(axis=1)
        ax2.plot(m_totals, (mean - opt) / opt * 100.0,
                 marker='o', color=colors[mode],
                 label=f'{mode} vs optimal', linewidth=1.5)
    ax2.axhline(0, color='k', linestyle=':', alpha=0.6)
    ax2.set_xlabel('Total probe budget $m$')
    ax2.set_ylabel('% regret excess over optimal allocation')
    ax2.set_xscale('log')
    ax2.set_title('Suboptimality of alternative allocations')
    ax2.grid(True, which='both', alpha=0.3); ax2.legend()

    fig.tight_layout()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"[exp5] saved {args.out}")


if __name__ == '__main__':
    main()
