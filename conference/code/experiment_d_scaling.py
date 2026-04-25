"""
Empirical d-scaling of SPSC regret (Reviewer 1 / Reviewer 2 Q1).

Theory says probe term is $\\tilde O(d^{2/3}\\,K^{1/3}\\,T^{2/3})$ —
predicted slope 2/3 in log(regret) vs log(d).
Question: is the empirical slope actually 2/3, or smaller?

Setting: synthetic piecewise low-rank LDS with fixed r, K, T, varying d.
Plots SPSC's regret-above-exploitation-floor on log-log axes and reports
the empirical exponent obtained by least-squares linear fit.
"""

import os, sys, json, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import RealPendigitsEnvironment
from algorithm import SPSC_Algorithm1, LinUCB

OUT_DIR     = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(OUT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
RESULTS_PATH = os.path.join(RESULTS_DIR, "experiment_d_scaling.json")
FIGURE_PATH  = os.path.join(OUT_DIR, "experiment_d_scaling.png")

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
# Sweep d at fixed r, K, T.  Pendigits supports d up to ~256 after random
# projection.  We use Pendigits because it's an existing real-data env;
# the d-scaling pattern should be intrinsic to SPSC, not env-specific.
D_VALUES   = [10, 20, 30, 50, 70, 90, 110, 130, 160, 200]
R          = 10
N_SEEDS    = 5     # bigger T sweep => fewer seeds, tighten if you want
T_TOTAL    = 5000
SEG_SIZE   = 500
N_SEGMENTS = 10
PROBE_EVERY = 10
PROBE_COST = 0.02
WINDOW     = 400
LAM        = 0.01
DELTA      = 0.05


def make_env(seed, d):
    return RealPendigitsEnvironment(
        d=d, r=R, n_actions=40, segment_size=SEG_SIZE,
        n_segments=N_SEGMENTS, seed=seed * 13 + 7,
    )


def run_spsc(d, seed):
    env = make_env(seed, d)
    spsc = SPSC_Algorithm1(
        env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
        window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
        normalize_gamma_by_d=True,
    )
    return float(spsc.run().cumulative_control_regret[-1])


def run_linucb(d, seed):
    env = make_env(seed, d)
    lin = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000)
    return float(lin.run().cumulative_control_regret[-1])


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    print("=" * 80)
    print(f"d-scaling sweep: Pendigits, r={R}, K={N_SEGMENTS}, T={T_TOTAL}, seeds={N_SEEDS}")
    print(f"  d in {D_VALUES}")
    print("=" * 80)

    results = {"d": D_VALUES, "spsc": {}, "linucb": {}}

    for d in D_VALUES:
        spsc_rs, lin_rs = [], []
        t_d = time.time()
        for seed in range(N_SEEDS):
            t0 = time.time()
            spsc_r = run_spsc(d, seed)
            spsc_rs.append(spsc_r)
            lin_r = run_linucb(d, seed)
            lin_rs.append(lin_r)
            print(f"  d={d:>3d}  seed {seed+1}/{N_SEEDS}: "
                  f"SPSC={spsc_r:>7.0f}  LinUCB={lin_r:>7.0f}  "
                  f"[{time.time()-t0:.1f}s]", flush=True)
        results["spsc"][str(d)] = spsc_rs
        results["linucb"][str(d)] = lin_rs
        print(f"  -- d={d} done in {time.time()-t_d:.1f}s "
              f"(SPSC mean {np.mean(spsc_rs):.0f}, "
              f"LinUCB mean {np.mean(lin_rs):.0f})", flush=True)

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {RESULTS_PATH}")

    fit_and_plot(results)


