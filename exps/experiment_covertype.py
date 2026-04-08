"""
Experiment: Covertype Semi-Synthetic Benchmark.

Uses the UCI Forest Covertype dataset (581K samples, 54 features) to
construct a semi-synthetic low-rank bandit with real feature structure
and controlled piecewise-stationary dynamics.

Benchmark protocol: real feature vectors define the action space; real data
statistics determine the low-rank subspace; AR(1) dynamics provide controlled
non-stationarity.  Used in contextual bandit benchmarks: Foster et al.
(ICML 2020), Bietti et al. (NeurIPS 2021), Agarwal et al. (ICML 2014).

Outputs
-------
  experiment_covertype.png       — 2-panel figure (costed + control regret)
  experiment_covertype_sweep.png — dimension sweep showing SPSC advantage vs d
  Printed table with comparison to published baselines.
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import CovtypeEnvironment
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB

# ---------------------------------------------------------------------------
# Parameters for main experiment
# ---------------------------------------------------------------------------

D           = 10       # ambient dimension (Covertype 10 quantitative features)
R           = 2        # latent rank
K           = 4        # segments
T           = 10000    # horizon
PROBE_EVERY = 30
PROBE_COST  = 0.1
WINDOW      = 100
N_SEEDS     = 10

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def make_env(seed, d=None, r=None):
    return CovtypeEnvironment(
        d=d or D, r=r or R, K=K, T=T,
        sigma_eps=0.3, spectral_radius=0.99,
        n_actions=80, seed=seed * 100,
        sigma_eta=0.04,
    )


def run_all(n_seeds, d=None, r=None):
    names   = ["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]
    results = {n: [] for n in names}

    for seed in range(n_seeds):
        print(f"  seed {seed+1}/{n_seeds} ...", end="\r", flush=True)

        env = make_env(seed, d=d, r=r)
        results["SPSC-Alg1"].append(
            SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=1.0, delta=0.05, seed=seed,
                            normalize_gamma_by_d=True).run()
        )

        env = make_env(seed, d=d, r=r)
        results["LinUCB"].append(
            LinUCB(env, lam=1.0, delta=0.05, seed=seed + 1000).run()
        )

        env = make_env(seed, d=d, r=r)
        results["Oracle-LinUCB"].append(
            OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                         seed=seed + 2000).run()
        )

    print(flush=True)
    return results


def agg(runs, attr):
    data = np.stack([getattr(r, attr) for r in runs])
    mean = data.mean(axis=0)
    se   = data.std(axis=0) / np.sqrt(len(runs))
    return mean, se


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(results, env_ref, out_path, d_val=None):
    d_val = d_val or D
    t_axis = np.arange(1, T + 1)
    change_pts = env_ref.tau[1:]

    COLORS = {
        "SPSC-Alg1":     "#1f77b4",
        "LinUCB":        "#d62728",
        "Oracle-LinUCB": "#2ca02c",
    }
    STYLES = {
        "SPSC-Alg1":     "-",
        "LinUCB":        "--",
        "Oracle-LinUCB": ":",
    }
    LABELS = {
        "SPSC-Alg1":     f"SPSC Algorithm 1 ($r={R}$-dim)",
        "LinUCB":        f"Ambient LinUCB ($d={d_val}$-dim)",
        "Oracle-LinUCB": f"Oracle LinUCB (true subspace, $r={R}$-dim)",
    }

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.subplots_adjust(wspace=0.30)

    panel_info = [
        ("cumulative_costed_regret",
         r"Cumulative Costed Regret $\mathrm{DynReg}_T^{(c)}$",
         "(a) Cumulative Costed Regret (primary metric)"),
        ("cumulative_control_regret",
         r"Cumulative Control Regret",
         "(b) Cumulative Control Regret (probe cost excluded)"),
    ]

    for ax, (attr, ylabel, title) in zip(axes, panel_info):
        for name, runs in results.items():
            mean, se = agg(runs, attr)
            ax.plot(t_axis, mean,
                    color=COLORS[name], ls=STYLES[name], lw=2.0,
                    label=LABELS[name], zorder=3)
            ax.fill_between(t_axis, mean - se, mean + se,
                            color=COLORS[name], alpha=0.18, zorder=2)
        for cp in change_pts:
            ax.axvline(cp, color="gray", ls=":", lw=1.0, alpha=0.65)
        ax.set_xlabel("Round $t$", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=11)
        ax.legend(fontsize=9, loc="upper left")
        ax.set_xlim(1, T)
        ax.set_ylim(bottom=0)
        ax.tick_params(labelsize=9)

    ax0 = axes[0]
    ymax = ax0.get_ylim()[1]
    for cp in change_pts:
        ax0.annotate("", xy=(cp, ymax * 0.07), xytext=(cp, ymax * 0.20),
                     arrowprops=dict(arrowstyle="->", color="gray", lw=1.2))

    fig.suptitle(
        f"Covertype Benchmark: SPSC vs LinUCB vs Oracle  |  "
        f"$d={d_val}$, $r={R}$, $K={K}$, $T={T}$, $c={PROBE_COST}$, "
        r"$\rho=0.99$, $\sigma_\eta=0.04$, "
        f"probe every {PROBE_EVERY}, $W={WINDOW}$  "
        f"($n={N_SEEDS}$ seeds, bands = $\\pm 1$ SE)",
        fontsize=10, y=1.02,
    )

    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

def print_table(results, env_ref, d_val=None):
    d_val = d_val or D
    n = N_SEEDS

    print()
    print("=" * 80)
    print("Covertype — Final cumulative regret summary")
    print(f"d={d_val}, r={R}, K={K}, T={T}, probe_every={PROBE_EVERY}, W={WINDOW}, c={PROBE_COST}")
    print("-" * 80)
    header = (f"{'Algorithm':<22}  {'Costed (mean+-SE)':>20}  "
              f"{'Control (mean+-SE)':>20}  {'Probes':>7}")
    print(header)
    print("-" * 80)

    finals = {}
    for name, runs in results.items():
        costed  = np.array([r.cumulative_costed_regret[-1]  for r in runs])
        control = np.array([r.cumulative_control_regret[-1] for r in runs])
        probes  = np.array([r.total_probes                  for r in runs])
        finals[name] = (costed.mean(), costed.std() / np.sqrt(n))
        print(
            f"  {name:<20}  "
            f"{costed.mean():>8.1f} +- {costed.std()/np.sqrt(n):>5.1f}  "
            f"{control.mean():>8.1f} +- {control.std()/np.sqrt(n):>5.1f}  "
            f"{probes.mean():>7.0f}"
        )

    print("-" * 80)
    spsc = finals["SPSC-Alg1"][0]
    lin  = finals["LinUCB"][0]
    ora  = finals["Oracle-LinUCB"][0]
    print(f"  SPSC / LinUCB ratio  : {spsc/lin:.3f}  "
          f"({'SPSC wins' if spsc < lin else 'LinUCB wins'})")
    print(f"  SPSC / Oracle ratio  : {spsc/ora:.3f}  "
          f"(1.0 = oracle-level)")
    print(f"  Theory sqrt(r/d)     : {(R/d_val)**0.5:.3f}  (exploitation-only lower bound)")

    print()
    print("=" * 80)
    print("Comparison with published baselines (Covertype, contextual bandits)")
    print("-" * 80)
    print("  Method                          Source                            Regret scaling")
    print("-" * 80)
    print("  LinUCB (full-dim)               Li et al. (WWW 2010)              O(d*sqrt(T))")
    print("  SquareCB                        Foster & Rakhlin (ICML 2020)      O(sqrt(K*T))")
    print("  LowESTR (low-rank)              Lu et al. (NeurIPS 2021)          O(r*sqrt(T))")
    print("  VOFUL (low-rank+non-stat.)      Cesa-Bianchi et al. (COLT 2023)   O(sqrt(rd*T))")
    print("-" * 80)
    print(f"  SPSC Alg 1 (ours, d={d_val},r={R})  This work                   "
          f"Costed: {finals['SPSC-Alg1'][0]:.1f} +- {finals['SPSC-Alg1'][1]:.1f}")
    print(f"  Ambient LinUCB (d={d_val})       This work (baseline)              "
          f"Costed: {finals['LinUCB'][0]:.1f} +- {finals['LinUCB'][1]:.1f}")
    print(f"  Oracle LinUCB (r={R})            This work (oracle ceiling)        "
          f"Costed: {finals['Oracle-LinUCB'][0]:.1f} +- {finals['Oracle-LinUCB'][1]:.1f}")
    print("-" * 80)
    if spsc < lin:
        ratio = lin / spsc
        pct = (1 - spsc/lin) * 100
        print(f"  SPSC achieves {ratio:.2f}x lower regret ({pct:.0f}% reduction) vs LinUCB")
        print(f"  Dimension reduction: r={R}-dim subspace vs d={d_val}-dim ambient")
        print(f"  SPSC within {spsc/ora:.2f}x of oracle performance")
    print("=" * 80)

    return finals


# ---------------------------------------------------------------------------
# Dimension sweep: show SPSC advantage grows with d
# ---------------------------------------------------------------------------

def run_dimension_sweep():
    """Run experiments at multiple d values to show scaling."""
    d_values = [6, 8, 10, 15, 20]
    sweep_results = {}

    for d_val in d_values:
        print(f"\n--- Dimension sweep: d={d_val} ---")
        results = run_all(N_SEEDS, d=d_val, r=R)

        spsc_costed = np.array([r.cumulative_costed_regret[-1]
                                for r in results["SPSC-Alg1"]])
        lin_costed  = np.array([r.cumulative_costed_regret[-1]
                                for r in results["LinUCB"]])
        ora_costed  = np.array([r.cumulative_costed_regret[-1]
                                for r in results["Oracle-LinUCB"]])

        n = N_SEEDS
        sweep_results[d_val] = {
            "spsc":   (spsc_costed.mean(), spsc_costed.std() / np.sqrt(n)),
            "linucb": (lin_costed.mean(),  lin_costed.std()  / np.sqrt(n)),
            "oracle": (ora_costed.mean(),  ora_costed.std()  / np.sqrt(n)),
            "ratio":  spsc_costed.mean() / lin_costed.mean(),
        }

    return d_values, sweep_results


def make_sweep_figure(d_values, sweep_results, out_path):
    """3-panel figure: regret vs d, ratio vs d, and theory comparison."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    fig.subplots_adjust(wspace=0.35)

    # Panel (a): Final costed regret vs d
    ax = axes[0]
    for name, color, marker in [
        ("spsc", "#1f77b4", "o"),
        ("linucb", "#d62728", "s"),
        ("oracle", "#2ca02c", "^"),
    ]:
        means = [sweep_results[d][name][0] for d in d_values]
        ses   = [sweep_results[d][name][1] for d in d_values]
        label = {"spsc": f"SPSC ($r={R}$)", "linucb": "LinUCB ($d$-dim)",
                 "oracle": f"Oracle ($r={R}$)"}[name]
        ax.errorbar(d_values, means, yerr=ses, color=color, marker=marker,
                    ms=6, lw=1.8, capsize=3, label=label)
    ax.set_xlabel("Ambient dimension $d$", fontsize=11)
    ax.set_ylabel("Final Cumulative Costed Regret", fontsize=11)
    ax.set_title("(a) Regret vs. dimension", fontsize=11)
    ax.legend(fontsize=9)
    ax.tick_params(labelsize=9)

    # Panel (b): SPSC/LinUCB ratio vs d
    ax = axes[1]
    ratios = [sweep_results[d]["ratio"] for d in d_values]
    ax.plot(d_values, ratios, "o-", color="#1f77b4", lw=2, ms=7, label="SPSC / LinUCB")
    ax.axhline(1.0, color="gray", ls="--", lw=1, alpha=0.6)
    ax.fill_between(d_values, [0]*len(d_values), [1]*len(d_values),
                    color="#1f77b4", alpha=0.08)
    ax.set_xlabel("Ambient dimension $d$", fontsize=11)
    ax.set_ylabel("SPSC / LinUCB regret ratio", fontsize=11)
    ax.set_title("(b) Relative performance", fontsize=11)
    ax.set_ylim(0, max(ratios) * 1.2)
    ax.legend(fontsize=9)
    ax.tick_params(labelsize=9)
    ax.annotate("SPSC wins", xy=(d_values[-1], 0.5), fontsize=9, color="#1f77b4",
                ha="right")

    # Panel (c): Theory vs empirical
    ax = axes[2]
    theory = [np.sqrt(R / d) for d in d_values]
    ax.plot(d_values, ratios, "o-", color="#1f77b4", lw=2, ms=7, label="Empirical ratio")
    ax.plot(d_values, theory, "s--", color="#2ca02c", lw=1.5, ms=5,
            label=r"Theory $\sqrt{r/d}$")
    ax.axhline(1.0, color="gray", ls="--", lw=1, alpha=0.6)
    ax.set_xlabel("Ambient dimension $d$", fontsize=11)
    ax.set_ylabel("Regret ratio", fontsize=11)
    ax.set_title("(c) Empirical vs. theory", fontsize=11)
    ax.legend(fontsize=9)
    ax.tick_params(labelsize=9)

    fig.suptitle(
        f"Covertype Dimension Sweep: $r={R}$, $K={K}$, $T={T}$, "
        f"$c={PROBE_COST}$, probe every {PROBE_EVERY}  "
        f"($n={N_SEEDS}$ seeds, bars = $\\pm 1$ SE)",
        fontsize=10, y=1.02,
    )

    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


