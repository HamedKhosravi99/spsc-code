"""
Experiment 1: Main benchmark figure.

Compares SPSC-Algorithm1 vs ambient LinUCB vs Oracle-LinUCB on the
piecewise-stationary low-rank LDS bandit.

Outputs
-------
  experiment1_main_benchmark.png  — 2-panel figure (costed + control regret)
  Printed table of final cumulative regrets (mean ± SE over seeds).

Setup (same as fair main comparison)
--------------------------------------
  d=4, r=1, K=4, T=6000
  probe_every=30, window=100 (= correlation time 1/(1-rho))
  probe_cost c=0.1, n_seeds=10

Bands show mean ± 1 standard error (SE = std / sqrt(n_seeds)).
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import LowRankLDSEnvironment
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

D           = 4
R           = 1
K           = 4
T           = 6000
PROBE_EVERY = 30
PROBE_COST  = 0.1
WINDOW      = 100
N_SEEDS     = 10

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Visual style
# ---------------------------------------------------------------------------

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
    "LinUCB":        f"Ambient LinUCB ($d={D}$-dim)",
    "Oracle-LinUCB": f"Oracle LinUCB (true subspace, $r={R}$-dim)",
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def make_env(seed):
    return LowRankLDSEnvironment(d=D, r=R, K=K, T=T, seed=seed * 100)


def run_all(n_seeds):
    names   = ["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]
    results = {n: [] for n in names}

    for seed in range(n_seeds):
        print(f"  seed {seed+1}/{n_seeds} ...", end="\r", flush=True)

        env = make_env(seed)
        results["SPSC-Alg1"].append(
            SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=1.0, delta=0.05, seed=seed).run()
        )

        env = make_env(seed)
        results["LinUCB"].append(
            LinUCB(env, lam=1.0, delta=0.05, seed=seed + 1000).run()
        )

        env = make_env(seed)
        results["Oracle-LinUCB"].append(
            OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                         seed=seed + 2000).run()
        )

    print(flush=True)
    return results


def agg(runs, attr):
    """Return (mean, se) arrays over seeds."""
    data = np.stack([getattr(r, attr) for r in runs])
    mean = data.mean(axis=0)
    se   = data.std(axis=0) / np.sqrt(len(runs))
    return mean, se


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(results, env_ref, out_path):
    t_axis = np.arange(1, T + 1)
    change_pts = env_ref.tau[1:]          # segment boundaries (skip t=0)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.subplots_adjust(wspace=0.30)

    panel_info = [
        ("cumulative_costed_regret",   r"Cumulative Costed Regret $\mathrm{DynReg}_T^{(c)}$",
         "(a) Cumulative Costed Regret (primary metric)"),
        ("cumulative_control_regret",  r"Cumulative Control Regret",
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

    # Annotate change-point arrows on panel (a)
    ax0 = axes[0]
    ymax = ax0.get_ylim()[1]
    for cp in change_pts:
        ax0.annotate("", xy=(cp, ymax * 0.07), xytext=(cp, ymax * 0.20),
                     arrowprops=dict(arrowstyle="->", color="gray", lw=1.2))

    fig.suptitle(
        f"Experiment 1: SPSC vs LinUCB vs Oracle  |  "
        f"$d={D}$, $r={R}$, $K={K}$, $T={T}$, $c={PROBE_COST}$, "
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

def print_table(results, env_ref):
    lam_r   = env_ref.sigma_eta / (1 - env_ref.spectral_radius ** 2)
    n       = N_SEEDS

    print()
    print("=" * 72)
    print("Experiment 1 — Final cumulative regret summary")
    print(f"d={D}, r={R}, K={K}, T={T}, probe_every={PROBE_EVERY}, W={WINDOW}, c={PROBE_COST}")
    print(f"sigma_eta={env_ref.sigma_eta}, rho={env_ref.spectral_radius}, "
          f"lambda_r(M*)~{lam_r:.3f}")
    print("-" * 72)
    header = f"{'Algorithm':<22}  {'Costed (mean±SE)':>20}  {'Control (mean±SE)':>20}  {'Probes':>7}"
    print(header)
    print("-" * 72)

    finals = {}
    for name, runs in results.items():
        costed  = np.array([r.cumulative_costed_regret[-1]  for r in runs])
        control = np.array([r.cumulative_control_regret[-1] for r in runs])
        probes  = np.array([r.total_probes                  for r in runs])
        finals[name] = costed.mean()
        print(
            f"  {name:<20}  "
            f"{costed.mean():>8.1f} ± {costed.std()/np.sqrt(n):>5.1f}  "
            f"{control.mean():>8.1f} ± {control.std()/np.sqrt(n):>5.1f}  "
            f"{probes.mean():>7.0f}"
        )

    print("-" * 72)
    spsc = finals["SPSC-Alg1"]
    lin  = finals["LinUCB"]
    ora  = finals["Oracle-LinUCB"]
    print(f"  SPSC / LinUCB ratio  : {spsc/lin:.3f}  "
          f"({'SPSC wins' if spsc < lin else 'LinUCB wins'})")
    print(f"  SPSC / Oracle ratio  : {spsc/ora:.3f}  "
          f"(1.0 = oracle-level)")
    print(f"  Theory sqrt(r/d)     : {(R/D)**0.5:.3f}  (exploitation-only lower bound)")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    env_ref = make_env(0)

    print("=" * 60)
    print("Experiment 1: Main Benchmark")
    print(f"  d={D}, r={R}, K={K}, T={T}")
    print(f"  probe_every={PROBE_EVERY}, window={WINDOW}, c={PROBE_COST}")
    print(f"  sigma_eta={env_ref.sigma_eta}, rho={env_ref.spectral_radius}")
    print(f"  Segment boundaries: {env_ref.tau}")
    print(f"  n_seeds={N_SEEDS}")
    print("=" * 60)

    print("\nRunning seeds...")
    results = run_all(N_SEEDS)

    print_table(results, env_ref)

    make_figure(
        results, env_ref,
        out_path=os.path.join(OUT_DIR, "experiment1_main_benchmark.png"),
    )

    print("\nDone.")