# --------------------------------------------------------------------------
# Fit and plot
# --------------------------------------------------------------------------
def fit_and_plot(results):
    d_arr      = np.array(results["d"], dtype=float)
    spsc_means = np.array([np.mean(results["spsc"][str(int(d))]) for d in d_arr])
    spsc_ses   = np.array([np.std(results["spsc"][str(int(d))])
                            / np.sqrt(len(results["spsc"][str(int(d))]))
                            for d in d_arr])
    lin_means  = np.array([np.mean(results["linucb"][str(int(d))]) for d in d_arr])

    # Estimated exploitation floor: r * sqrt(K*T) (proxy, ignores log factors)
    expl_floor = R * np.sqrt(N_SEGMENTS * T_TOTAL)

    # Residual = total SPSC regret - exploitation floor.
    # The remaining d-dependence should come from the probe term ~ d^{2/3}.
    residual = np.maximum(spsc_means - expl_floor, 1.0)  # avoid log(neg)

    # Log-log linear fit: log(residual) = a * log(d) + b
    log_d, log_res = np.log(d_arr), np.log(residual)
    a_emp, b_emp = np.polyfit(log_d, log_res, 1)
    print(f"\nEmpirical exponent (residual): a = {a_emp:.3f}  "
          f"(theory predicts 2/3 ≈ 0.667)")

    # Also fit raw SPSC means
    log_spsc = np.log(spsc_means)
    a_raw, b_raw = np.polyfit(log_d, log_spsc, 1)
    print(f"Empirical exponent (raw SPSC):  a = {a_raw:.3f}")

    # ----------------------------------------------------------------------
    # Two-panel plot: log-log scaling + SPSC vs LinUCB
    # ----------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # --- Panel 1: log-log of residual vs d, with theory and fit lines ---
    ax = axes[0]
    ax.errorbar(d_arr, residual, yerr=spsc_ses, fmt="o", capsize=4,
                color="#1f77b4", label="SPSC residual (mean ± SE)",
                markersize=8, markeredgecolor="black", markeredgewidth=0.8)
    # Empirical fit
    d_grid = np.linspace(d_arr.min(), d_arr.max(), 100)
    ax.plot(d_grid, np.exp(b_emp) * d_grid ** a_emp,
            "--", color="#1f77b4", linewidth=2,
            label=f"Empirical fit: $d^{{{a_emp:.2f}}}$")
    # Theory line: anchor to first point, plot d^{2/3}
    c_theory = residual[0] / d_arr[0] ** (2/3)
    ax.plot(d_grid, c_theory * d_grid ** (2/3),
            ":", color="#d62728", linewidth=2,
            label=r"Theory: $d^{2/3}$")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("$d$ (ambient dimension)", fontsize=13, fontweight="bold")
    ax.set_ylabel(r"Residual = SPSC regret $- r\sqrt{KT}$",
                  fontsize=13, fontweight="bold")
    ax.set_title("Empirical $d$-scaling of probe-term residual",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=11, loc="upper left")
    ax.grid(True, which="both", alpha=0.35)

    # --- Panel 2: SPSC vs LinUCB on linear axes ---
    ax = axes[1]
    ax.errorbar(d_arr, spsc_means, yerr=spsc_ses, fmt="o-", capsize=4,
                color="#1f77b4", label="SPSC", linewidth=2, markersize=7)
    ax.plot(d_arr, lin_means, "s--", color="#d62728",
            label="LinUCB", linewidth=2, markersize=7)
    ax.set_xlabel("$d$", fontsize=13, fontweight="bold")
    ax.set_ylabel("Control regret", fontsize=13, fontweight="bold")
    ax.set_title(f"SPSC vs LinUCB at $r{{=}}{R}$, $K{{=}}{N_SEGMENTS}$, $T{{=}}{T_TOTAL}$",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.35)

    fig.suptitle(
        f"Pendigits $d$-scaling: empirical exponent $\\approx{a_emp:.2f}$ "
        f"(theoretical bound $2/3$)",
        fontsize=15, fontweight="bold", y=1.02,
    )
    plt.tight_layout()
    plt.savefig(FIGURE_PATH, dpi=180, bbox_inches="tight")
    print(f"Saved: {FIGURE_PATH}")
    print(f"\nReport these in proposed_additions.tex:")
    print(f"  empirical exponent a = {a_emp:.3f}  (theory: 0.667)")
    print(f"  raw SPSC slope:    a = {a_raw:.3f}")


if __name__ == "__main__":
    main()
