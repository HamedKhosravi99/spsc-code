"""
NeurIPS Main Experiment: Comprehensive SOTA Comparison

Compares SPSC (Algorithm 1 + Adaptive Algorithm 4) against:
  - Full-dimensional baselines: LinUCB, SW-LinUCB, D-LinUCB, Restart-LinUCB
  - Stationary low-rank baselines: LowOFUL, VOFUL
  - Oracle: OracleLinUCB (performance ceiling)
  - ETC: Explore-then-Commit LowRank

Three experiment blocks:
  (A) Synthetic phase-transition: d in {10,20,40,60,80}, r in {1,3,5,10}
  (B) Synthetic SOTA benchmark:  d=40, r=3, T=10000 — head-to-head comparison
  (C) Algorithm 4 vs Algorithm 1: adaptive vs oracle boundaries

Outputs
-------
  experiment_neurips_main.png  — multi-panel composite figure
  Console table with all numbers
"""

import os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

from environments import LowRankLDSEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, OracleLinUCB,
    SWLinUCB, DLinUCB, RestartLinUCB, OracleResetLinUCB,
    LowOFUL, VOFUL, ETCLowRank, RunMetrics,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
np.set_printoptions(precision=1)


# =====================================================================
# Global parameters
# =====================================================================

N_SEEDS    = 10
T_DEFAULT  = 10000
K_DEFAULT  = 4
SIGMA_EPS  = 0.3
N_ACTIONS  = 80
PROBE_EVERY = 20
PROBE_COST  = 0.1
WINDOW      = 150
LAM         = 1.0
DELTA       = 0.05


# =====================================================================
# Helpers
# =====================================================================

def make_env(d, r, T=T_DEFAULT, K=K_DEFAULT, seed=42):
    return LowRankLDSEnvironment(
        d=d, r=r, K=K, T=T, sigma_eps=SIGMA_EPS,
        n_actions=N_ACTIONS, seed=seed,
    )


def run_algo(algo_cls, env, seed, **kwargs):
    """Run a single algorithm instance on a fresh copy of env."""
    return algo_cls(env, seed=seed, **kwargs).run()


def agg_final(runs, attr="cumulative_costed_regret"):
    """Get final value of cumulative metric: mean and SE."""
    vals = np.array([getattr(r, attr)[-1] for r in runs])
    return vals.mean(), vals.std() / np.sqrt(len(vals))


def agg_curves(runs, attr="cumulative_costed_regret"):
    """Get mean curve and SE band."""
    data = np.stack([getattr(r, attr) for r in runs])
    return data.mean(axis=0), data.std(axis=0) / np.sqrt(len(runs))


# =====================================================================
# (A) Synthetic phase-transition grid
# =====================================================================

def run_phase_grid():
    """
    Run SPSC Alg1 vs LinUCB across (d, r) grid.
    Returns dict: (d, r) -> (spsc_mean, linucb_mean, oracle_mean)
    """
    d_vals = [10, 20, 40, 60, 80]
    r_vals = [1, 3, 5, 10]

    results = {}
    total = sum(1 for d in d_vals for r in r_vals if r < d)
    done = 0

    for d in d_vals:
        for r in r_vals:
            if r >= d:
                continue
            done += 1
            print(f"  Phase grid [{done}/{total}] d={d}, r={r} ...", flush=True)

            spsc_runs, lin_runs, orac_runs = [], [], []
            for seed in range(N_SEEDS):
                env = make_env(d, r, T=T_DEFAULT, seed=seed * 100)
                spsc_runs.append(
                    SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                                    window=WINDOW, lam=LAM, delta=DELTA, seed=seed).run()
                )
                env = make_env(d, r, T=T_DEFAULT, seed=seed * 100)
                lin_runs.append(LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000).run())

                env = make_env(d, r, T=T_DEFAULT, seed=seed * 100)
                orac_runs.append(
                    OracleLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                                 seed=seed + 2000).run()
                )

            sm, _ = agg_final(spsc_runs)
            lm, _ = agg_final(lin_runs)
            om, _ = agg_final(orac_runs)
            results[(d, r)] = (sm, lm, om)
            print(f"    SPSC={sm:.0f}  LinUCB={lm:.0f}  Oracle={om:.0f}  "
                  f"ratio={sm/lm:.3f}")

    return results


