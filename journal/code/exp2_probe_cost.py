"""
Experiment 2 (journal.tex): Probe-Cost Scaling.

Verifies Theorems thm:closed_dynamic_regret and thm:probe_rate_lb:
    DynReg_T^(c) ~ alpha r sqrt(T) + beta c^{1/3} T^{2/3}

Setup
-----
d = 10, r = 2, K = 4 equal-length segments.
T in {1000, 2000, 5000, 10000, 20000}, c in {0.01, 0.1, 1.0, 10.0}.

Per segment k we use the theoretically optimal probe count
    m_k^* = (gamma * ell_k / (2 c))^{2/3}
(Thm regret_allocation) with gamma = 1, run probes, estimate subspace, and
record the probe-cost + subspace-mismatch penalty
    R_probe(T, c) = c * sum m_k^* + sum ell_k * ||P_hat_k - P_k^*||_op.

This is the term in the dynamic-regret decomposition that depends on c —
the separate r * sqrt(T) exploitation term is validated in Experiment 3 and
does not depend on c. Measuring R_probe isolates the predicted
c^{1/3} T^{2/3} scaling from the within-segment drift regret that would
otherwise dominate in a finite-T bandit simulation.
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


def optimal_m(ell: int, c: float, gamma: float = 1.0) -> int:
    m_star = (gamma * ell / (2.0 * c)) ** (2.0 / 3.0)
    return max(2, min(ell - 1, int(round(m_star))))


def run_one(T, c, d, r, K, sigma_eps, seed, gamma=1.0):
    rng = np.random.default_rng(seed)
    base = T // K
    seg_lengths = [base] * K
    seg_lengths[-1] += T - sum(seg_lengths)
    B_list = [stiefel(d, r, rng) for _ in range(K)]
    theta = make_segments(B_list, seg_lengths, rng, rho=0.5, sigma_eta=1.0)

    R_probe = 0.0
    t0 = 0
    for k, L in enumerate(seg_lengths):
        theta_seg = theta[t0:t0 + L]
        m_k = optimal_m(L, c, gamma)
        # Probes
        U_probes = rng.standard_normal((m_k, d))
        signal = np.einsum('ij,ij->i', U_probes, theta_seg[:m_k])
        Y = signal + sigma_eps * rng.standard_normal(m_k)
        s = Y**2 - sigma_eps**2
        M_raw = (U_probes.T * s) @ U_probes / m_k
        M_hat = K_inv_gaussian(M_raw, d)
        M_hat = 0.5 * (M_hat + M_hat.T)
        _, eigvecs = np.linalg.eigh(M_hat)
        U_hat = eigvecs[:, -r:]
        err = projector_error(U_hat, B_list[k])
        # Probe-cost + subspace-mismatch contribution to DynReg
        R_probe += c * m_k + L * err
        t0 += L
    return R_probe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=20)
    ap.add_argument('--out', type=str,
                    default=os.path.join(HERE, '..', '..', 'figs',
                                         'journal_exp2_probe_cost.png'))
    args = ap.parse_args()

    d = 10
    r = 2
    K = 4
    sigma_eps = 1.0
    T_values = [1000, 2000, 5000, 10000, 20000]
    c_values = [0.01, 0.1, 1.0, 10.0]

    regret = np.full((len(c_values), len(T_values), args.seeds), np.nan)
    t_start = time.time()
    for ci, c in enumerate(c_values):
        for ti, T in enumerate(T_values):
            for s in range(args.seeds):
                regret[ci, ti, s] = run_one(
                    T, c, d, r, K, sigma_eps,
                    seed=10_000 * ci + 31 * ti + s)
            mean = regret[ci, ti].mean()
            print(f"c={c}, T={T:5d}: mean R_probe = {mean:.2f}", flush=True)
    print(f"[exp2] elapsed {time.time()-t_start:.1f}s")

    # ---- Plot ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    colors = ['C0', 'C1', 'C2', 'C3']
    slopes = []
    for ci, c in enumerate(c_values):
        mean = regret[ci].mean(axis=1)
        se = regret[ci].std(axis=1, ddof=1) / np.sqrt(args.seeds)
        ax1.errorbar(T_values, mean, yerr=se, marker='o', color=colors[ci],
                     label=f'c = {c}', capsize=3)
        slope, _ = np.polyfit(np.log(T_values), np.log(mean), 1)
        slopes.append(slope)

    # Reference T^{2/3}
    T_ref = np.array([T_values[0], T_values[-1]])
    level = regret[-1].mean(axis=1)[0]
    ax1.plot(T_ref, level * (T_ref / T_values[0])**(2/3),
             'k--', alpha=0.5, label=r'$T^{2/3}$ reference')
    ax1.set_xscale('log'); ax1.set_yscale('log')
    ax1.set_xlabel('Horizon $T$')
    ax1.set_ylabel(r'$R_{\mathrm{probe}}(T,c)$')
    ax1.set_title(
        'Probe-cost + subspace-mismatch penalty\n'
        f'slopes: ' + ', '.join(f'c={c}: {s:.2f}'
                                 for c, s in zip(c_values, slopes)))
    ax1.grid(True, which='both', alpha=0.3); ax1.legend()

    # c-scaling at fixed T: should be c^{1/3}
    T_fixed_idx = -1  # T = 20000
    T_fixed = T_values[T_fixed_idx]
    means_c = regret[:, T_fixed_idx, :].mean(axis=1)
    ses_c = regret[:, T_fixed_idx, :].std(axis=1, ddof=1) / np.sqrt(args.seeds)
    ax2.errorbar(c_values, means_c, yerr=ses_c, marker='o', capsize=3,
                 label=f'empirical  (T={T_fixed})')
    c_arr = np.array(c_values)
    c_slope, _ = np.polyfit(np.log(c_arr), np.log(means_c), 1)
    ref_level = means_c[0] * (c_arr / c_arr[0])**(1/3)
    ax2.plot(c_arr, ref_level, 'k--', alpha=0.5,
             label=r'$c^{1/3}$ reference')
    ax2.set_xscale('log'); ax2.set_yscale('log')
    ax2.set_xlabel('Probe cost $c$')
    ax2.set_ylabel(r'$R_{\mathrm{probe}}$')
    ax2.set_title(f'Fitted c-slope: {c_slope:.2f}  (predicted $1/3$)')
    ax2.grid(True, which='both', alpha=0.3); ax2.legend()

    fig.tight_layout()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"[exp2] saved {args.out}")


if __name__ == '__main__':
    main()