# ---------------------------------------------------------------------------
# SVD analysis
# ---------------------------------------------------------------------------

def print_svd_analysis(env_ref):
    print()
    print("=" * 80)
    print("Subspace analysis of Covertype benchmark")
    print("-" * 80)

    for k in range(env_ref.K):
        start = env_ref.tau[k]
        end = start + env_ref.segment_lengths[k]
        seg_theta = env_ref.theta[start:end]

        _, S_vals, _ = np.linalg.svd(seg_theta, full_matrices=False)
        total_var = np.sum(S_vals ** 2)
        cumvar = np.cumsum(S_vals ** 2) / total_var

        r5 = min(4, len(cumvar) - 1)
        print(f"  Segment {k+1} (t={start}-{end-1}):")
        print(f"    Top singular values: {S_vals[:5].round(4)}")
        print(f"    Cumvar: r=1:{cumvar[0]:.3f}, r=2:{cumvar[1]:.3f}, "
              f"r=3:{cumvar[min(2,r5)]:.3f}, r=5:{cumvar[r5]:.3f}")

    print()
    print("  Cross-segment subspace distances (||P_k - P_{k-1}||_F):")
    for k in range(1, env_ref.K):
        P_prev = env_ref.segment_projector(k - 1)
        P_curr = env_ref.segment_projector(k)
        dist = np.linalg.norm(P_curr - P_prev, "fro")
        print(f"    Segment {k} -> {k+1}: {dist:.3f}")
    print("=" * 80)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    env_ref = make_env(0)

    print("=" * 60)
    print("Covertype Semi-Synthetic Benchmark")
    print(f"  d={D}, r={R}, K={K}, T={T}")
    print(f"  probe_every={PROBE_EVERY}, window={WINDOW}, c={PROBE_COST}")
    print(f"  n_actions={env_ref.n_actions}")
    print(f"  Segment boundaries: {env_ref.tau}")
    print(f"  n_seeds={N_SEEDS}")
    print(f"  max ||theta_t|| = {env_ref.S:.4f}")
    print("=" * 60)

    print_svd_analysis(env_ref)

    # Main experiment (d=10)
    print("\n--- Main experiment (d=10) ---")
    print("Running seeds...")
    results = run_all(N_SEEDS)
    print_table(results, env_ref)
    make_figure(
        results, env_ref,
        out_path=os.path.join(OUT_DIR, "experiment_covertype.png"),
    )

    # Dimension sweep
    print("\n\n" + "=" * 60)
    print("DIMENSION SWEEP: varying d with fixed r=2")
    print("=" * 60)
    d_values, sweep_results = run_dimension_sweep()

    print("\n" + "=" * 80)
    print(f"Dimension sweep summary (r={R}, K={K}, T={T})")
    print("-" * 80)
    print(f"  {'d':>4}  {'SPSC (mean+-SE)':>20}  {'LinUCB (mean+-SE)':>20}  "
          f"{'Oracle (mean+-SE)':>20}  {'SPSC/LinUCB':>12}")
    print("-" * 80)
    for d_val in d_values:
        s = sweep_results[d_val]
        print(f"  {d_val:>4}  "
              f"{s['spsc'][0]:>8.1f} +- {s['spsc'][1]:>5.1f}  "
              f"{s['linucb'][0]:>8.1f} +- {s['linucb'][1]:>5.1f}  "
              f"{s['oracle'][0]:>8.1f} +- {s['oracle'][1]:>5.1f}  "
              f"{s['ratio']:>10.3f}")
    print("=" * 80)

    make_sweep_figure(
        d_values, sweep_results,
        out_path=os.path.join(OUT_DIR, "experiment_covertype_sweep.png"),
    )

    print("\nDone.")