# =====================================================================
# (B) Head-to-head SOTA comparison
# =====================================================================

ALGO_CONFIGS = {
    "SPSC-Alg1": dict(
        cls=SPSC_Algorithm1,
        kw=dict(probe_every=PROBE_EVERY, probe_cost=PROBE_COST, window=WINDOW,
                lam=LAM, delta=DELTA),
    ),
    "SPSC-Adaptive": dict(
        cls=SPSC_Adaptive,
        kw=dict(probe_every=PROBE_EVERY, probe_cost=PROBE_COST, window=WINDOW,
                lam=LAM, delta=DELTA, m_relearn=30, det_window=50,
                cusum_threshold=3.0, warmup=100),
    ),
    "Oracle-LinUCB": dict(
        cls=OracleLinUCB,
        kw=dict(window=WINDOW, lam=LAM, delta=DELTA),
    ),
    "LinUCB": dict(
        cls=LinUCB,
        kw=dict(lam=LAM, delta=DELTA),
    ),
    "SW-LinUCB": dict(
        cls=SWLinUCB,
        kw=dict(window=200, lam=LAM, delta=DELTA),
    ),
    "D-LinUCB": dict(
        cls=DLinUCB,
        kw=dict(gamma=0.998, lam=LAM, delta=DELTA),
    ),
    "Restart-LinUCB": dict(
        cls=RestartLinUCB,
        kw=dict(restart_period=500, lam=LAM, delta=DELTA),
    ),
    "LowOFUL": dict(
        cls=LowOFUL,
        kw=dict(lam=LAM, delta=DELTA, pca_warmup=30, subspace_update_freq=20),
    ),
    "VOFUL": dict(
        cls=VOFUL,
        kw=dict(lam=LAM, delta=DELTA, pca_warmup=30, subspace_update_freq=20),
    ),
    "ETC-LowRank": dict(
        cls=ETCLowRank,
        kw=dict(m_explore=50, probe_cost=PROBE_COST, window=WINDOW,
                lam=LAM, delta=DELTA),
    ),
}

ALGO_NAMES = list(ALGO_CONFIGS.keys())

COLORS = {
    "SPSC-Alg1":      "#1f77b4",
    "SPSC-Adaptive":   "#17becf",
    "Oracle-LinUCB":   "#2ca02c",
    "LinUCB":          "#d62728",
    "SW-LinUCB":       "#9467bd",
    "D-LinUCB":        "#ff7f0e",
    "Restart-LinUCB":  "#8c564b",
    "LowOFUL":         "#e377c2",
    "VOFUL":           "#bcbd22",
    "ETC-LowRank":     "#7f7f7f",
}

STYLES = {
    "SPSC-Alg1":      "-",
    "SPSC-Adaptive":   "-",
    "Oracle-LinUCB":   ":",
    "LinUCB":          "--",
    "SW-LinUCB":       "-.",
    "D-LinUCB":        "--",
    "Restart-LinUCB":  ":",
    "LowOFUL":         "--",
    "VOFUL":           "-.",
    "ETC-LowRank":     ":",
}

LABELS = {
    "SPSC-Alg1":      "SPSC Alg.1 (ours, oracle CP)",
    "SPSC-Adaptive":   "SPSC Adaptive (ours, no oracle)",
    "Oracle-LinUCB":   "Oracle LinUCB",
    "LinUCB":          "LinUCB",
    "SW-LinUCB":       "SW-LinUCB (Cheung+ '19)",
    "D-LinUCB":        "D-LinUCB (Russac+ '19)",
    "Restart-LinUCB":  "Restart-LinUCB",
    "LowOFUL":         "LowOFUL (Jun+ '19)",
    "VOFUL":           "VOFUL (Kim+ '22)",
    "ETC-LowRank":     "ETC-LowRank",
}


