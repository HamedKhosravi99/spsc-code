"""
Experiment 8: Drift Speed

Sweeps LDS spectral radius rho over {0.30, 0.50, 0.70, 0.90, 0.95, 0.99}.
Higher rho = slower decay = longer correlation time = more signal energy.

Outputs
-------
  experiment8_drift_speed.png  — 3-panel figure
    (a) Control regret vs rho
    (b) Regret ratios vs rho
    (c) Subspace error vs rho
"""

import os, sys, numpy as np
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

RHO_VALS = [0.30, 0.50, 0.70, 0.90, 0.95, 0.99]

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

COLORS = {
    "SPSC-Alg1":     "#1f77b4",
    "LinUCB":        "#d62728",
    "Oracle-LinUCB": "#2ca02c",
}
LABELS = {
    "SPSC-Alg1":     "SPSC Algorithm 1",
    "LinUCB":        "Ambient LinUCB",
    "Oracle-LinUCB": "Oracle LinUCB",
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def make_env(rho, seed):
    return LowRankLDSEnvironment(d=D, r=R, K=K, T=T,
                                  spectral_radius=rho, seed=seed * 100)


def run_sweep(rho_vals, n_seeds):
    sweep = {}
    for rho in rho_vals:
        names = ["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]
        results = {n: [] for n in names}
        for seed in range(n_seeds):
            print(f"  rho={rho}, seed {seed+1}/{n_seeds}", end="\r", flush=True)

            env = make_env(rho, seed)
            results["SPSC-Alg1"].append(
                SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                                window=WINDOW, lam=1.0, delta=0.05, seed=seed).run()
            )
            env = make_env(rho, seed)
            results["LinUCB"].append(
                LinUCB(env, lam=1.0, delta=0.05, seed=seed + 1000).run()
            )
            env = make_env(rho, seed)
            results["Oracle-LinUCB"].append(
                OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                             seed=seed + 2000).run()
            )
        sweep[rho] = results
    print(flush=True)
    return sweep


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(sweep, out_path):
    rhos = sorted(sweep.keys())

    spsc_ctrl, lin_ctrl, ora_ctrl = [], [], []
    spsc_se, lin_se, ora_se = [], [], []
    sub_errors = []

    for rho in rhos:
        for name, sm, ss in [
            ("SPSC-Alg1", spsc_ctrl, spsc_se),
            ("LinUCB", lin_ctrl, lin_se),
            ("Oracle-LinUCB", ora_ctrl, ora_se),
        ]:
            finals = np.array([r.cumulative_control_regret[-1]
                               for r in sweep[rho][name]])
            n = len(finals)
            sm.append(finals.mean())
            ss.append(finals.std() / np.sqrt(n))

        # Subspace error: mean of last-round subspace error across seeds
        se_vals = []
        for r in sweep[rho]["SPSC-Alg1"]:
            valid = r.subspace_error[~np.isnan(r.subspace_error)]
            if len(valid) > 0:
                se_vals.append(valid[-1])
        sub_errors.append(np.mean(se_vals) if se_vals else np.nan)

    spsc_ctrl = np.array(spsc_ctrl)
    lin_ctrl  = np.array(lin_ctrl)
    ora_ctrl  = np.array(ora_ctrl)

    ratio_lin = spsc_ctrl / lin_ctrl
    ratio_ora = spsc_ctrl / ora_ctrl

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    fig.subplots_adjust(wspace=0.30)

    # Panel (a): Control regret vs rho
    ax = axes[0]
    x = np.arange(len(rhos))
    w = 0.25
    ax.bar(x - w, spsc_ctrl, w, yerr=np.array(spsc_se), color=COLORS["SPSC-Alg1"],
           label=LABELS["SPSC-Alg1"], capsize=3)
    ax.bar(x,     lin_ctrl,  w, yerr=np.array(lin_se),  color=COLORS["LinUCB"],
           label=LABELS["LinUCB"], capsize=3)
    ax.bar(x + w, ora_ctrl,  w, yerr=np.array(ora_se),  color=COLORS["Oracle-LinUCB"],
           label=LABELS["Oracle-LinUCB"], capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels([str(r) for r in rhos])
    ax.set_xlabel(r"Spectral radius $\rho$", fontsize=11)
    ax.set_ylabel("Final Control Regret", fontsize=11)
    ax.set_title(r"(a) Control regret vs. $\rho$", fontsize=11)
    ax.legend(fontsize=7); ax.yaxis.grid(True, alpha=0.3)

    # Panel (b): Ratios
    ax = axes[1]
    ax.plot(rhos, ratio_lin, "o-", color=COLORS["SPSC-Alg1"], lw=2,
            label="SPSC / LinUCB")
    ax.plot(rhos, ratio_ora, "s--", color=COLORS["Oracle-LinUCB"], lw=2,
            label="SPSC / Oracle")
    ax.axhline(1.0, color="gray", ls=":", lw=1)
    for i, rho in enumerate(rhos):
        ax.annotate(f"{ratio_lin[i]:.3f}", (rho, ratio_lin[i]),
                    textcoords="offset points", xytext=(0, 8), fontsize=7, ha="center")
    ax.set_xlabel(r"Spectral radius $\rho$", fontsize=11)
    ax.set_ylabel("Regret Ratio", fontsize=11)
    ax.set_title(r"(b) Regret ratios vs. $\rho$", fontsize=11)
    ax.legend(fontsize=9); ax.yaxis.grid(True, alpha=0.3)

    # Panel (c): Subspace error vs rho
    ax = axes[2]
    ax.plot(rhos, sub_errors, "D-", color="#9467bd", lw=2, markersize=7)
    ax.set_xlabel(r"Spectral radius $\rho$", fontsize=11)
    ax.set_ylabel(r"Final subspace error $\|\hat P - P^*\|_2$", fontsize=11)
    ax.set_title(r"(c) Subspace error vs. $\rho$", fontsize=11)
    ax.yaxis.grid(True, alpha=0.3)

    fig.suptitle(
        f"Experiment 8: Drift Speed  |  "
        f"$d={D}$, $r={R}$, $K={K}$, $T={T}$, $c={PROBE_COST}$, "
        f"probe every {PROBE_EVERY}, $W={WINDOW}$  "
        f"($n={N_SEEDS}$ seeds)",
        fontsize=10, y=1.02,
    )
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

def print_table(sweep):
    rhos = sorted(sweep.keys())
    print()
    print("=" * 100)
    print("Experiment 8 — Drift Speed Summary")
    print("-" * 100)
    header = (f"{'rho':>5}  {'tau':>5}  {'Algorithm':<20}  {'Control (mean±SE)':>20}  "
              f"{'Costed (mean±SE)':>20}  {'SPSC/LinUCB':>11}  {'SPSC/Oracle':>11}")
    print(header)
    print("-" * 100)

    for rho in rhos:
        tau = 1.0 / (1.0 - rho)
        finals = {}
        for name in ["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]:
            ctrl = np.array([r.cumulative_control_regret[-1]
                             for r in sweep[rho][name]])
            cost = np.array([r.cumulative_costed_regret[-1]
                             for r in sweep[rho][name]])
            n = len(ctrl)
            finals[name] = (ctrl.mean(), ctrl.std()/np.sqrt(n),
                            cost.mean(), cost.std()/np.sqrt(n))

        rl = finals["SPSC-Alg1"][0] / finals["LinUCB"][0]
        ro = finals["SPSC-Alg1"][0] / finals["Oracle-LinUCB"][0]

        for i, name in enumerate(["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]):
            cm, cs, xm, xs = finals[name]
            rho_s = f"{rho:.2f}" if i == 0 else ""
            tau_s = f"{tau:.1f}" if i == 0 else ""
            rl_s = f"{rl:.3f}" if i == 0 else ""
            ro_s = f"{ro:.3f}" if i == 0 else ""
            print(f"{rho_s:>5}  {tau_s:>5}  {name:<20}  "
                  f"{cm:>8.0f} ± {cs:>5.0f}       "
                  f"{xm:>8.0f} ± {xs:>5.0f}       {rl_s:>11}  {ro_s:>11}")
        print()
    print("=" * 100)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Experiment 8: Drift Speed")
    print(f"  d={D}, r={R}, K={K}, T={T}")
    print(f"  rho sweep: {RHO_VALS}")
    print(f"  n_seeds={N_SEEDS}")
    print("=" * 60)

    sweep = run_sweep(RHO_VALS, N_SEEDS)
    print_table(sweep)
    make_figure(sweep, os.path.join(OUT_DIR, "experiment8_drift_speed.png"))
    print("\nDone.")
