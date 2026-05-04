"""
Satimage Real-Data: Extended SOTA Comparison (10 methods).

Extends experiment_real_satimage_regime.py by adding:
  8. LowOFUL       (Jun et al. 2019 — stationary low-rank)
  9. VOFUL          (Kim & Paik 2022 — variance-aware low-rank)
 10. SPSC-Adaptive  (Algorithm 4 — no oracle segment boundaries)

Same grid, same parameters, same seeds as the original experiment
so results are directly comparable.

Grid: d in {5, 55, 105, 155}, r in {1, 10, 20, 30}
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

from environments import RealSatimageEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, OracleLinUCB,
    SWLinUCB, RestartLinUCB, LowRankRewardUCB, LowOFUL, VOFUL,
    RunMetrics,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Parameters — IDENTICAL to experiment_real_satimage_regime.py
# ---------------------------------------------------------------------------
N_SEEDS     = 10
SEG_SIZE    = 500
N_SEGMENTS  = 10
PROBE_EVERY = 10
WINDOW      = 400
LAM         = 0.01
DELTA       = 0.05
PROBE_COST  = 0.02

D_VALUES = [5, 55, 105, 155]
R_VALUES = [1, 10, 20, 30]

# All 10 methods
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

# Competitors (exclude oracle and our methods for "best competitor" calculation)
COMPETITORS = ["LinUCB", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB",
               "LowRank-Reward", "LowOFUL", "VOFUL"]


def make_env(seed, d, r):
    return RealSatimageEnvironment(
        d=d, r=r, n_actions=40, segment_size=SEG_SIZE,
        n_segments=N_SEGMENTS, seed=seed * 13 + 7,
    )


def run_cell(d, r):
    """Run all 10 methods on one (d, r) cell."""
    results = {m: [] for m in METHOD_NAMES}

    for seed in range(N_SEEDS):
        # --- SPSC Algorithm 1 (oracle segment boundaries) ---
        env = make_env(seed, d, r)
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
        results["SPSC-Alg1"].append(m.cumulative_control_regret[-1])

        # --- SPSC Adaptive (no oracle boundaries) ---
        env = make_env(seed, d, r)
        m = SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                          window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                          m_relearn=30, det_window=50, cusum_threshold=3.0,
                          warmup=100).run()
        results["SPSC-Adaptive"].append(m.cumulative_control_regret[-1])

        # --- LinUCB ---
        env = make_env(seed, d, r)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000).run()
        results["LinUCB"].append(m.cumulative_control_regret[-1])

        # --- D-LinUCB (discounted) ---
        env = make_env(seed, d, r)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 2000,
                   forgetting_factor=0.998).run()
        results["D-LinUCB"].append(m.cumulative_control_regret[-1])

        # --- SW-LinUCB ---
        env = make_env(seed, d, r)
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                     seed=seed + 3000).run()
        results["SW-LinUCB"].append(m.cumulative_control_regret[-1])

        # --- Oracle LinUCB ---
        env = make_env(seed, d, r)
        m = OracleLinUCB(env, window=10000, lam=LAM, delta=DELTA,
                         seed=seed + 4000).run()
        results["Oracle-LinUCB"].append(m.cumulative_control_regret[-1])

        # --- Restart-LinUCB (periodic, no oracle CPs) ---
        env = make_env(seed, d, r)
        T_env = env.T
        m = RestartLinUCB(env, restart_period=T_env // N_SEGMENTS,
                          lam=LAM, delta=DELTA, seed=seed + 5000).run()
        results["Restart-LinUCB"].append(m.cumulative_control_regret[-1])

        # --- LowRank-Reward ---
        env = make_env(seed, d, r)
        m = LowRankRewardUCB(env, window=WINDOW, pca_warmup=50,
                              lam=LAM, delta=DELTA, seed=seed + 6000).run()
        results["LowRank-Reward"].append(m.cumulative_control_regret[-1])

        # --- LowOFUL (stationary low-rank) ---
        env = make_env(seed, d, r)
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 7000,
                     pca_warmup=30, subspace_update_freq=20).run()
        results["LowOFUL"].append(m.cumulative_control_regret[-1])

        # --- VOFUL (variance-aware low-rank) ---
        env = make_env(seed, d, r)
        m = VOFUL(env, lam=LAM, delta=DELTA, seed=seed + 8000,
                  pca_warmup=30, subspace_update_freq=20).run()
        results["VOFUL"].append(m.cumulative_control_regret[-1])

    return {m: np.array(results[m]) for m in METHOD_NAMES}


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def print_tables(all_results):
    n = N_SEEDS

    for d in D_VALUES:
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                continue

            print()
            print("=" * 130)
            print(f"  d={d}, r={r}   ({n} seeds)")
            print("-" * 130)
            print(f"  {'Method':<30}  {'Mean':>10}  {'Std':>10}  {'SE':>10}  "
                  f"{'vs LinUCB':>10}  {'vs Best':>10}  {'Note':>12}")
            print("-" * 130)

            lin_mean = res["LinUCB"].mean()
            best_comp_mean = min(res[m].mean() for m in COMPETITORS)
            best_method = min(COMPETITORS, key=lambda m: res[m].mean())

            for method in METHOD_NAMES:
                arr = res[method]
                mean = arr.mean()
                std = arr.std()
                se = std / np.sqrt(n)
                vs_lin = mean / max(lin_mean, 1e-8)
                vs_best = mean / max(best_comp_mean, 1e-8)

                if method in ("SPSC-Alg1", "SPSC-Adaptive"):
                    tag = "<<< WINS" if mean < best_comp_mean else ""
                elif method == "Oracle-LinUCB":
                    tag = "(oracle)"
                else:
                    tag = "* best" if method == best_method else ""

                print(f"  {METHOD_LABELS[method]:<30}  {mean:>10.1f}  {std:>10.1f}  "
                      f"{se:>10.1f}  {vs_lin:>10.3f}  {vs_best:>10.3f}  {tag:>12}")

    # Ratio summary
    print("\n" + "=" * 100)
    print("SPSC-Alg1 / LinUCB ratio (* = SPSC wins):")
    header = f"{'d\\\\r':>6}"
    for r in R_VALUES:
        header += f"  {'r='+str(r):>8}"
    print(header)
    print("-" * (6 + 10 * len(R_VALUES)))
    for d in D_VALUES:
        row = f"{d:>6}"
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>8}"
            else:
                ratio = res["SPSC-Alg1"].mean() / max(res["LinUCB"].mean(), 1e-8)
                marker = "*" if ratio < 1.0 else " "
                row += f"  {ratio:>7.3f}{marker}"
        print(row)

    print(f"\nSPSC-Alg1 / Best Competitor ratio:")
    header = f"{'d\\\\r':>6}"
    for r in R_VALUES:
        header += f"  {'r='+str(r):>8}"
    print(header)
    print("-" * (6 + 10 * len(R_VALUES)))
    for d in D_VALUES:
        row = f"{d:>6}"
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>8}"
            else:
                best_comp = min(res[m].mean() for m in COMPETITORS)
                ratio = res["SPSC-Alg1"].mean() / max(best_comp, 1e-8)
                marker = "*" if ratio < 1.0 else " "
                row += f"  {ratio:>7.3f}{marker}"
        print(row)

    # NEW: Show where LowOFUL/VOFUL rank vs SPSC
    print(f"\nStationary low-rank methods (LowOFUL, VOFUL) fail under nonstationarity:")
    header = f"{'d\\\\r':>6}"
    for r in R_VALUES:
        header += f"  {'r='+str(r):>8}"
    print(header)
    print("-" * (6 + 10 * len(R_VALUES)))
    for d in D_VALUES:
        row = f"{d:>6}"
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>8}"
            else:
                loful = res["LowOFUL"].mean()
                spsc = res["SPSC-Alg1"].mean()
                ratio = loful / max(spsc, 1e-8)
                row += f"  {ratio:>7.3f} "
        print(row + "  (LowOFUL / SPSC)")

    for d in D_VALUES:
        row = f"{d:>6}"
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>8}"
            else:
                voful = res["VOFUL"].mean()
                spsc = res["SPSC-Alg1"].mean()
                ratio = voful / max(spsc, 1e-8)
                row += f"  {ratio:>7.3f} "
        print(row + "  (VOFUL / SPSC)")

    print("=" * 100)


# ---------------------------------------------------------------------------
# Bar chart figure
# ---------------------------------------------------------------------------

def make_bar_figure(all_results, out_path):
    """Grouped bar chart for each (d,r) cell where SPSC wins."""
    # Find cells where SPSC beats LinUCB
    winning_cells = []
    for d in D_VALUES:
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                continue
            if res["SPSC-Alg1"].mean() < res["LinUCB"].mean():
                winning_cells.append((d, r))

    if not winning_cells:
        print("No winning cells for bar chart!")
        return

    n_cells = len(winning_cells)
    n_methods = len(METHOD_NAMES)

    fig, axes = plt.subplots(1, min(n_cells, 4), figsize=(6 * min(n_cells, 4), 6),
                             sharey=False)
    if n_cells == 1:
        axes = [axes]

    for ax_idx, (d, r) in enumerate(winning_cells[:4]):
        ax = axes[ax_idx]
        res = all_results[(d, r)]

        means = [res[m].mean() for m in METHOD_NAMES]
        ses = [res[m].std() / np.sqrt(N_SEEDS) for m in METHOD_NAMES]
        colors = [METHOD_COLORS[m] for m in METHOD_NAMES]

        # Sort by mean regret
        order = np.argsort(means)
        y = np.arange(n_methods)

        ax.barh(y, [means[i] for i in order],
                xerr=[ses[i] for i in order],
                color=[colors[i] for i in order],
                capsize=3, height=0.7, edgecolor="black", linewidth=0.3)
        ax.set_yticks(y)
        ax.set_yticklabels([METHOD_LABELS[METHOD_NAMES[i]].split("(")[0].strip()
                            for i in order], fontsize=8)
        ax.set_xlabel("Control Regret", fontsize=10)
        ax.set_title(f"$d={d}$, $r={r}$", fontsize=11, fontweight="bold")
        ax.xaxis.grid(True, alpha=0.3)

    fig.suptitle(
        "Satimage Extended SOTA: SPSC Winning Configurations\n"
        f"$K={N_SEGMENTS}$, $T=5000$, probe_every={PROBE_EVERY}, "
        f"$\\lambda={LAM}$  ({N_SEEDS} seeds)",
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
    print("Satimage Extended SOTA (10 methods)")
    print(f"  d = {D_VALUES}")
    print(f"  r = {R_VALUES}")
    print(f"  lam={LAM}, probe_every={PROBE_EVERY}, window={WINDOW}")
    print(f"  N_SEEDS={N_SEEDS}, SEG_SIZE={SEG_SIZE}, N_SEGMENTS={N_SEGMENTS}")
    print("=" * 80)

    all_results = {}
    total_cells = len(D_VALUES) * len(R_VALUES)
    cell_idx = 0

    for d in D_VALUES:
        for r in R_VALUES:
            cell_idx += 1
            if r >= d:
                print(f"\n[{cell_idx}/{total_cells}] d={d}, r={r} -- SKIPPED (r >= d)")
                all_results[(d, r)] = None
                continue

            t0 = time.time()
            print(f"\n[{cell_idx}/{total_cells}] Running d={d}, r={r} "
                  f"(10 methods x {N_SEEDS} seeds) ...", flush=True)

            res = run_cell(d, r)
            elapsed = time.time() - t0
            all_results[(d, r)] = res

            spsc_m = res["SPSC-Alg1"].mean()
            adapt_m = res["SPSC-Adaptive"].mean()
            lin_m = res["LinUCB"].mean()
            loful_m = res["LowOFUL"].mean()
            voful_m = res["VOFUL"].mean()
            winner = "SPSC" if spsc_m < lin_m else "LinUCB"

            print(f"  DONE in {elapsed:.1f}s")
            print(f"    SPSC={spsc_m:.0f}  Adaptive={adapt_m:.0f}  "
                  f"Lin={lin_m:.0f}  LowOFUL={loful_m:.0f}  VOFUL={voful_m:.0f}")
            print(f"    SPSC/Lin={spsc_m/max(lin_m,1):.3f}  [{winner}]")
            sys.stdout.flush()

    print_tables(all_results)
    make_bar_figure(all_results,
                    os.path.join(OUT_DIR, "experiment_satimage_extended.png"))
    print("\nDone.")