def run_sota_benchmark(d=40, r=3, T=T_DEFAULT):
    """Run all algorithms on a single (d, r, T) config, N_SEEDS seeds."""
    results = {name: [] for name in ALGO_NAMES}

    for seed in range(N_SEEDS):
        print(f"  SOTA seed {seed+1}/{N_SEEDS} ...", end="\r", flush=True)
        for name, cfg in ALGO_CONFIGS.items():
            env = make_env(d, r, T=T, seed=seed * 100)
            m = cfg["cls"](env, seed=seed + hash(name) % 10000, **cfg["kw"]).run()
            results[name].append(m)

    print(flush=True)
    return results


# =====================================================================
# (C) Algorithm 4 vs Algorithm 1 at multiple d
# =====================================================================

def run_adaptive_comparison():
    """Compare adaptive vs oracle across multiple d values."""
    configs = [
        (20, 3, 10000),
        (40, 3, 10000),
        (60, 5, 10000),
        (80, 5, 10000),
    ]
    results = {}
    for d, r, T in configs:
        print(f"  Adaptive comparison d={d}, r={r}, T={T} ...", flush=True)
        alg1_runs, adapt_runs, lin_runs = [], [], []

        for seed in range(N_SEEDS):
            env = make_env(d, r, T=T, seed=seed * 100)
            alg1_runs.append(
                SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                                window=WINDOW, lam=LAM, delta=DELTA, seed=seed).run()
            )

            env = make_env(d, r, T=T, seed=seed * 100)
            adapt_runs.append(
                SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                              window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                              m_relearn=30, det_window=50, cusum_threshold=3.0,
                              warmup=100).run()
            )

            env = make_env(d, r, T=T, seed=seed * 100)
            lin_runs.append(LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 5000).run())

        results[(d, r)] = {
            "SPSC-Alg1": alg1_runs,
            "SPSC-Adaptive": adapt_runs,
            "LinUCB": lin_runs,
        }
    return results


# =====================================================================
# Tables
# =====================================================================

def print_sota_table(results, d, r, T):
    print()
    print("=" * 100)
    print(f"SOTA Benchmark: d={d}, r={r}, K={K_DEFAULT}, T={T}, "
          f"sigma_eps={SIGMA_EPS}, probe_every={PROBE_EVERY}, n_seeds={N_SEEDS}")
    print("-" * 100)
    hdr = (f"{'Algorithm':<30}  {'Control (mean±SE)':>18}  "
           f"{'Costed (mean±SE)':>18}  {'vs LinUCB':>10}  {'Probes':>8}")
    print(hdr)
    print("-" * 100)

    lin_ctrl, _ = agg_final(results["LinUCB"], "cumulative_control_regret")

    for name in ALGO_NAMES:
        ctrl_m, ctrl_s = agg_final(results[name], "cumulative_control_regret")
        cost_m, cost_s = agg_final(results[name], "cumulative_costed_regret")
        probes = np.mean([r.total_probes for r in results[name]])
        pct = (ctrl_m - lin_ctrl) / lin_ctrl * 100
        sign = "+" if pct >= 0 else ""
        vs = f"{sign}{pct:.1f}%" if name != "LinUCB" else "---"
        print(f"  {LABELS[name]:<28}  {ctrl_m:>7.0f} ± {ctrl_s:>4.0f}    "
              f"{cost_m:>7.0f} ± {cost_s:>4.0f}    {vs:>10}  {probes:>8.0f}")
    print("=" * 100)


