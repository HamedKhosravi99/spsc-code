"""
Experiment 7: Changepoint Frequency

Sweeps K (number of segments) over {1, 2, 4, 6, 8, 12} with T=6000 fixed,
giving segment lengths {6000, 3000, 1500, 1000, 750, 500}.

Outputs
-------
  experiment7_changepoint_frequency.png  — 3-panel figure
    (a) Costed regret vs K
    (b) Control regret vs K
    (c) Regret ratios vs K
"""

import os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from environment import LowRankLDSEnvironment
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

D           = 4
R           = 1
T           = 6000
PROBE_EVERY = 30
PROBE_COST  = 0.1
WINDOW      = 100
N_SEEDS     = 10

K_VALS = [1, 2, 4, 6, 8, 12]

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

def make_env(K, seed):
    return LowRankLDSEnvironment(d=D, r=R, K=K, T=T, seed=seed * 100)


def run_sweep(k_vals, n_seeds):
    sweep = {}
    for K in k_vals:
        names = ["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]
        results = {n: [] for n in names}
        for seed in range(n_seeds):
            print(f"  K={K}, seed {seed+1}/{n_seeds}", end="\r", flush=True)

            env = make_env(K, seed)
            results["SPSC-Alg1"].append(
                SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                                window=WINDOW, lam=1.0, delta=0.05, seed=seed).run()
            )
            env = make_env(K, seed)
            results["LinUCB"].append(
                LinUCB(env, lam=1.0, delta=0.05, seed=seed + 1000).run()
            )
            env = make_env(K, seed)
            results["Oracle-LinUCB"].append(
                OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                             seed=seed + 2000).run()
            )
        sweep[K] = results
    print(flush=True)
    return sweep


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(sweep, out_path):
    k_vals = sorted(sweep.keys())

    spsc_costed, lin_costed, ora_costed = [], [], []
    spsc_ctrl, lin_ctrl, ora_ctrl = [], [], []
    spsc_cs, lin_cs, ora_cs = [], [], []
    spsc_crs, lin_crs, ora_crs = [], [], []

    for K in k_vals:
        for name, sm, ss, cm, cs in [
            ("SPSC-Alg1", spsc_costed, spsc_cs, spsc_ctrl, spsc_crs),
            ("LinUCB", lin_costed, lin_cs, lin_ctrl, lin_crs),
            ("Oracle-LinUCB", ora_costed, ora_cs, ora_ctrl, ora_crs),
        ]:
            cost_f = np.array([r.cumulative_costed_regret[-1]
                               for r in sweep[K][name]])
            ctrl_f = np.array([r.cumulative_control_regret[-1]
                               for r in sweep[K][name]])
            n = len(cost_f)
            sm.append(cost_f.mean()); ss.append(cost_f.std() / np.sqrt(n))
            cm.append(ctrl_f.mean()); cs.append(ctrl_f.std() / np.sqrt(n))

    spsc_costed = np.array(spsc_costed)
    lin_costed  = np.array(lin_costed)
    ora_costed  = np.array(ora_costed)
    spsc_ctrl   = np.array(spsc_ctrl)
    lin_ctrl    = np.array(lin_ctrl)
    ora_ctrl    = np.array(ora_ctrl)

    ratio_lin = spsc_costed / lin_costed
    ratio_ora = spsc_costed / ora_costed

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    fig.subplots_adjust(wspace=0.30)

    x = np.arange(len(k_vals))
    w = 0.25
    k_labels = [str(k) for k in k_vals]

    # Panel (a): Costed regret
    ax = axes[0]
    ax.bar(x - w, spsc_costed, w, yerr=np.array(spsc_cs), color=COLORS["SPSC-Alg1"],
           label=LABELS["SPSC-Alg1"], capsize=3)
    ax.bar(x,     lin_costed,  w, yerr=np.array(lin_cs),  color=COLORS["LinUCB"],
           label=LABELS["LinUCB"], capsize=3)
    ax.bar(x + w, ora_costed,  w, yerr=np.array(ora_cs),  color=COLORS["Oracle-LinUCB"],
           label=LABELS["Oracle-LinUCB"], capsize=3)
    ax.set_xticks(x); ax.set_xticklabels(k_labels)
    ax.set_xlabel("$K$ (number of segments)", fontsize=11)
    ax.set_ylabel("Final Costed Regret", fontsize=11)
    ax.set_title("(a) Costed regret vs. $K$", fontsize=11)
    ax.legend(fontsize=7); ax.yaxis.grid(True, alpha=0.3)

    # Panel (b): Control regret
    ax = axes[1]
    ax.bar(x - w, spsc_ctrl, w, yerr=np.array(spsc_crs), color=COLORS["SPSC-Alg1"],
           label=LABELS["SPSC-Alg1"], capsize=3)
    ax.bar(x,     lin_ctrl,  w, yerr=np.array(lin_crs),  color=COLORS["LinUCB"],
           label=LABELS["LinUCB"], capsize=3)
    ax.bar(x + w, ora_ctrl,  w, yerr=np.array(ora_crs),  color=COLORS["Oracle-LinUCB"],
           label=LABELS["Oracle-LinUCB"], capsize=3)
    ax.set_xticks(x); ax.set_xticklabels(k_labels)
    ax.set_xlabel("$K$ (number of segments)", fontsize=11)
    ax.set_ylabel("Final Control Regret", fontsize=11)
    ax.set_title("(b) Control regret vs. $K$", fontsize=11)
    ax.legend(fontsize=7); ax.yaxis.grid(True, alpha=0.3)

    # Panel (c): Ratios
    ax = axes[2]
    ax.plot(k_vals, ratio_lin, "o-", color=COLORS["SPSC-Alg1"], lw=2,
            label="SPSC / LinUCB")
    ax.plot(k_vals, ratio_ora, "s--", color=COLORS["Oracle-LinUCB"], lw=2,
            label="SPSC / Oracle")
    ax.axhline(1.0, color="gray", ls=":", lw=1)
    for i, k in enumerate(k_vals):
        ax.annotate(f"{ratio_lin[i]:.3f}", (k, ratio_lin[i]),
                    textcoords="offset points", xytext=(0, 8), fontsize=7, ha="center")
    ax.set_xlabel("$K$ (number of segments)", fontsize=11)
    ax.set_ylabel("Regret Ratio", fontsize=11)
    ax.set_title("(c) Regret ratios vs. $K$", fontsize=11)
    ax.legend(fontsize=9); ax.yaxis.grid(True, alpha=0.3)

    fig.suptitle(
        f"Experiment 7: Changepoint Frequency  |  "
        f"$d={D}$, $r={R}$, $T={T}$, $c={PROBE_COST}$, "
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
    k_vals = sorted(sweep.keys())
    print()
    print("=" * 90)
    print("Experiment 7 — Changepoint Frequency Summary")
    print("-" * 90)
    header = (f"{'K':>4}  {'ell':>5}  {'Algorithm':<20}  {'Costed (mean±SE)':>20}  "
              f"{'Control (mean±SE)':>20}  {'SPSC/LinUCB':>11}")
    print(header)
    print("-" * 90)

    for K in k_vals:
        ell = T // K
        finals = {}
        for name in ["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]:
            cost = np.array([r.cumulative_costed_regret[-1]
                             for r in sweep[K][name]])
            ctrl = np.array([r.cumulative_control_regret[-1]
                             for r in sweep[K][name]])
            n = len(cost)
            finals[name] = (cost.mean(), cost.std()/np.sqrt(n),
                            ctrl.mean(), ctrl.std()/np.sqrt(n))

        ratio = finals["SPSC-Alg1"][0] / finals["LinUCB"][0]
        for i, name in enumerate(["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]):
            cm, cs, xm, xs = finals[name]
            k_str = str(K) if i == 0 else ""
            e_str = str(ell) if i == 0 else ""
            r_str = f"{ratio:.3f}" if i == 0 else ""
            print(f"{k_str:>4}  {e_str:>5}  {name:<20}  "
                  f"{cm:>8.0f} ± {cs:>5.0f}       "
                  f"{xm:>8.0f} ± {xs:>5.0f}       {r_str:>11}")
        print()
    print("=" * 90)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Experiment 7: Changepoint Frequency")
    print(f"  d={D}, r={R}, T={T}")
    print(f"  K sweep: {K_VALS}")
    print(f"  n_seeds={N_SEEDS}")
    print("=" * 60)

    sweep = run_sweep(K_VALS, N_SEEDS)
    print_table(sweep)
    make_figure(sweep, os.path.join(OUT_DIR, "experiment7_changepoint_frequency.png"))
    print("\nDone.")
