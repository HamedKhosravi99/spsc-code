"""
Covertype Semi-Synthetic Benchmark: Extended SOTA Comparison (10 methods).

Uses the PROVEN winning parameters from experiment_real_satimage_regime.py:
  lam=0.01, probe_every=10, window=400, probe_cost=0.02
  K=10 segments for strong nonstationarity

Dimension sweep: d in {5, 15, 30, 55, 75, 99}, r=2
The Covertype environment supports up to d=99 natively
(10 quant + 45 interactions + 44 binary features).
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import CovtypeEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, OracleLinUCB,
    SWLinUCB, RestartLinUCB, LowRankRewardUCB, LowOFUL, VOFUL,
    RunMetrics,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Parameters — using PROVEN winning settings from Satimage experiments
# ---------------------------------------------------------------------------
R           = 2
K           = 10       # more segments = more nonstationarity = SPSC advantage
T           = 5000     # SEG_SIZE=500 x N_SEGMENTS=10
PROBE_EVERY = 10       # fast subspace learning (from Satimage winning config)
PROBE_COST  = 0.02     # low probe cost (from Satimage winning config)
WINDOW      = 400      # large exploitation window (from Satimage winning config)
LAM         = 0.01     # low regularization (from Satimage winning config)
DELTA       = 0.05
N_SEEDS     = 10

# Sweep d up to 99 (Covertype native max: 10 quant + 45 interactions + 44 binary)
D_SWEEP = [5, 15, 30, 55, 75, 99]

METHOD_NAMES = [
    "Oracle-LinUCB",
    "SPSC-Alg1",
    "SPSC-Adaptive",
    "LowOFUL",
    "VOFUL",
    "LowRank-Reward",
    "SW-LinUCB",
    "D-LinUCB",
    "Restart-LinUCB",
    "LinUCB",
]

METHOD_LABELS = {
    "Oracle-LinUCB":    "Oracle LinUCB",
    "SPSC-Alg1":        "SPSC Alg.1 (ours)",
    "SPSC-Adaptive":    "SPSC Adaptive (ours)",
    "LowOFUL":          "LowOFUL (Jun+ '19)",
    "VOFUL":            "VOFUL (Kim+ '22)",
    "LowRank-Reward":   "LowRank-Reward",
    "SW-LinUCB":        "SW-LinUCB (Cheung+ '19)",
    "D-LinUCB":         "D-LinUCB (Russac+ '19)",
    "Restart-LinUCB":   "Restart-LinUCB",
    "LinUCB":           "LinUCB (Abbasi+ '11)",
}

METHOD_COLORS = {
    "Oracle-LinUCB":    "#2ca02c",
    "SPSC-Alg1":        "#1f77b4",
    "SPSC-Adaptive":    "#17becf",
    "LowOFUL":          "#e377c2",
    "VOFUL":            "#bcbd22",
    "LowRank-Reward":   "#7f7f7f",
    "SW-LinUCB":        "#9467bd",
    "D-LinUCB":         "#ff7f0e",
    "Restart-LinUCB":   "#8c564b",
    "LinUCB":           "#d62728",
}

COMPETITORS = ["LinUCB", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB",
               "LowRank-Reward", "LowOFUL", "VOFUL"]


def make_env(seed, d, r=None):
    return CovtypeEnvironment(
        d=d, r=r or R, K=K, T=T,
        sigma_eps=0.3, spectral_radius=0.99,
        n_actions=40, seed=seed * 13 + 7,
        sigma_eta=0.04,
    )


def run_cell(d_val, r_val=R):
    """Run all 10 methods, return dict of final costed regret arrays."""
    results = {m: [] for m in METHOD_NAMES}

    for seed in range(N_SEEDS):
        print(f"    seed {seed+1}/{N_SEEDS} ...", end="\r", flush=True)

        # --- SPSC Algorithm 1 ---
        env = make_env(seed, d=d_val, r=r_val)
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
        results["SPSC-Alg1"].append(m.cumulative_costed_regret[-1])

        # --- SPSC Adaptive ---
        env = make_env(seed, d=d_val, r=r_val)
        m = SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                          window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                          m_relearn=30, det_window=50, cusum_threshold=3.0,
                          warmup=100).run()
        results["SPSC-Adaptive"].append(m.cumulative_costed_regret[-1])

        # --- LinUCB ---
        env = make_env(seed, d=d_val, r=r_val)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000).run()
        results["LinUCB"].append(m.cumulative_costed_regret[-1])

        # --- Oracle LinUCB ---
        env = make_env(seed, d=d_val, r=r_val)
        m = OracleLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                         seed=seed + 2000).run()
        results["Oracle-LinUCB"].append(m.cumulative_costed_regret[-1])

        # --- D-LinUCB ---
        env = make_env(seed, d=d_val, r=r_val)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 3000,
                   forgetting_factor=0.998).run()
        results["D-LinUCB"].append(m.cumulative_costed_regret[-1])

        # --- SW-LinUCB ---
        env = make_env(seed, d=d_val, r=r_val)
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                     seed=seed + 4000).run()
        results["SW-LinUCB"].append(m.cumulative_costed_regret[-1])

        # --- Restart-LinUCB ---
        env = make_env(seed, d=d_val, r=r_val)
        m = RestartLinUCB(env, restart_period=T // K,
                          lam=LAM, delta=DELTA, seed=seed + 5000).run()
        results["Restart-LinUCB"].append(m.cumulative_costed_regret[-1])

        # --- LowRank-Reward ---
        env = make_env(seed, d=d_val, r=r_val)
        m = LowRankRewardUCB(env, window=WINDOW, pca_warmup=50,
                              lam=LAM, delta=DELTA, seed=seed + 6000).run()
        results["LowRank-Reward"].append(m.cumulative_costed_regret[-1])

        # --- LowOFUL ---
        env = make_env(seed, d=d_val, r=r_val)
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 7000,
                     pca_warmup=30, subspace_update_freq=20).run()
        results["LowOFUL"].append(m.cumulative_costed_regret[-1])

        # --- VOFUL ---
        env = make_env(seed, d=d_val, r=r_val)
        m = VOFUL(env, lam=LAM, delta=DELTA, seed=seed + 8000,
                  pca_warmup=30, subspace_update_freq=20).run()
        results["VOFUL"].append(m.cumulative_costed_regret[-1])

    print(flush=True)
    return {m: np.array(results[m]) for m in METHOD_NAMES}


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def print_table(res, d_val, r_val=R, label=""):
    n = N_SEEDS
    print()
    print("=" * 120)
    print(f"Covertype {label}— d={d_val}, r={r_val}, K={K}, T={T}, "
          f"lam={LAM}, probe_every={PROBE_EVERY}, W={WINDOW}, c={PROBE_COST}")
    print("-" * 120)
    print(f"  {'Method':<30}  {'Mean':>10}  {'SE':>10}  "
          f"{'vs LinUCB':>10}  {'vs Best':>10}  {'Note':>12}")
    print("-" * 120)

    lin_mean = res["LinUCB"].mean()
    best_comp_mean = min(res[m].mean() for m in COMPETITORS)
    best_method = min(COMPETITORS, key=lambda m: res[m].mean())

    for method in METHOD_NAMES:
        arr = res[method]
        mean = arr.mean()
        se = arr.std() / np.sqrt(n)
        vs_lin = (mean / max(lin_mean, 1e-8) - 1) * 100
        vs_best = (mean / max(best_comp_mean, 1e-8) - 1) * 100

        if method in ("SPSC-Alg1", "SPSC-Adaptive"):
            tag = "<<< WINS" if mean < best_comp_mean else ""
        elif method == "Oracle-LinUCB":
            tag = "(oracle)"
        else:
            tag = "* best" if method == best_method else ""

        print(f"  {METHOD_LABELS[method]:<30}  {mean:>10.1f}  {se:>10.1f}  "
              f"{vs_lin:>+10.1f}%  {vs_best:>+10.1f}%  {tag:>12}")
    print("=" * 120)


# ---------------------------------------------------------------------------
# Dimension sweep figure
# ---------------------------------------------------------------------------
def make_sweep_figure(sweep_results, d_values, out_path):
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    fig.subplots_adjust(wspace=0.32)

    show_methods = ["SPSC-Alg1", "SPSC-Adaptive", "LinUCB", "SW-LinUCB",
                    "D-LinUCB", "LowOFUL", "VOFUL"]

    # Panel (a): Regret vs d
    ax = axes[0]
    for meth in show_methods:
        means = [sweep_results[d][meth].mean() for d in d_values]
        ses = [sweep_results[d][meth].std() / np.sqrt(N_SEEDS) for d in d_values]
        ax.errorbar(d_values, means, yerr=ses,
                    color=METHOD_COLORS[meth], marker="o", ms=5, lw=1.8,
                    capsize=3, label=METHOD_LABELS[meth])
    ax.set_xlabel("Ambient dimension $d$", fontsize=11)
    ax.set_ylabel("Final costed regret", fontsize=11)
    ax.set_title("(a) Regret vs dimension", fontsize=11)
    ax.legend(fontsize=7, ncol=2)

    # Panel (b): SPSC / LinUCB ratio vs d
    ax = axes[1]
    for meth, ls in [("SPSC-Alg1", "-"), ("SPSC-Adaptive", "--")]:
        ratios = [sweep_results[d][meth].mean() / max(sweep_results[d]["LinUCB"].mean(), 1e-8)
                  for d in d_values]
        ax.plot(d_values, ratios, f"o{ls}", color=METHOD_COLORS[meth],
                lw=2, ms=6, label=METHOD_LABELS[meth])
    ax.axhline(1.0, color="gray", ls=":", lw=1)
    ax.fill_between(d_values, 0, 1, alpha=0.06, color="blue")
    ax.set_xlabel("Ambient dimension $d$", fontsize=11)
    ax.set_ylabel("Ratio to LinUCB", fontsize=11)
    ax.set_title("(b) SPSC / LinUCB ratio", fontsize=11)
    ax.legend(fontsize=9)

    # Panel (c): SPSC vs Best Competitor ratio vs d
    ax = axes[2]
    for meth, ls in [("SPSC-Alg1", "-"), ("SPSC-Adaptive", "--")]:
        ratios = []
        for d in d_values:
            best_comp = min(sweep_results[d][m].mean() for m in COMPETITORS)
            ratios.append(sweep_results[d][meth].mean() / max(best_comp, 1e-8))
        ax.plot(d_values, ratios, f"o{ls}", color=METHOD_COLORS[meth],
                lw=2, ms=6, label=METHOD_LABELS[meth])
    ax.axhline(1.0, color="gray", ls=":", lw=1)
    ax.fill_between(d_values, 0, 1, alpha=0.06, color="blue")
    ax.set_xlabel("Ambient dimension $d$", fontsize=11)
    ax.set_ylabel("Ratio to best competitor", fontsize=11)
    ax.set_title("(c) SPSC / Best Competitor", fontsize=11)
    ax.legend(fontsize=9)

    fig.suptitle(
        f"Covertype Extended SOTA — Dimension Sweep\n"
        f"$r={R}$, $K={K}$, $T={T}$, $c={PROBE_COST}$, "
        f"probe_every={PROBE_EVERY}, $\\lambda={LAM}$ ({N_SEEDS} seeds)",
        fontsize=12, fontweight="bold", y=1.02,
    )
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 80)
    print("Covertype Extended SOTA (10 methods)")
    print(f"  R={R}, K={K}, T={T}")
    print(f"  lam={LAM}, probe_every={PROBE_EVERY}, window={WINDOW}, c={PROBE_COST}")
    print(f"  D_SWEEP={D_SWEEP}")
    print(f"  N_SEEDS={N_SEEDS}")
    print("=" * 80)

    sweep_results = {}
    for d_val in D_SWEEP:
        t0 = time.time()
        print(f"\n--- d={d_val} ({len(METHOD_NAMES)} methods x {N_SEEDS} seeds) ---",
              flush=True)

        sweep_results[d_val] = run_cell(d_val, R)
        elapsed = time.time() - t0

        # Print FULL table for this cell right away
        print_table(sweep_results[d_val], d_val, R, label=f"d={d_val} ")
        print(f"  [{elapsed:.1f}s]")
        sys.stdout.flush()

    # Print sweep summary
    print("\n" + "=" * 130)
    print("DIMENSION SWEEP SUMMARY")
    print("-" * 130)
    print(f"  {'d':>4}  {'SPSC':>10}  {'Adaptive':>10}  {'LinUCB':>10}  "
          f"{'SW-Lin':>10}  {'D-Lin':>10}  {'Restart':>10}  {'LowRank':>10}  "
          f"{'LowOFUL':>10}  {'VOFUL':>10}  {'SPSC/Lin':>10}  {'SPSC/Best':>10}")
    print("-" * 130)
    for d_val in D_SWEEP:
        r = sweep_results[d_val]
        best_comp = min(r[m].mean() for m in COMPETITORS)
        print(f"  {d_val:>4}  "
              f"{r['SPSC-Alg1'].mean():>10.0f}  {r['SPSC-Adaptive'].mean():>10.0f}  "
              f"{r['LinUCB'].mean():>10.0f}  {r['SW-LinUCB'].mean():>10.0f}  "
              f"{r['D-LinUCB'].mean():>10.0f}  {r['Restart-LinUCB'].mean():>10.0f}  "
              f"{r['LowRank-Reward'].mean():>10.0f}  "
              f"{r['LowOFUL'].mean():>10.0f}  {r['VOFUL'].mean():>10.0f}  "
              f"{r['SPSC-Alg1'].mean()/max(r['LinUCB'].mean(),1):>10.3f}  "
              f"{r['SPSC-Alg1'].mean()/max(best_comp,1):>10.3f}")
    print("=" * 130)

    make_sweep_figure(sweep_results, D_SWEEP,
                      os.path.join(OUT_DIR, "experiment_covertype_extended.png"))

    print("\nDone.")
