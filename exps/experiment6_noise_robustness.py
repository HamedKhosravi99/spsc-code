"""
Experiment 6: Noise Robustness

Sweeps observation noise sigma_eps over {0.05, 0.10, 0.20, 0.30, 0.50, 0.80}
with all other parameters fixed at reference values.

Outputs
-------
  experiment6_noise_robustness.png  — 2-panel figure
    (a) Final control regret vs sigma_eps
    (b) SPSC/LinUCB and SPSC/Oracle ratios vs sigma_eps
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
K           = 4
T           = 6000
PROBE_EVERY = 30
PROBE_COST  = 0.1
WINDOW      = 100
N_SEEDS     = 10

SIGMA_VALS = [0.05, 0.10, 0.20, 0.30, 0.50, 0.80]

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

def make_env(sigma_eps, seed):
    return LowRankLDSEnvironment(d=D, r=R, K=K, T=T,
                                  sigma_eps=sigma_eps, seed=seed * 100)


def run_sweep(sigma_vals, n_seeds):
    sweep = {}
    for sig in sigma_vals:
        names = ["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]
        results = {n: [] for n in names}
        for seed in range(n_seeds):
            print(f"  sigma={sig}, seed {seed+1}/{n_seeds}", end="\r", flush=True)

            env = make_env(sig, seed)
            results["SPSC-Alg1"].append(
                SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                                window=WINDOW, lam=1.0, delta=0.05, seed=seed).run()
            )
            env = make_env(sig, seed)
            results["LinUCB"].append(
                LinUCB(env, lam=1.0, delta=0.05, seed=seed + 1000).run()
            )
            env = make_env(sig, seed)
            results["Oracle-LinUCB"].append(
                OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                             seed=seed + 2000).run()
            )
        sweep[sig] = results
    print(flush=True)
    return sweep


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(sweep, out_path):
    sigmas = sorted(sweep.keys())

    spsc_means, lin_means, ora_means = [], [], []
    spsc_ses, lin_ses, ora_ses = [], [], []

    for sig in sigmas:
        for name, store_m, store_s in [
            ("SPSC-Alg1", spsc_means, spsc_ses),
            ("LinUCB", lin_means, lin_ses),
            ("Oracle-LinUCB", ora_means, ora_ses),
        ]:
            finals = np.array([r.cumulative_control_regret[-1]
                               for r in sweep[sig][name]])
            store_m.append(finals.mean())
            store_s.append(finals.std() / np.sqrt(len(finals)))

    spsc_means = np.array(spsc_means)
    lin_means  = np.array(lin_means)
    ora_means  = np.array(ora_means)
    spsc_ses   = np.array(spsc_ses)
    lin_ses    = np.array(lin_ses)
    ora_ses    = np.array(ora_ses)

    ratio_lin = spsc_means / lin_means
    ratio_ora = spsc_means / ora_means

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.subplots_adjust(wspace=0.30)

    # Panel (a): Final control regret vs sigma
    ax = axes[0]
    x = np.arange(len(sigmas))
    w = 0.25
    ax.bar(x - w, spsc_means, w, yerr=spsc_ses, color=COLORS["SPSC-Alg1"],
           label=LABELS["SPSC-Alg1"], capsize=3)
    ax.bar(x,     lin_means,  w, yerr=lin_ses,  color=COLORS["LinUCB"],
           label=LABELS["LinUCB"], capsize=3)
    ax.bar(x + w, ora_means,  w, yerr=ora_ses,  color=COLORS["Oracle-LinUCB"],
           label=LABELS["Oracle-LinUCB"], capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels([str(s) for s in sigmas])
    ax.set_xlabel(r"$\sigma_\varepsilon$", fontsize=11)
    ax.set_ylabel("Final Control Regret", fontsize=11)
    ax.set_title("(a) Final control regret vs. noise level", fontsize=11)
    ax.legend(fontsize=8)
    ax.yaxis.grid(True, alpha=0.3)

    # Panel (b): Ratios
    ax = axes[1]
    ax.plot(sigmas, ratio_lin, "o-", color=COLORS["SPSC-Alg1"], lw=2,
            label="SPSC / LinUCB")
    ax.plot(sigmas, ratio_ora, "s--", color=COLORS["Oracle-LinUCB"], lw=2,
            label="SPSC / Oracle")
    ax.axhline(1.0, color="gray", ls=":", lw=1)
    ax.set_xlabel(r"$\sigma_\varepsilon$", fontsize=11)
    ax.set_ylabel("Regret Ratio", fontsize=11)
    ax.set_title("(b) SPSC / LinUCB and SPSC / Oracle ratios", fontsize=11)
    ax.legend(fontsize=9)
    ax.yaxis.grid(True, alpha=0.3)

    fig.suptitle(
        f"Experiment 6: Noise Robustness  |  "
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
    sigmas = sorted(sweep.keys())
    print()
    print("=" * 80)
    print("Experiment 6 — Noise Robustness Summary")
    print("-" * 80)
    header = (f"{'sigma':>6}  {'Algorithm':<20}  {'Control (mean±SE)':>20}  "
              f"{'Costed (mean±SE)':>20}  {'SPSC/LinUCB':>11}  {'SPSC/Oracle':>11}")
    print(header)
    print("-" * 80)

    for sig in sigmas:
        finals = {}
        for name in ["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]:
            ctrl = np.array([r.cumulative_control_regret[-1]
                             for r in sweep[sig][name]])
            cost = np.array([r.cumulative_costed_regret[-1]
                             for r in sweep[sig][name]])
            finals[name] = (ctrl.mean(), ctrl.std() / np.sqrt(len(ctrl)),
                            cost.mean(), cost.std() / np.sqrt(len(cost)))

        ratio_l = finals["SPSC-Alg1"][0] / finals["LinUCB"][0]
        ratio_o = finals["SPSC-Alg1"][0] / finals["Oracle-LinUCB"][0]

        for i, name in enumerate(["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]):
            cm, cs, xm, xs = finals[name]
            sig_str = f"{sig:.2f}" if i == 0 else ""
            rl = f"{ratio_l:.3f}" if i == 0 else ""
            ro = f"{ratio_o:.3f}" if i == 0 else ""
            print(f"{sig_str:>6}  {name:<20}  {cm:>8.0f} ± {cs:>5.0f}       "
                  f"{xm:>8.0f} ± {xs:>5.0f}       {rl:>11}  {ro:>11}")
        print()

    print("=" * 80)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Experiment 6: Noise Robustness")
    print(f"  d={D}, r={R}, K={K}, T={T}")
    print(f"  sigma_eps sweep: {SIGMA_VALS}")
    print(f"  n_seeds={N_SEEDS}")
    print("=" * 60)

    sweep = run_sweep(SIGMA_VALS, N_SEEDS)
    print_table(sweep)
    make_figure(sweep, os.path.join(OUT_DIR, "experiment6_noise_robustness.png"))
    print("\nDone.")