def print_adaptive_table(results):
    print()
    print("=" * 100)
    print("Adaptive vs Oracle Boundary Comparison")
    print("-" * 100)
    print(f"{'(d,r)':<12}  {'Alg1 ctrl':>12}  {'Adaptive ctrl':>14}  "
          f"{'LinUCB ctrl':>12}  {'Adapt/Alg1':>11}  {'Adapt/LinUCB':>13}")
    print("-" * 100)

    for (d, r), alg_dict in sorted(results.items()):
        a1_m, _ = agg_final(alg_dict["SPSC-Alg1"], "cumulative_control_regret")
        ad_m, _ = agg_final(alg_dict["SPSC-Adaptive"], "cumulative_control_regret")
        li_m, _ = agg_final(alg_dict["LinUCB"], "cumulative_control_regret")
        print(f"  ({d:2d},{r:2d})       {a1_m:>9.0f}      {ad_m:>11.0f}      "
              f"{li_m:>9.0f}     {ad_m/a1_m:>8.3f}      {ad_m/li_m:>10.3f}")
    print("=" * 100)


# =====================================================================
# Figures
# =====================================================================

def make_figure_sota(results, d, r, T, out_path):
    """3-panel figure: (a) cumulative curves, (b) final bar chart, (c) regret ratio."""
    t_axis = np.arange(1, T + 1)

    fig, axes = plt.subplots(1, 3, figsize=(20, 5.5))
    fig.subplots_adjust(wspace=0.32)

    # --- Panel (a): Cumulative control regret ---
    ax = axes[0]
    for name in ALGO_NAMES:
        mean, se = agg_curves(results[name], "cumulative_control_regret")
        ax.plot(t_axis, mean, color=COLORS[name], ls=STYLES[name],
                lw=2.0 if "SPSC" in name else 1.5, label=LABELS[name], zorder=3)
        ax.fill_between(t_axis, mean - se, mean + se,
                        color=COLORS[name], alpha=0.08, zorder=2)
    # Change points
    env_ref = make_env(d, r, T=T, seed=0)
    for cp in env_ref.tau[1:]:
        ax.axvline(cp, color="gray", ls=":", lw=0.8, alpha=0.5)
    ax.set_xlabel("Round $t$", fontsize=11)
    ax.set_ylabel("Cumulative Control Regret", fontsize=11)
    ax.set_title(f"(a) Cumulative regret ($d={d}$, $r={r}$)", fontsize=11)
    ax.legend(fontsize=6.5, loc="upper left", ncol=1)
    ax.set_xlim(1, T)
    ax.set_ylim(bottom=0)

    # --- Panel (b): Final regret bar chart ---
    ax = axes[1]
    names_sorted = sorted(ALGO_NAMES,
                          key=lambda n: agg_final(results[n], "cumulative_control_regret")[0])
    x = np.arange(len(names_sorted))
    means = [agg_final(results[n], "cumulative_control_regret")[0] for n in names_sorted]
    ses   = [agg_final(results[n], "cumulative_control_regret")[1] for n in names_sorted]
    colors_sorted = [COLORS[n] for n in names_sorted]
    bars = ax.barh(x, means, xerr=ses, color=colors_sorted, capsize=3, height=0.7)
    ax.set_yticks(x)
    ax.set_yticklabels([LABELS[n].split("(")[0].strip() for n in names_sorted],
                       fontsize=8)
    ax.set_xlabel("Final Control Regret", fontsize=11)
    ax.set_title("(b) Final regret ranking", fontsize=11)
    ax.xaxis.grid(True, alpha=0.3)

    # --- Panel (c): SPSC/LinUCB ratio over time ---
    ax = axes[2]
    lin_mean, _ = agg_curves(results["LinUCB"], "cumulative_control_regret")
    for name in ["SPSC-Alg1", "SPSC-Adaptive", "LowOFUL", "VOFUL"]:
        m, _ = agg_curves(results[name], "cumulative_control_regret")
        # Smooth ratio (avoid /0 at start)
        safe_lin = np.maximum(lin_mean, 1.0)
        ratio = m / safe_lin
        ax.plot(t_axis[100:], ratio[100:], color=COLORS[name], ls=STYLES[name],
                lw=2.0 if "SPSC" in name else 1.5, label=LABELS[name])
    ax.axhline(1.0, color="gray", ls="--", lw=1)
    ax.set_xlabel("Round $t$", fontsize=11)
    ax.set_ylabel("Regret / LinUCB Regret", fontsize=11)
    ax.set_title("(c) Regret ratio vs LinUCB", fontsize=11)
    ax.legend(fontsize=7, loc="best")
    ax.set_xlim(100, T)

    fig.suptitle(
        f"NeurIPS SOTA Benchmark  |  $d={d}$, $r={r}$, $K={K_DEFAULT}$, $T={T}$  "
        f"($n={N_SEEDS}$ seeds)",
        fontsize=11, y=1.02,
    )
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


