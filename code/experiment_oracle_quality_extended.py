"""
Oracle-quality sweep for the appendix L `When the adaptive variant wins`
figure (`fig:adaptive`).

Re-runs the K_oracle ablation at extended K_oracle range and higher
seed count to make the "Alg.1 degrades, Adaptive flat" claim land
clearly with publication-quality error bars.

Setup (matches the original sweep2 in
`/Users/hkhosravi7/Downloads/source/code/experiment_synthetic_comparison.py`,
with extended K_oracle range and 20 seeds):

  - True environment: piecewise low-rank LDS with K_real = 5 segments,
    d = 60, r = 5, T = 5000.
  - SPSC-Alg.1 is fed K_oracle  evenly-spaced segment boundaries (ranging
    from the truth K_oracle = K_real = 5 up to K_oracle = 200, i.e.,
    40x more boundaries than truth -- almost all are false alarms).
    Alg.1 resets at every fed boundary, so it pays per-segment burn-in
    each time.
  - SPSC-Adaptive ignores the oracle and uses its CUSUM detector on
    the clean (untouched) environment.
  - LinUCB is run on the clean environment as a baseline reference.

Outputs:
  - JSON: `code/results/experiment_oracle_quality.json`  (per-seed data)
  - Figure: `figures/experiment_oracle_quality.png`
            (single-panel high-DPI plot, paper-ready)

Usage:
    cd code/
    python3 experiment_oracle_quality_extended.py
"""

import os
import sys
import json
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from environments import LowRankLDSEnvironment
from algorithm import SPSC_Algorithm1, SPSC_Adaptive, LinUCB


# =========================================================================
# Parameters (matched to the original experiment_synthetic_comparison.py;
# only K_ORACLE_SWEEP and N_SEEDS extended.)
# =========================================================================
T              = 5000
K_REAL         = 5            # true number of subspace shifts
D              = 60
R              = 5
SIGMA_EPS      = 0.3
SPEC_RAD       = 0.99
SIGMA_ETA      = 0.04
N_ACTIONS      = 40
PROBE_EVERY    = 50
PROBE_COST     = 0.1
WINDOW         = 400
LAM            = 0.01
DELTA          = 0.05
FEATURE_DECAY  = 1.5
N_SEEDS        = 20

K_ORACLE_SWEEP = [5, 10, 20, 40, 80, 150, 200]


HERE      = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(HERE, "results", "experiment_oracle_quality.json")
FIG_PATH  = os.path.join(os.path.dirname(HERE), "figures",
                         "experiment_oracle_quality.png")


# -------------------------------------------------------------------------
# Environment helpers
# -------------------------------------------------------------------------
def make_env(seed):
    """Construct the true environment (always K_REAL segments)."""
    return LowRankLDSEnvironment(
        d=D, r=R, K=K_REAL, T=T,
        sigma_eps=SIGMA_EPS, spectral_radius=SPEC_RAD,
        n_actions=N_ACTIONS, sigma_eta=SIGMA_ETA, seed=seed * 100,
        piecewise_constant=True, feature_decay=FEATURE_DECAY,
    )


