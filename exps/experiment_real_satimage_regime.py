"""
Satimage Real-Data Operating Regime Study with 7 methods.

Grid: d in {5, 55, 105, 155}, r in {1, 10, 20, 30}
Methods:
  1. SPSC Algorithm 1       (ours, probe + r-dim UCB)
  2. LinUCB                 (stationary ridge UCB, full d)
  3. D-LinUCB               (discounted ridge UCB)
  4. SW-LinUCB              (sliding-window ridge UCB)
  5. Restart-LinUCB         (periodic restart, NO oracle CPs)
  6. LowRank-Reward-UCB     (subspace from rewards, r-dim)
  7. Oracle-LinUCB          (known subspace, r-dim UCB)

Outputs:
  - Detailed table with mean +- std for all 7 methods at each (d,r)
  - SPSC/LinUCB and SPSC/Best ratio tables
  - Double-ring figure: (a) SPSC/LinUCB, (b) SPSC/Best Competitor
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

from environments import RealSatimageEnvironment
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB, RunMetrics, SWLinUCB, RestartLinUCB, LowRankRewardUCB

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Fixed parameters
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

METHOD_NAMES = [
    "Oracle-LinUCB",
    "SPSC-Alg1",
    "LowRank-Reward",
    "SW-LinUCB",
    "D-LinUCB",
    "Restart-LinUCB",
    "LinUCB",
]

METHOD_LABELS = {
    "Oracle-LinUCB":    "Oracle (Jun+ '19)",
    "SPSC-Alg1":        "SPSC (ours)",
    "LowRank-Reward":   "LowRank-Reward",
    "SW-LinUCB":        "SW-LinUCB (Cheung+ '19)",
    "D-LinUCB":         "D-LinUCB (Russac+ '19)",
    "Restart-LinUCB":   "Restart-LinUCB (Auer+ '19)",
    "LinUCB":           "LinUCB (Abbasi+ '11)",
}

NON_ORACLE_ALL = ["LinUCB", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB", "LowRank-Reward"]


def make_env(seed, d, r):
    return RealSatimageEnvironment(
        d=d, r=r, n_actions=40, segment_size=SEG_SIZE,
        n_segments=N_SEGMENTS, seed=seed * 13 + 7,
    )


def run_cell(d, r):
    """Run all 7 methods on one (d, r) cell. Returns per-seed arrays."""
    results = {m: [] for m in METHOD_NAMES}

    for seed in range(N_SEEDS):
        env = make_env(seed, d, r)
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
        results["SPSC-Alg1"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000).run()
        results["LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 2000,
                   forgetting_factor=0.998).run()
        results["D-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                     seed=seed + 3000).run()
        results["SW-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = OracleLinUCB(env, window=10000, lam=LAM, delta=DELTA,
                         seed=seed + 4000).run()
        results["Oracle-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        T_env = env.T
        m = RestartLinUCB(env, restart_period=T_env // N_SEGMENTS,
                          lam=LAM, delta=DELTA, seed=seed + 5000).run()
        results["Restart-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = LowRankRewardUCB(env, window=WINDOW, pca_warmup=50,
                              lam=LAM, delta=DELTA, seed=seed + 6000).run()
        results["LowRank-Reward"].append(m.cumulative_control_regret[-1])

    return {m: np.array(results[m]) for m in METHOD_NAMES}


# ---------------------------------------------------------------------------
# Double ring figure
# ---------------------------------------------------------------------------

def make_ring(ax, ratio_grid, title, d_grid, r_grid, cbar_ax=None, fig=None):
    n_d, n_r = len(d_grid), len(r_grid)
    sector_width = 2 * np.pi / n_d
    angles = np.linspace(0, 2 * np.pi, n_d, endpoint=False)

    valid = ratio_grid[~np.isnan(ratio_grid)]
    vmin = min(0.50, valid.min() - 0.02) if len(valid) > 0 else 0.5
    vmax = max(1.25, valid.max() + 0.02) if len(valid) > 0 else 1.25
    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)
    cmap = plt.cm.RdBu_r

    ring_inner = 0.3
    ring_width = 0.18

    for i, r in enumerate(r_grid):
        r_bottom = ring_inner + i * ring_width
        r_height = ring_width * 0.90

        for j, d in enumerate(d_grid):
            angle = angles[j]
            val = ratio_grid[i, j]

            if np.isnan(val) or r >= d:
                color = "#e0e0e0"
                val_text = ""
            else:
                color = cmap(norm(val))
                val_text = f"{val:.2f}"

            ax.bar(angle, r_height, width=sector_width * 0.90,
                   bottom=r_bottom, color=color,
                   edgecolor="white", linewidth=1.5)

            text_r = r_bottom + r_height / 2
            txt_color = "white" if not np.isnan(val) and r < d and abs(val - 1.0) > 0.15 else "#333333"
            rot = np.degrees(angle) - 90 if angle < np.pi else np.degrees(angle) + 90
            ax.text(angle, text_r, val_text,
                    ha="center", va="center", fontsize=7.5,
                    fontweight="bold", color=txt_color, rotation=rot)

    for i, r in enumerate(r_grid):
        r_center = ring_inner + i * ring_width + ring_width * 0.45
        ax.text(np.pi * 1.08, r_center, f"$r$={r}",
                ha="center", va="center", fontsize=9.5, fontweight="bold",
                color="#333333",
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="gray",
                          alpha=0.9, lw=0.6))

    outer_r = ring_inner + n_r * ring_width + 0.05
    for j, d in enumerate(d_grid):
        ax.text(angles[j], outer_r, f"$d$={d}",
                ha="center", va="center", fontsize=10, fontweight="bold")

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(0, ring_inner + n_r * ring_width + 0.13)
    ax.grid(False)
    ax.spines['polar'].set_visible(False)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=22, y=1.03)

    if cbar_ax is not None and fig is not None:
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cbar_ax, aspect=25)
        cbar.set_label("Regret ratio", fontsize=10, labelpad=6)
        cbar.ax.axhline(1.0, color="black", lw=2)
        cbar.ax.tick_params(labelsize=9)


def make_double_rings(all_results, out_path):
    n_r, n_d = len(R_VALUES), len(D_VALUES)

    ratio_vs_lin = np.full((n_r, n_d), np.nan)
    ratio_vs_best = np.full((n_r, n_d), np.nan)

    for i, r_val in enumerate(R_VALUES):
        for j, d_val in enumerate(D_VALUES):
            res = all_results.get((d_val, r_val))
            if res is None or r_val >= d_val:
                continue
            spsc = res["SPSC-Alg1"].mean()
            lin = res["LinUCB"].mean()
            ratio_vs_lin[i, j] = spsc / max(lin, 1e-8)

            best_reg = min(res[m].mean() for m in NON_ORACLE_ALL)
            ratio_vs_best[i, j] = spsc / max(best_reg, 1e-8)

    plt.rcParams.update({
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.linewidth": 1.2,
    })

    fig = plt.figure(figsize=(16, 7.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.05], wspace=0.15)

    ax1 = fig.add_subplot(gs[0], polar=True)
    ax2 = fig.add_subplot(gs[1], polar=True)
    cbar_ax = fig.add_subplot(gs[2])

    make_ring(ax1, ratio_vs_lin,
              "(a) SPSC / LinUCB", D_VALUES, R_VALUES)
    make_ring(ax2, ratio_vs_best,
              "(b) SPSC / Best Competitor",
              D_VALUES, R_VALUES,
              cbar_ax=cbar_ax, fig=fig)

    fig.suptitle(
        r"$\mathbf{Satimage\ Operating\!-\!Regime\ Study}$  (Real Data)"
        f"\n$K\\!=\\!{N_SEGMENTS}$,  $T\\!=\\!5,000$,  "
        f"probe\\_every$\\!=\\!{PROBE_EVERY}$,  "
        f"$\\lambda\\!=\\!{LAM}$   "
        f"({N_SEEDS} seeds / cell)",
        fontsize=13, y=1.02,
    )

    plt.savefig(out_path, bbox_inches="tight", dpi=200)
    print(f"Saved: {out_path}")


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
            print("=" * 120)
            print(f"  d={d}, r={r}   ({n} seeds)")
            print("-" * 120)
            print(f"  {'Method':<30}  {'Mean':>10}  {'Std':>10}  {'SE':>10}  "
                  f"{'vs LinUCB':>10}  {'vs Best':>10}  {'Winner?':>8}")
            print("-" * 120)

            lin_mean = res["LinUCB"].mean()
            best_comp_mean = min(res[m].mean() for m in NON_ORACLE_ALL)
            best_method = min(NON_ORACLE_ALL, key=lambda m: res[m].mean())

            for method in METHOD_NAMES:
                arr = res[method]
                mean = arr.mean()
                std = arr.std()
                se = std / np.sqrt(n)
                vs_lin = mean / max(lin_mean, 1e-8)
                vs_best = mean / max(best_comp_mean, 1e-8)

                if method == "SPSC-Alg1":
                    tag = "<<<" if mean < best_comp_mean else ""
                elif method == "Oracle-LinUCB":
                    tag = "(oracle)"
                else:
                    tag = "* best" if method == best_method else ""

                print(f"  {METHOD_LABELS[method]:<30}  {mean:>10.1f}  {std:>10.1f}  "
                      f"{se:>10.1f}  {vs_lin:>10.3f}  {vs_best:>10.3f}  {tag:>8}")

    # Ratio summary tables
    print("\n" + "=" * 100)
    print("SPSC / LinUCB ratio (mean over seeds, < 1 = SPSC wins):")
    header = f"{'d\\r':>6}"
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

    print(f"\nSPSC / Best Competitor ratio (mean over seeds):")
    header = f"{'d\\r':>6}"
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
                best_comp = min(res[m].mean() for m in NON_ORACLE_ALL)
                ratio = res["SPSC-Alg1"].mean() / max(best_comp, 1e-8)
                marker = "*" if ratio < 1.0 else " "
                row += f"  {ratio:>7.3f}{marker}"
        print(row)

    print("=" * 100)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 80)
    print("Satimage Real-Data Operating Regime (7 methods)")
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
                  f"(7 methods x {N_SEEDS} seeds) ...", flush=True)

            res = run_cell(d, r)
            elapsed = time.time() - t0
            all_results[(d, r)] = res

            spsc_m = res["SPSC-Alg1"].mean()
            lin_m = res["LinUCB"].mean()
            spsc_r = spsc_m / max(lin_m, 1e-8)
            best_comp = min(res[m].mean() for m in NON_ORACLE_ALL)
            spsc_best = spsc_m / max(best_comp, 1e-8)
            winner = "SPSC" if spsc_m < lin_m else "LinUCB"

            print(f"  DONE in {elapsed:.1f}s")
            print(f"    SPSC={spsc_m:.0f}+-{res['SPSC-Alg1'].std():.0f}  "
                  f"Lin={lin_m:.0f}+-{res['LinUCB'].std():.0f}  "
                  f"Oracle={res['Oracle-LinUCB'].mean():.0f}")
            print(f"    SPSC/Lin={spsc_r:.3f}  SPSC/Best={spsc_best:.3f}  [{winner}]")
            sys.stdout.flush()

    # Print all tables
    print_tables(all_results)

    # Generate double-rings figure
    make_double_rings(all_results,
                      os.path.join(OUT_DIR, "experiment_real_satimage_double_rings.png"))
    print("Done.")
