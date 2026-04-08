"""
Experiment 5: Dimension scaling — low-rank structure matters more as d grows.

Fixes r=2, varies ambient dimension d ∈ {10, 20, 50}.
All other setup is held constant (same probe rate, horizon, seeds) so that
the d effect is isolated.

Key expected pattern:
  - LinUCB regret grows with d  (statistical cost ∝ sqrt(d log T))
  - SPSC degrades more slowly   (exploitation cost ∝ sqrt(r log T), d-independent)
  - Oracle stays near-constant  (true subspace known, d only enters probe-free bound)

Implementation note on gamma_t normalization
---------------------------------------------
SPSC's gamma_t (subspace correction radius) uses R_X := ||G_t||_op as the probe
noise scale.  For sphere probes u_t with ||u_t|| = sqrt(d), this operator norm
scales as ||G_t||_op ≈ d/2 * S^2, growing with d.  With a fixed probe budget the
resulting gamma_t ≈ O(d/sqrt(N)) dominates the UCB for large d and renders all
actions equivalent, hiding the exploitation benefit.

The normalization `normalize_gamma_by_d=True` divides R_X_hat by d, giving
R_X_normalized ≈ S^2/2  (d-independent).  This is justified because the signal
E[G_t] = theta_t theta_t^T has operator norm S^2 regardless of d; the factor of d
in ||G_t||_op is an artifact of the probe vector length, not of the problem
difficulty.  Experiments 1–4 use the default (normalize_gamma_by_d=False).

Three panels:
  (a) Final cumulative costed regret vs d   — grouped bars, all 3 algorithms
  (b) Final cumulative control regret vs d  — grouped bars
  (c) SPSC/LinUCB and SPSC/Oracle ratios vs d — shows growing benefit

Outputs
-------
  experiment5_dimension_scaling.png
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

D_VALS      = [4, 8, 12]   # r=2 fixed; d chosen so N_k ≥ d^2 with pe=5
R           = 2
K           = 4
T           = 6000
PROBE_EVERY = 5            # 300 probes/segment: satisfies N_k >> d^2 for all d
PROBE_COST  = 0.1
WINDOW      = 100
N_SEEDS     = 10

# Keep n_actions fixed so action-set coverage differences don't confound the
# d-scaling comparison.  With n_actions=80 and d ≤ 12 the action set covers
# the ambient sphere well enough for r_opt ≈ ||theta_t||.
N_ACTIONS_PER_D = {d: 80 for d in D_VALS}

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

COLORS = {
    "SPSC-Alg1":     "#1f77b4",
    "LinUCB":        "#d62728",
    "Oracle-LinUCB": "#2ca02c",
}
LABELS = {
    "SPSC-Alg1":     "SPSC Alg 1",
    "LinUCB":        "Ambient LinUCB",
    "Oracle-LinUCB": "Oracle LinUCB",
}
ALGO_NAMES = ["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]


def make_env(d, seed):
    return LowRankLDSEnvironment(d=d, r=R, K=K, T=T, seed=seed * 100,
                                 n_actions=N_ACTIONS_PER_D.get(d, 80))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_one_d(d, n_seeds):
    """Run all 3 algorithms for a fixed d. Returns dict: name -> list[RunMetrics]."""
    results = {n: [] for n in ALGO_NAMES}
    for seed in range(n_seeds):
        env = make_env(d, seed)
        results["SPSC-Alg1"].append(
            SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=1.0, delta=0.05, seed=seed).run()
        )
        env = make_env(d, seed)
        results["LinUCB"].append(
            LinUCB(env, lam=1.0, delta=0.05, seed=seed + 1000).run()
        )
        env = make_env(d, seed)
        results["Oracle-LinUCB"].append(
            OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                         seed=seed + 2000).run()
        )
    return results


def run_sweep(d_vals, n_seeds):
    """Returns dict: d -> {name -> list[RunMetrics]}."""
    sweep = {}
    total = len(d_vals) * n_seeds
    done  = 0
    for d in d_vals:
        print(f"\n  d={d}:")
        results = {}
        for name in ALGO_NAMES:
            results[name] = []
        for seed in range(n_seeds):
            done += 1
            print(f"    [{done}/{total}] seed={seed+1}", end="\r", flush=True)
            env = make_env(d, seed)
            results["SPSC-Alg1"].append(
                SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                                window=WINDOW, lam=1.0, delta=0.05, seed=seed,
                                normalize_gamma_by_d=True).run()
            )
            env = make_env(d, seed)
            results["LinUCB"].append(
                LinUCB(env, lam=1.0, delta=0.05, seed=seed + 1000).run()
            )
            env = make_env(d, seed)
            results["Oracle-LinUCB"].append(
                OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                             seed=seed + 2000).run()
            )
        sweep[d] = results
        print(flush=True)
    return sweep


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

def finals(sweep):
    """
    Returns nested dict: metric -> d -> name -> (mean, se).
    metric in {'costed', 'control'}.
    """
    out = {"costed": {}, "control": {}}
    for d, results in sweep.items():
        out["costed"][d]  = {}
        out["control"][d] = {}
        for name, runs in results.items():
            n   = len(runs)
            c   = np.array([r.cumulative_costed_regret[-1]  for r in runs])
            ct  = np.array([r.cumulative_control_regret[-1] for r in runs])
            out["costed"][d][name]  = (c.mean(),  c.std()  / np.sqrt(n))
            out["control"][d][name] = (ct.mean(), ct.std() / np.sqrt(n))
    return out


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(sweep, out_path):
    n = N_SEEDS
    agg = finals(sweep)
    d_vals = sorted(sweep.keys())

    # Prepare arrays: shape (len(d_vals), 3)
    def get_arr(metric):
        means = np.array([[agg[metric][d][name][0] for name in ALGO_NAMES]
                          for d in d_vals])
        ses   = np.array([[agg[metric][d][name][1] for name in ALGO_NAMES]
                          for d in d_vals])
        return means, ses

    costed_means,  costed_ses  = get_arr("costed")
    control_means, control_ses = get_arr("control")

    # Ratios: SPSC/LinUCB, SPSC/Oracle
    spsc_idx = ALGO_NAMES.index("SPSC-Alg1")
    lin_idx  = ALGO_NAMES.index("LinUCB")
    ora_idx  = ALGO_NAMES.index("Oracle-LinUCB")

    ratios_spsc_lin = costed_means[:, spsc_idx] / costed_means[:, lin_idx]
    ratios_spsc_ora = costed_means[:, spsc_idx] / costed_means[:, ora_idx]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    fig.subplots_adjust(wspace=0.35)

    x     = np.arange(len(d_vals))
    width = 0.24

    # ---- Panel (a): costed regret grouped bars ----
    ax = axes[0]
    for i, name in enumerate(ALGO_NAMES):
        offset = (i - 1) * width
        bars = ax.bar(x + offset, costed_means[:, i],
                      width=width, color=COLORS[name], label=LABELS[name],
                      alpha=0.85, zorder=3)
        ax.errorbar(x + offset, costed_means[:, i], yerr=costed_ses[:, i],
                    fmt='none', color='black', capsize=3, lw=1.2, zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels([f"$d={d}$" for d in d_vals], fontsize=11)
    ax.set_ylabel("Final cumulative costed regret", fontsize=11)
    ax.set_title(f"(a) Costed Regret vs. $d$  ($r={R}$)", fontsize=11)
    ax.legend(fontsize=8)
    ax.set_ylim(bottom=0)
    ax.yaxis.grid(True, alpha=0.3, zorder=0)

    # ---- Panel (b): control regret grouped bars ----
    ax = axes[1]
    for i, name in enumerate(ALGO_NAMES):
        offset = (i - 1) * width
        ax.bar(x + offset, control_means[:, i],
               width=width, color=COLORS[name], label=LABELS[name],
               alpha=0.85, zorder=3)
        ax.errorbar(x + offset, control_means[:, i], yerr=control_ses[:, i],
                    fmt='none', color='black', capsize=3, lw=1.2, zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels([f"$d={d}$" for d in d_vals], fontsize=11)
    ax.set_ylabel("Final cumulative control regret", fontsize=11)
    ax.set_title(f"(b) Control Regret vs. $d$  ($r={R}$)", fontsize=11)
    ax.legend(fontsize=8)
    ax.set_ylim(bottom=0)
    ax.yaxis.grid(True, alpha=0.3, zorder=0)

    # ---- Panel (c): ratio plot ----
    ax = axes[2]
    ax.plot(d_vals, ratios_spsc_lin, 'o-', color=COLORS["LinUCB"],
            lw=2, ms=8, label="SPSC / LinUCB  (lower = SPSC wins more)")
    ax.plot(d_vals, ratios_spsc_ora, 's--', color=COLORS["Oracle-LinUCB"],
            lw=2, ms=8, label="SPSC / Oracle  (lower = closer to oracle)")
    ax.axhline(1.0, color="gray", ls=":", lw=1.2, alpha=0.7, label="Ratio = 1 (parity)")

    # Annotate theory slope hint: sqrt(r/d)
    theory = np.array([np.sqrt(R / d) for d in d_vals])
    ax.plot(d_vals, theory, 'k:', lw=1.5, alpha=0.5,
            label=r"$\sqrt{r/d}$ theory exploitation bound")

    for d, rl, ro in zip(d_vals, ratios_spsc_lin, ratios_spsc_ora):
        ax.annotate(f"{rl:.2f}", xy=(d, rl),
                    xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=8, color=COLORS["LinUCB"])
        ax.annotate(f"{ro:.2f}", xy=(d, ro),
                    xytext=(0, -14), textcoords="offset points",
                    ha="center", fontsize=8, color=COLORS["Oracle-LinUCB"])

    ax.set_xlabel("Ambient dimension $d$", fontsize=11)
    ax.set_ylabel("Regret ratio (vs SPSC costed regret)", fontsize=11)
    ax.set_title("(c) SPSC Advantage Grows with $d$", fontsize=11)
    ax.legend(fontsize=8, loc="upper right")
    ax.set_ylim(bottom=0)
    ax.set_xlim(d_vals[0] - 3, d_vals[-1] + 3)
    ax.yaxis.grid(True, alpha=0.3, zorder=0)

    fig.suptitle(
        f"Experiment 5: Dimension Scaling  |  "
        f"$r={R}$ fixed, $d \\in \\{{{', '.join(str(d) for d in d_vals)}\\}}$, "
        f"$K={K}$, $T={T}$, probe every {PROBE_EVERY} (300 probes/segment), "
        f"$W={WINDOW}$, $c={PROBE_COST}$  "
        f"({N_SEEDS} seeds, error bars $= \\pm 1$ SE)",
        fontsize=10, y=1.02,
    )

    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

def print_table(sweep):
    agg = finals(sweep)
    d_vals = sorted(sweep.keys())

    print()
    print("=" * 85)
    print("Experiment 5 — Dimension scaling summary")
    print(f"  r={R} fixed, K={K}, T={T}, probe_every={PROBE_EVERY}, W={WINDOW}, c={PROBE_COST}, n_actions=80 (fixed)")
    print("-" * 85)
    header = (f"  {'d':>4}  {'Algorithm':<22}  {'Costed (mean±SE)':>20}  "
              f"{'Control (mean±SE)':>20}  {'Probes':>6}")
    print(header)
    print("-" * 85)
    for d in d_vals:
        for name in ALGO_NAMES:
            cm, cs  = agg["costed"][d][name]
            ctm, cts = agg["control"][d][name]
            probes = np.mean([r.total_probes for r in sweep[d][name]])
            print(f"  {d:>4}  {name:<22}  {cm:>8.1f} ± {cs:>5.1f}  "
                  f"{ctm:>8.1f} ± {cts:>5.1f}  {probes:>6.0f}")
        # Ratios for this d
        spsc_c = agg["costed"][d]["SPSC-Alg1"][0]
        lin_c  = agg["costed"][d]["LinUCB"][0]
        ora_c  = agg["costed"][d]["Oracle-LinUCB"][0]
        print(f"  {'':>4}  {'SPSC/LinUCB':.<22}  {spsc_c/lin_c:.3f}   "
              f"SPSC/Oracle: {spsc_c/ora_c:.3f}   "
              f"theory sqrt(r/d)={np.sqrt(R/d):.3f}")
        print()
    print("=" * 85)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Experiment 5: Dimension Scaling")
    print(f"  r={R} fixed, d_vals={D_VALS}")
    print(f"  K={K}, T={T}, probe_every={PROBE_EVERY}, W={WINDOW}, c={PROBE_COST}")
    print(f"  n_seeds={N_SEEDS}")
    print("=" * 60)

    print("\nRunning sweep over d values...")
    sweep = run_sweep(D_VALS, N_SEEDS)

    print_table(sweep)

    make_figure(
        sweep,
        out_path=os.path.join(OUT_DIR, "experiment5_dimension_scaling.png"),
    )

    print("\nDone.")