def add_false_boundaries(env, K_oracle):
    """Inject K_oracle evenly-spaced 'oracle' boundaries (only K_REAL of
    them are real; the rest are false alarms). Used only for Alg.1's env."""
    if K_oracle == K_REAL:
        return
    real_seg_len   = T // K_REAL
    oracle_seg_len = T // K_oracle
    new_seg_of = np.minimum(
        np.arange(T) // oracle_seg_len, K_oracle - 1
    ).astype(int)
    new_tau = np.array([i * oracle_seg_len for i in range(K_oracle)])
    new_B_list = []
    for k in range(K_oracle):
        t_mid  = new_tau[k] + oracle_seg_len // 2
        real_k = min(t_mid // real_seg_len, K_REAL - 1)
        new_B_list.append(env.B_list[real_k])
    env.seg_of  = new_seg_of
    env.tau     = new_tau
    env.K       = K_oracle
    env.B_list  = new_B_list


def run_one(K_oracle, seed):
    """Run the three methods at one (K_oracle, seed); return final-regret tuple."""
    # SPSC Alg.1 sees K_oracle (possibly false-alarm-inflated) boundaries
    env_a1 = make_env(seed)
    add_false_boundaries(env_a1, K_oracle)
    a1 = SPSC_Algorithm1(
        env_a1, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
        window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
        normalize_gamma_by_d=True,
    ).run()

    # SPSC-Adaptive: clean env, ignores oracle, detects via CUSUM
    env_ad = make_env(seed)
    ad = SPSC_Adaptive(
        env_ad, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
        window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
        m_relearn=30, det_window=50, cusum_threshold=3.0,
        warmup=100,
    ).run()

    # LinUCB: clean env, baseline reference (oracle-insensitive)
    env_li = make_env(seed)
    li = LinUCB(env_li, lam=LAM, delta=DELTA, seed=seed + 1000).run()

    return (
        a1.cumulative_costed_regret[-1],
        ad.cumulative_costed_regret[-1],
        li.cumulative_costed_regret[-1],
    )


# -------------------------------------------------------------------------
# Plotting
# -------------------------------------------------------------------------
def make_figure(results):
    plt.rcParams.update({
        "figure.dpi":         300,
        "savefig.dpi":        300,
        "font.family":        "serif",
        "font.size":          14,
        "axes.labelsize":     16,
        "axes.titlesize":     17,
        "axes.linewidth":     1.4,
        "xtick.labelsize":    13,
        "ytick.labelsize":    13,
        "xtick.major.width":  1.2,
        "ytick.major.width":  1.2,
        "xtick.major.size":   5,
        "ytick.major.size":   5,
        "legend.fontsize":    13,
        "legend.frameon":     True,
        "legend.framealpha":  0.95,
        "legend.edgecolor":   "0.3",
        "lines.linewidth":    2.6,
        "lines.markersize":   10,
        "lines.markeredgewidth": 1.4,
        "axes.grid":          True,
        "grid.alpha":         0.30,
        "grid.linestyle":     "--",
        "grid.linewidth":     0.7,
        "axes.axisbelow":     True,
    })

    fig, ax = plt.subplots(figsize=(10.0, 6.5))

    style = {
        "SPSC-Alg1":     ("#1f4e79", "o",  "-",  "SPSC Alg. 1"),
        "SPSC-Adaptive": ("#c0392b", "s",  "-",  "SPSC-Adaptive"),
        "LinUCB":        ("#555555", "^",  "--", "LinUCB"),
    }

    K_vals = K_ORACLE_SWEEP
    for method, (color, marker, ls, label) in style.items():
        means, ses = [], []
        for K in K_vals:
            vals = np.array(results[f"K_oracle={K}"][method])
            means.append(vals.mean())
            ses.append(vals.std(ddof=1) / np.sqrt(len(vals)))
        means = np.array(means)
        ses   = np.array(ses)
        ax.errorbar(
            K_vals, means, yerr=ses,
            color=color, marker=marker, linestyle=ls, label=label,
            capsize=4, capthick=1.4, elinewidth=1.4,
            markeredgecolor="black",
        )

    # Mark the true K_real
    ax.axvline(
        K_REAL, color="#27ae60", linestyle=":", linewidth=2.4, alpha=0.85,
        label=rf"True $K_{{\rm real}} = {K_REAL}$",
    )

    ax.set_xlabel(r"Oracle-supplied number of segments $K_{\rm oracle}$ "
                  r"(log scale)")
    ax.set_ylabel("Final cumulative costed regret")
    ax.set_xscale("log")
    ax.set_xticks(K_vals)
    ax.set_xticklabels([str(K) for K in K_vals])
    ax.legend(loc="upper left", framealpha=0.93)

    plt.tight_layout()
    os.makedirs(os.path.dirname(FIG_PATH), exist_ok=True)
    plt.savefig(FIG_PATH, bbox_inches="tight", dpi=300, facecolor="white")
    print(f"Saved figure to {FIG_PATH}")


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------
def main():
    print("=" * 80)
    print("Oracle-quality sweep (extended) — appendix L 'fig:adaptive'")
    print(f"  T={T}, K_real={K_REAL}, d={D}, r={R}")
    print(f"  K_oracle sweep: {K_ORACLE_SWEEP}")
    print(f"  N_SEEDS = {N_SEEDS}")
    print("=" * 80)
    print(f"{'K_oracle':>10}  {'Alg.1':>10}  {'Adapt':>10}  "
          f"{'LinUCB':>10}  {'Alg1/Adp':>10}  {'time':>8}")
    print("-" * 80)
    sys.stdout.flush()

    results = {}
    grand_t0 = time.time()
    for K_oracle in K_ORACLE_SWEEP:
        a1s, ads, lis = [], [], []
        t0 = time.time()
        for seed in range(N_SEEDS):
            a1, ad, li = run_one(K_oracle, seed)
            a1s.append(a1)
            ads.append(ad)
            lis.append(li)
        elapsed = time.time() - t0

        results[f"K_oracle={K_oracle}"] = {
            "SPSC-Alg1":     a1s,
            "SPSC-Adaptive": ads,
            "LinUCB":        lis,
        }

        a1m = float(np.mean(a1s))
        adm = float(np.mean(ads))
        lim = float(np.mean(lis))
        print(f"{K_oracle:>10d}  {a1m:>10.1f}  {adm:>10.1f}  "
              f"{lim:>10.1f}  {a1m/adm:>10.3f}  {elapsed:>7.1f}s")
        sys.stdout.flush()

    print("-" * 80)
    print(f"Total runtime: {(time.time() - grand_t0)/60:.1f} min")

    # ------------------------------------------------------------------
    # Save JSON
    # ------------------------------------------------------------------
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    with open(JSON_PATH, "w") as f:
        json.dump({
            "config": {
                "T": T, "K_REAL": K_REAL, "D": D, "R": R,
                "SIGMA_EPS": SIGMA_EPS, "SPEC_RAD": SPEC_RAD,
                "SIGMA_ETA": SIGMA_ETA, "N_ACTIONS": N_ACTIONS,
                "PROBE_EVERY": PROBE_EVERY, "PROBE_COST": PROBE_COST,
                "WINDOW": WINDOW, "LAM": LAM, "DELTA": DELTA,
                "FEATURE_DECAY": FEATURE_DECAY, "N_SEEDS": N_SEEDS,
                "K_ORACLE_SWEEP": K_ORACLE_SWEEP,
            },
            "results": results,
        }, f, indent=2)
    print(f"Saved JSON to {JSON_PATH}")

    # ------------------------------------------------------------------
    # Generate the figure from the freshly computed results
    # ------------------------------------------------------------------
    make_figure(results)


if __name__ == "__main__":
    main()
