"""
Experiment 1 (journal.tex): Minimax Subspace Recovery Rate.

Verifies Theorem thm:minimax_subspace_recovery:
    || P_hat - P^* ||_op = Theta(1 / sqrt(m))

Setup
-----
Single segment (K=1), d=20, r in {1, 3, 5}, m in {50, ..., 5000}.
For each (r, m) pair:
  * draw B^* ~ Stiefel(d, r)
  * simulate m rounds with theta_t = B^* w_t, w_t = 0.5 w_{t-1} + eta_t
  * collect m isotropic Gaussian probes, observations y_t
  * compute M_hat = K^{-1}(m^{-1} sum s_t u_t u_t^T), take top-r eigenspace
  * record error || P_hat - P^* ||_op

Runs 20 seeds, reports mean ± 1 SE, fits log-log slope.
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

from core import (stiefel, make_segments, draw_probes,
                  subspace_from_probes, projector_error)


def run_one(d, r, m, sigma_eps, seed, probe_kind='sphere', sigma_eta=2.0):
    rng = np.random.default_rng(seed)
    B = stiefel(d, r, rng)
    # Use sigma_eta=2 (so ||theta||^2 ~ 4*r / (1-0.25) = 5.3 r vs sigma_eps^2=1,
    # giving a finite-sample regime well above identifiability for d=20).
    theta = make_segments([B], [m], rng, rho=0.5, sigma_eta=sigma_eta)
    U_probes = draw_probes(m, d, rng, kind=probe_kind)
    Y_probes = np.einsum('ij,ij->i', U_probes, theta) + sigma_eps * rng.standard_normal(m)
    U_hat, _ = subspace_from_probes(U_probes, Y_probes, sigma_eps, d, r,
                                    probe_kind=probe_kind)
    return projector_error(U_hat, B)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=20)
    ap.add_argument('--out', type=str,
                    default=os.path.join(HERE, '..', '..', 'figs',
                                         'journal_exp1_minimax_recovery.png'))
    args = ap.parse_args()

    # Use d=10 so the identifiability threshold m >= r(2d-r) is reachable within
    # a tractable probe budget (r=5 gives threshold 75, well below our m tail).
    d = 10
    sigma_eps = 1.0
    r_values = [1, 3, 5]
    m_values = [50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]

    # results[r_idx, m_idx, seed] = error
    errors = np.full((len(r_values), len(m_values), args.seeds), np.nan)
    t0 = time.time()
    for ri, r in enumerate(r_values):
        for mi, m in enumerate(m_values):
            for s in range(args.seeds):
                errors[ri, mi, s] = run_one(d, r, m, sigma_eps, seed=1000*r + 7*m + s)
            mean = errors[ri, mi].mean()
            print(f"r={r}, m={m:5d}: mean err = {mean:.4f}", flush=True)
    print(f"[exp1] elapsed {time.time()-t0:.1f}s")

    # ---- Plot ----
    fig, ax = plt.subplots(figsize=(6, 4.5))
    colors = ['C0', 'C1', 'C2']
    slopes = []
    # Fit slope only on the asymptotic tail: drop m values below the
    # identifiability threshold m >= r*(2d-r) where subspace is non-trivial.
    for ri, r in enumerate(r_values):
        mean = errors[ri].mean(axis=1)
        se = errors[ri].std(axis=1, ddof=1) / np.sqrt(args.seeds)
        ax.errorbar(m_values, mean, yerr=se,
                    marker='o', color=colors[ri],
                    label=f'r = {r}', capsize=3)
        # Tail slope: fit on m >= max(5 r (2d-r), 1000) so we are clearly in
        # the asymptotic 1/sqrt(m) regime rather than the pre-identifiability
        # saturation regime.
        thresh = max(5 * r * (2 * d - r), 1000)
        tail_mask = np.array(m_values) >= thresh
        if tail_mask.sum() >= 3:
            log_m = np.log(np.array(m_values)[tail_mask])
            log_err = np.log(mean[tail_mask])
        else:
            log_m = np.log(np.array(m_values))
            log_err = np.log(mean)
        slope, intercept = np.polyfit(log_m, log_err, 1)
        slopes.append(slope)
        print(f"r={r}: tail-fit log-log slope = {slope:.3f} "
              f"(fit on m >= {thresh})")

    # Reference -1/2 slope
    m_ref = np.array([m_values[0], m_values[-1]])
    # Anchor at r=3 curve midpoint
    ref_level = errors[1].mean(axis=1)[len(m_values)//2]
    ref_m = m_values[len(m_values)//2]
    ref_curve = ref_level * np.sqrt(ref_m / m_ref)
    ax.plot(m_ref, ref_curve, 'k--', alpha=0.6, label=r'slope $-1/2$')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Number of probes $m$')
    ax.set_ylabel(r'$\|\hat P - P^\star\|_{op}$')
    title = (f'Minimax subspace recovery (d={d})\n'
             f'fitted slopes: '
             + ', '.join(f'r={r}: {s:.2f}' for r, s in zip(r_values, slopes)))
    ax.set_title(title)
    ax.grid(True, which='both', alpha=0.3)
    ax.legend()
    fig.tight_layout()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"[exp1] saved {args.out}")


if __name__ == '__main__':
    main()