def make_figure_phase(grid_results, out_path):
    """Phase-transition heatmap: SPSC/LinUCB costed regret ratio."""
    d_vals = sorted(set(d for d, r in grid_results))
    r_vals = sorted(set(r for d, r in grid_results))

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5),
                             gridspec_kw={"width_ratios": [1.2, 1]})

    # --- Panel (a): Heatmap ---
    ax = axes[0]
    ratio_grid = np.full((len(d_vals), len(r_vals)), np.nan)
    for i, d in enumerate(d_vals):
        for j, r in enumerate(r_vals):
            if (d, r) in grid_results:
                sm, lm, om = grid_results[(d, r)]
                ratio_grid[i, j] = sm / lm

    im = ax.imshow(ratio_grid.T, aspect="auto", origin="lower",
                   cmap="RdYlGn_r",
                   norm=TwoSlopeNorm(vmin=0.4, vcenter=1.0, vmax=1.6),
                   extent=[d_vals[0] - 5, d_vals[-1] + 5,
                           r_vals[0] - 1, r_vals[-1] + 1])
    for i, d in enumerate(d_vals):
        for j, r in enumerate(r_vals):
            if not np.isnan(ratio_grid[i, j]):
                ax.text(d, r, f"{ratio_grid[i,j]:.2f}", ha="center", va="center",
                        fontsize=8, fontweight="bold",
                        color="white" if ratio_grid[i,j] < 0.8 else "black")
    ax.set_xlabel("Ambient dimension $d$", fontsize=11)
    ax.set_ylabel("Rank $r$", fontsize=11)
    ax.set_title("(a) SPSC / LinUCB costed regret ratio", fontsize=11)
    ax.set_xticks(d_vals)
    ax.set_yticks(r_vals)
    fig.colorbar(im, ax=ax, label="Ratio (< 1 = SPSC wins)")

    # Phase transition boundary: d - r = T^{1/6}
    T_sixth = T_DEFAULT ** (1.0 / 6.0)
    d_line = np.linspace(d_vals[0], d_vals[-1], 100)
    r_line = d_line - T_sixth
    ax.plot(d_line, r_line, "k--", lw=1.5, label=f"$d - r = T^{{1/6}} \\approx {T_sixth:.1f}$")
    ax.legend(fontsize=8, loc="upper left")

    # --- Panel (b): 1D slices ---
    ax = axes[1]
    for r in r_vals:
        ratios = []
        ds = []
        for d in d_vals:
            if (d, r) in grid_results:
                sm, lm, _ = grid_results[(d, r)]
                ratios.append(sm / lm)
                ds.append(d)
        if ratios:
            ax.plot(ds, ratios, "o-", label=f"$r={r}$", markersize=5, lw=1.5)
    ax.axhline(1.0, color="gray", ls="--", lw=1)
    ax.set_xlabel("Ambient dimension $d$", fontsize=11)
    ax.set_ylabel("SPSC / LinUCB ratio", fontsize=11)
    ax.set_title("(b) Phase transition by rank", fontsize=11)
    ax.legend(fontsize=9)
    ax.set_ylim(0.3, 1.5)
    ax.grid(alpha=0.3)

    fig.suptitle(
        f"Phase Transition  |  $K={K_DEFAULT}$, $T={T_DEFAULT}$  "
        f"($n={N_SEEDS}$ seeds)",
        fontsize=11, y=1.02,
    )
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


