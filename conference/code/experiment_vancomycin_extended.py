"""
Vancomycin Clinical Dosing Benchmark: Extended SOTA Comparison.

Mirrors the Warfarin extended-SOTA benchmark, swapping the drug-specific
environment.  The dosing protocol is the AUC-targeted Cockcroft-Gault
population-PK formula (Rybak et al., 2020 ASHP/IDSA consensus).

Methods compared:
  - SPSC (Algorithm 1)
  - SPSC-Adaptive (Algorithm 4 — no oracle segment boundaries)
  - LowOFUL  (Jun+ '19)
  - VOFUL    (Kim+ '22)
  - LowRank-Reward
  - SW-LinUCB, D-LinUCB, Restart-LinUCB, LinUCB
  - Oracle-LinUCB

d=93, K=8, T=5000, r in {1, 2, 3, 5, 10}
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import VancomycinEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, OracleLinUCB,
    SWLinUCB, DLinUCB, OracleResetLinUCB,
    LowRankRewardUCB, LowOFUL, VOFUL,
    RunMetrics,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Parameters — IDENTICAL to experiment_warfarin_extended.py
# ---------------------------------------------------------------------------
D           = 93
K           = 8
T           = 5000
N_ACTIONS   = 40
SIGMA_EPS   = 0.3
PROBE_EVERY = 10
PROBE_COST  = 0.1
WINDOW      = 200
LAM         = 1.0
DELTA       = 0.05
N_SEEDS     = 10

R_VALUES    = [1, 2, 3, 5, 10]

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


def make_env(seed, r):
    return VancomycinEnvironment(
        d=D, r=r, K=K, T=T, n_actions=N_ACTIONS,
        sigma_eps=SIGMA_EPS, seed=seed * 13 + 7,
    )


def run_cell(r):
    """Run all 10 methods for one rank value."""
    results = {m: [] for m in METHOD_NAMES}

    for seed in range(N_SEEDS):
        print(f"    seed {seed+1}/{N_SEEDS}", end="\r", flush=True)

        env = make_env(seed, r)
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
        results["SPSC-Alg1"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, r)
        m = SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                          window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                          m_relearn=30, det_window=50, cusum_threshold=3.0,
                          warmup=100).run()
        results["SPSC-Adaptive"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, r)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000).run()
        results["LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, r)
        m = OracleLinUCB(env, window=10000, lam=LAM, delta=DELTA,
                         seed=seed + 2000).run()
        results["Oracle-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, r)
        m = DLinUCB(env, gamma=0.995, lam=LAM, delta=DELTA,
                    seed=seed + 3000).run()
        results["D-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, r)
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                     seed=seed + 4000).run()
        results["SW-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, r)
        m = OracleResetLinUCB(env, lam=LAM, delta=DELTA,
                              seed=seed + 5000).run()
        results["Restart-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, r)
        m = LowRankRewardUCB(env, window=WINDOW, pca_warmup=50,
                             lam=LAM, delta=DELTA, seed=seed + 6000).run()
        results["LowRank-Reward"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, r)
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 7000,
                    pca_warmup=30, subspace_update_freq=20).run()
        results["LowOFUL"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, r)
        m = VOFUL(env, lam=LAM, delta=DELTA, seed=seed + 8000,
                  pca_warmup=30, subspace_update_freq=20).run()
        results["VOFUL"].append(m.cumulative_control_regret[-1])

    print(flush=True)
    return {m: np.array(results[m]) for m in METHOD_NAMES}


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def print_table(res, r):
    n = N_SEEDS
    lin_mean = res["LinUCB"].mean()
    best_comp_mean = min(res[m].mean() for m in COMPETITORS)
    best_method = min(COMPETITORS, key=lambda m: res[m].mean())

    print()
    print("=" * 120)
    print(f"  Vancomycin d={D}, r={r}, K={K}, T={T}  ({n} seeds)")
    print("-" * 120)
    print(f"  {'Method':<30}  {'Mean':>10}  {'SE':>10}  "
          f"{'vs LinUCB':>10}  {'vs Best':>10}  {'Note':>12}")
    print("-" * 120)

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
# Figure
# ---------------------------------------------------------------------------
def make_figure(all_results, out_path):
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    fig.subplots_adjust(wspace=0.32)

    show_methods = ["SPSC-Alg1", "SPSC-Adaptive", "LinUCB", "SW-LinUCB",
                    "D-LinUCB", "Restart-LinUCB", "LowOFUL", "VOFUL"]

    r_vals_used = [r for r in R_VALUES if r in all_results]

    # Panel (a): Regret vs r
    ax = axes[0]
    for meth in show_methods:
        means = [all_results[r][meth].mean() for r in r_vals_used]
        ses = [all_results[r][meth].std() / np.sqrt(N_SEEDS) for r in r_vals_used]
        ax.errorbar(r_vals_used, means, yerr=ses,
                    color=METHOD_COLORS[meth], marker="o", ms=5, lw=1.8,
                    capsize=3, label=METHOD_LABELS[meth])
    ax.set_xlabel("Latent rank $r$", fontsize=11)
    ax.set_ylabel("Control regret", fontsize=11)
    ax.set_title(f"(a) Regret vs rank  ($d={D}$)", fontsize=11)
    ax.legend(fontsize=6, ncol=2)
    ax.set_xticks(r_vals_used)

    # Panel (b): SPSC / LinUCB ratio vs r
    ax = axes[1]
    for meth, ls in [("SPSC-Alg1", "-"), ("SPSC-Adaptive", "--")]:
        ratios = [all_results[r][meth].mean() / max(all_results[r]["LinUCB"].mean(), 1e-8)
                  for r in r_vals_used]
        ax.plot(r_vals_used, ratios, f"o{ls}", color=METHOD_COLORS[meth],
                lw=2, ms=6, label=METHOD_LABELS[meth])
    ax.axhline(1.0, color="gray", ls=":", lw=1)
    ax.fill_between(r_vals_used, 0, 1, alpha=0.06, color="blue")
    ax.set_xlabel("Latent rank $r$", fontsize=11)
    ax.set_ylabel("Ratio to LinUCB", fontsize=11)
    ax.set_title("(b) SPSC / LinUCB ratio", fontsize=11)
    ax.legend(fontsize=9)
    ax.set_xticks(r_vals_used)

    # Panel (c): Bar chart for best r
    ax = axes[2]
    best_r = min(r_vals_used,
                 key=lambda r: all_results[r]["SPSC-Alg1"].mean() /
                               max(all_results[r]["LinUCB"].mean(), 1e-8))
    res = all_results[best_r]
    means = [res[m].mean() for m in METHOD_NAMES]
    ses = [res[m].std() / np.sqrt(N_SEEDS) for m in METHOD_NAMES]
    colors = [METHOD_COLORS[m] for m in METHOD_NAMES]

    order = np.argsort(means)
    y = np.arange(len(METHOD_NAMES))
    ax.barh(y, [means[i] for i in order],
            xerr=[ses[i] for i in order],
            color=[colors[i] for i in order],
            capsize=3, height=0.7, edgecolor="black", linewidth=0.3)
    ax.set_yticks(y)
    ax.set_yticklabels([METHOD_LABELS[METHOD_NAMES[i]].split("(")[0].strip()
                        for i in order], fontsize=8)
    ax.set_xlabel("Control regret", fontsize=10)
    ax.set_title(f"(c) Best config: $r={best_r}$", fontsize=11)

    fig.suptitle(
        f"Vancomycin Extended SOTA — $d={D}$, $K={K}$, $T={T}$\n"
        f"probe_every={PROBE_EVERY}, $\\lambda={LAM}$  ({N_SEEDS} seeds)",
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
    print("Vancomycin Extended SOTA (10 methods)")
    print(f"  d={D}, K={K}, T={T}")
    print(f"  r = {R_VALUES}")
    print(f"  lam={LAM}, probe_every={PROBE_EVERY}, window={WINDOW}, c={PROBE_COST}")
    print(f"  N_SEEDS={N_SEEDS}")
    print("=" * 80)

    all_results = {}

    for r in R_VALUES:
        t0 = time.time()
        print(f"\n--- r={r} ({len(METHOD_NAMES)} methods x {N_SEEDS} seeds) ---")

        res = run_cell(r)
        elapsed = time.time() - t0
        all_results[r] = res

        spsc_m = res["SPSC-Alg1"].mean()
        adapt_m = res["SPSC-Adaptive"].mean()
        lin_m = res["LinUCB"].mean()
        winner = "SPSC" if spsc_m < lin_m else "LinUCB"

        print(f"  DONE in {elapsed:.1f}s")
        print(f"    SPSC={spsc_m:.0f}  Adaptive={adapt_m:.0f}  Lin={lin_m:.0f}")
        print(f"    SPSC/Lin={spsc_m/max(lin_m,1):.3f}  [{winner}]")

        print_table(res, r)

    # Summary
    print("\n" + "=" * 80)
    print("Vancomycin SPSC/LinUCB ratio summary:")
    for r in R_VALUES:
        if r not in all_results:
            continue
        res = all_results[r]
        spsc_m = res["SPSC-Alg1"].mean()
        adapt_m = res["SPSC-Adaptive"].mean()
        lin_m = res["LinUCB"].mean()
        best_comp = min(res[m].mean() for m in COMPETITORS)
        marker_s = "*" if spsc_m < lin_m else " "
        marker_a = "*" if adapt_m < lin_m else " "
        print(f"  r={r:>2}: SPSC/Lin={spsc_m/max(lin_m,1):.3f}{marker_s}  "
              f"Adapt/Lin={adapt_m/max(lin_m,1):.3f}{marker_a}  "
              f"SPSC/Best={spsc_m/max(best_comp,1):.3f}")
    print("=" * 80)

    make_figure(all_results,
                os.path.join(OUT_DIR, "experiment_vancomycin_extended.png"))
    print("\nDone.")