def make_figure_adaptive(adapt_results, out_path):
    """Bar chart: Alg1 vs Adaptive vs LinUCB at multiple (d,r)."""
    configs = sorted(adapt_results.keys())
    n_configs = len(configs)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(n_configs)
    width = 0.25

    for i, name in enumerate(["SPSC-Alg1", "SPSC-Adaptive", "LinUCB"]):
        means, ses = [], []
        for cfg in configs:
            m, s = agg_final(adapt_results[cfg][name], "cumulative_control_regret")
            means.append(m)
            ses.append(s)
        color = COLORS[name]
        ax.bar(x + i * width, means, width, yerr=ses, label=LABELS[name],
               color=color, capsize=3, alpha=0.85)

    ax.set_xticks(x + width)
    ax.set_xticklabels([f"$d={d}$, $r={r}$" for d, r in configs], fontsize=10)
    ax.set_ylabel("Final Control Regret", fontsize=11)
    ax.set_title("Algorithm 4 (Adaptive) vs Algorithm 1 (Oracle Boundaries) vs LinUCB",
                 fontsize=11)
    ax.legend(fontsize=9)
    ax.yaxis.grid(True, alpha=0.3)

    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


# =====================================================================
# Main
# =====================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", action="store_true", help="Run phase-transition grid (A)")
    parser.add_argument("--sota", action="store_true", help="Run SOTA benchmark (B)")
    parser.add_argument("--adaptive", action="store_true", help="Run adaptive comparison (C)")
    parser.add_argument("--all", action="store_true", help="Run all experiments")
    parser.add_argument("--d", type=int, default=40, help="Ambient dim for SOTA benchmark")
    parser.add_argument("--r", type=int, default=3, help="Rank for SOTA benchmark")
    parser.add_argument("--T", type=int, default=T_DEFAULT, help="Horizon")
    parser.add_argument("--seeds", type=int, default=N_SEEDS, help="Number of seeds")
    args = parser.parse_args()

    if args.seeds != N_SEEDS:
        N_SEEDS = args.seeds

    run_all = args.all or not (args.phase or args.sota or args.adaptive)

    # ---- (A) Phase transition ----
    if args.phase or run_all:
        print("\n" + "=" * 60)
        print("(A) Phase-Transition Grid")
        print("=" * 60)
        grid = run_phase_grid()
        make_figure_phase(grid, os.path.join(OUT_DIR, "neurips_phase_transition.png"))

        # Print grid table
        print("\nPhase grid (SPSC/LinUCB ratio):")
        d_vals = sorted(set(d for d, r in grid))
        r_vals = sorted(set(r for d, r in grid))
        print(f"{'d\\r':>6}", end="")
        for r in r_vals:
            print(f"  r={r:>2}", end="")
        print()
        for d in d_vals:
            print(f"  d={d:>2}", end="")
            for r in r_vals:
                if (d, r) in grid:
                    sm, lm, _ = grid[(d, r)]
                    print(f"  {sm/lm:.3f}", end="")
                else:
                    print(f"  {'---':>5}", end="")
            print()

    # ---- (B) SOTA benchmark ----
    if args.sota or run_all:
        d_sota, r_sota = args.d, args.r
        T_sota = args.T
        print(f"\n{'=' * 60}")
        print(f"(B) SOTA Benchmark: d={d_sota}, r={r_sota}, T={T_sota}")
        print("=" * 60)
        sota = run_sota_benchmark(d=d_sota, r=r_sota, T=T_sota)
        print_sota_table(sota, d_sota, r_sota, T_sota)
        make_figure_sota(sota, d_sota, r_sota, T_sota,
                         os.path.join(OUT_DIR, f"neurips_sota_d{d_sota}_r{r_sota}.png"))

    # ---- (C) Adaptive comparison ----
    if args.adaptive or run_all:
        print(f"\n{'=' * 60}")
        print("(C) Adaptive vs Oracle Boundaries")
        print("=" * 60)
        adapt = run_adaptive_comparison()
        print_adaptive_table(adapt)
        make_figure_adaptive(adapt, os.path.join(OUT_DIR, "neurips_adaptive_comparison.png"))

    print("\nAll experiments complete.")
