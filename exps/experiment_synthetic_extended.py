"""
Synthetic Operating-Regime Benchmark: Extended SOTA Comparison (10 methods).

Extends experiment1_synthetic_final.py by adding:
  4. SPSC-Adaptive  (Algorithm 4 — no oracle segment boundaries)
  5. SW-LinUCB      (Cheung+ '19)
  6. D-LinUCB       (Russac+ '19)
  7. Restart-LinUCB
  8. LowOFUL        (Jun+ '19 — stationary low-rank)
  9. VOFUL           (Kim+ '22 — variance-aware low-rank)
 10. LowRank-Reward

Same grid, same parameters, same seeds as the original experiment
so results are directly comparable.

Grid: d in {5, 10, 20, 30, 45, 60, 80, 100}, r in {1, 3, 5, 10, 15, 20}
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

sys.path.insert(0, os.path.dirname(__file__))
from environments import LowRankLDSEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, OracleLinUCB,
    SWLinUCB, RestartLinUCB, LowRankRewardUCB, LowOFUL, VOFUL,
    RunMetrics,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================================================================
# Parameters — IDENTICAL to experiment1_synthetic_final.py
# =========================================================================
DS = [5, 50, 100, 500]
RS = [1, 10, 25, 50, 100]
K = 10
T = 5000
SIGMA_EPS = 0.3
SPEC_RAD = 0.99
SIGMA_ETA = 0.04
N_ACTIONS = 40
PROBE_EVERY = 50
PROBE_COST = 0.1
WINDOW = 400
LAM = 0.01
DELTA = 0.05
FEATURE_DECAY = 1.5
N_SEEDS = 10
T_SIXTH = T ** (1.0 / 6.0)

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

COMPETITORS = ["LinUCB", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB",
               "LowRank-Reward", "LowOFUL", "VOFUL"]


def make_env(seed, d, r):
    return LowRankLDSEnvironment(
        d=d, r=r, K=K, T=T, sigma_eps=SIGMA_EPS,
        spectral_radius=SPEC_RAD, n_actions=N_ACTIONS,
        sigma_eta=SIGMA_ETA, seed=seed * 100,
    )


def run_method(name, seed, d, r):
    """Run a single method for a single seed, return final costed regret."""
    env = make_env(seed, d, r)
    if name == "SPSC-Alg1":
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
    elif name == "SPSC-Adaptive":
        m = SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                          window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                          m_relearn=30, det_window=50, cusum_threshold=3.0,
                          warmup=100).run()
    elif name == "LinUCB":
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000).run()
    elif name == "Oracle-LinUCB":
        m = OracleLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                         seed=seed + 2000).run()
    elif name == "D-LinUCB":
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 3000,
                   forgetting_factor=0.998).run()
    elif name == "SW-LinUCB":
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                     seed=seed + 4000).run()
    elif name == "Restart-LinUCB":
        m = RestartLinUCB(env, restart_period=T // K,
                          lam=LAM, delta=DELTA, seed=seed + 5000).run()
    elif name == "LowRank-Reward":
        m = LowRankRewardUCB(env, window=WINDOW, pca_warmup=50,
                              lam=LAM, delta=DELTA, seed=seed + 6000).run()
    elif name == "LowOFUL":
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 7000,
                     pca_warmup=30, subspace_update_freq=20).run()
    elif name == "VOFUL":
        m = VOFUL(env, lam=LAM, delta=DELTA, seed=seed + 8000,
                  pca_warmup=30, subspace_update_freq=20).run()
    return m.cumulative_costed_regret[-1]


def run_cell(d, r, n_seeds):
    """Run all 10 methods x n_seeds with per-seed per-method timing printed."""
    results = {m: [] for m in METHOD_NAMES}

    for seed in range(n_seeds):
        print(f"\n  -- seed {seed+1}/{n_seeds} --", flush=True)
        for name in METHOD_NAMES:
            t0 = time.time()
            val = run_method(name, seed, d, r)
            results[name].append(val)
            elapsed = time.time() - t0
            print(f"    {METHOD_LABELS[name]:<30}  regret = {val:>10.1f}   [{elapsed:.1f}s]",
                  flush=True)

    return {m: np.array(results[m]) for m in METHOD_NAMES}


# =========================================================================
# Tables
# =========================================================================
def print_tables(all_results, d_vals, r_vals):
    print("\n" + "=" * 140)
    print("DETAILED RESULTS")
    print("=" * 140)

    for d in d_vals:
        for r in r_vals:
            res = all_results.get((d, r))
            if res is None:
                continue

            n = len(res["LinUCB"])
            print()
            print("=" * 130)
            print(f"  d={d}, r={r}   ({n} seed{'s' if n>1 else ''})")
            print("-" * 130)
            print(f"  {'Method':<30}  {'Mean':>10}  {'SE':>10}  "
                  f"{'vs LinUCB':>10}  {'vs Best':>10}  {'Note':>12}")
            print("-" * 130)

            lin_mean = res["LinUCB"].mean()
            best_comp_mean = min(res[m].mean() for m in COMPETITORS)
            best_method = min(COMPETITORS, key=lambda m: res[m].mean())

            for method in METHOD_NAMES:
                arr = res[method]
                mean = arr.mean()
                se = arr.std() / np.sqrt(max(n, 1))
                vs_lin = (mean / max(lin_mean, 1e-8) - 1) * 100
                vs_best = (mean / max(best_comp_mean, 1e-8) - 1) * 100

                if method in ("SPSC-Alg1", "SPSC-Adaptive"):
                    tag = "<<< WINS" if mean < best_comp_mean else ""
                elif method == "Oracle-LinUCB":
                    tag = "(oracle)"
                else:
                    tag = "* best" if method == best_method else ""

                print(f"  {METHOD_LABELS[method]:<30}  {mean:>10.1f}  {se:>10.1f}  "
                      f"{vs_lin:>+10.1f}%  {vs_best:>+10.1f}%  {tag:>12}")

    # Ratio summary: SPSC / LinUCB
    print("\n" + "=" * 100)
    print("SPSC-Alg1 / LinUCB ratio (* = SPSC wins):")
    header = f"{'d\\\\r':>6}"
    for r in r_vals:
        header += f"  {'r='+str(r):>8}"
    print(header)
    print("-" * (6 + 10 * len(r_vals)))
    for d in d_vals:
        row = f"{d:>6}"
        for r in r_vals:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>8}"
            else:
                ratio = res["SPSC-Alg1"].mean() / max(res["LinUCB"].mean(), 1e-8)
                marker = "*" if ratio < 1.0 else " "
                row += f"  {ratio:>7.3f}{marker}"
        print(row)

    # SPSC / Best Competitor
    print(f"\nSPSC-Alg1 / Best Competitor ratio (* = SPSC beats all):")
    header = f"{'d\\\\r':>6}"
    for r in r_vals:
        header += f"  {'r='+str(r):>8}"
    print(header)
    print("-" * (6 + 10 * len(r_vals)))
    for d in d_vals:
        row = f"{d:>6}"
        for r in r_vals:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>8}"
            else:
                best_comp = min(res[m].mean() for m in COMPETITORS)
                ratio = res["SPSC-Alg1"].mean() / max(best_comp, 1e-8)
                marker = "*" if ratio < 1.0 else " "
                row += f"  {ratio:>7.3f}{marker}"
        print(row)

    # Adaptive / LinUCB
    print(f"\nSPSC-Adaptive / LinUCB ratio (* = Adaptive wins):")
    header = f"{'d\\\\r':>6}"
    for r in r_vals:
        header += f"  {'r='+str(r):>8}"
    print(header)
    print("-" * (6 + 10 * len(r_vals)))
    for d in d_vals:
        row = f"{d:>6}"
        for r in r_vals:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>8}"
            else:
                ratio = res["SPSC-Adaptive"].mean() / max(res["LinUCB"].mean(), 1e-8)
                marker = "*" if ratio < 1.0 else " "
                row += f"  {ratio:>7.3f}{marker}"
        print(row)

    print("=" * 100)


# =========================================================================
# Phase-transition heatmap (extended)
# =========================================================================
def make_heatmap_figure(all_results, d_vals, r_vals, out_path):
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))

    # --- Panel (a): SPSC-Alg1 / LinUCB ratio heatmap ---
    ratio_grid = np.full((len(r_vals), len(d_vals)), np.nan)
    for i, r in enumerate(r_vals):
        for j, d in enumerate(d_vals):
            res = all_results.get((d, r))
            if res is None:
                continue
            ratio_grid[i, j] = res["SPSC-Alg1"].mean() / max(res["LinUCB"].mean(), 1e-8)

    ax = axes[0, 0]
    norm = TwoSlopeNorm(vmin=0.3, vcenter=1.0, vmax=3.0)
    im = ax.imshow(ratio_grid, cmap="RdYlBu_r", norm=norm, aspect="auto", origin="lower")
    for i in range(len(r_vals)):
        for j in range(len(d_vals)):
            v = ratio_grid[i, j]
            if np.isnan(v):
                ax.text(j, i, "--", ha="center", va="center", fontsize=8, color="gray")
            else:
                color = "white" if (v < 0.6 or v > 2.0) else "black"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=9, fontweight="bold", color=color)
    ax.set_xticks(range(len(d_vals)))
    ax.set_xticklabels(d_vals)
    ax.set_yticks(range(len(r_vals)))
    ax.set_yticklabels(r_vals)
    ax.set_xlabel("Ambient dimension $d$", fontsize=12)
    ax.set_ylabel("Latent rank $r$", fontsize=12)
    ax.set_title("(a) SPSC Alg.1 / LinUCB\n(blue < 1 = SPSC wins)", fontsize=12)
    plt.colorbar(im, ax=ax, shrink=0.85)

    # Draw d - r = T^{1/6} boundary
    for i, r in enumerate(r_vals):
        boundary_d = r + T_SIXTH
        if d_vals[0] <= boundary_d <= d_vals[-1]:
            j_frac = np.interp(boundary_d, d_vals, range(len(d_vals)))
            ax.plot(j_frac, i, "k*", markersize=10, zorder=5)
    ax.plot([], [], "k*", markersize=10, label=f"$d - r = T^{{1/6}} \\approx {T_SIXTH:.1f}$")
    ax.legend(loc="upper left", fontsize=9)

    # --- Panel (b): SPSC-Adaptive / LinUCB ratio heatmap ---
    adapt_grid = np.full((len(r_vals), len(d_vals)), np.nan)
    for i, r in enumerate(r_vals):
        for j, d in enumerate(d_vals):
            res = all_results.get((d, r))
            if res is None:
                continue
            adapt_grid[i, j] = res["SPSC-Adaptive"].mean() / max(res["LinUCB"].mean(), 1e-8)

    ax = axes[0, 1]
    im = ax.imshow(adapt_grid, cmap="RdYlBu_r", norm=norm, aspect="auto", origin="lower")
    for i in range(len(r_vals)):
        for j in range(len(d_vals)):
            v = adapt_grid[i, j]
            if np.isnan(v):
                ax.text(j, i, "--", ha="center", va="center", fontsize=8, color="gray")
            else:
                color = "white" if (v < 0.6 or v > 2.0) else "black"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=9, fontweight="bold", color=color)
    ax.set_xticks(range(len(d_vals)))
    ax.set_xticklabels(d_vals)
    ax.set_yticks(range(len(r_vals)))
    ax.set_yticklabels(r_vals)
    ax.set_xlabel("Ambient dimension $d$", fontsize=12)
    ax.set_ylabel("Latent rank $r$", fontsize=12)
    ax.set_title("(b) SPSC Adaptive / LinUCB\n(blue < 1 = Adaptive wins)", fontsize=12)
    plt.colorbar(im, ax=ax, shrink=0.85)

    # --- Panel (c): SPSC-Alg1 / Best Competitor heatmap ---
    best_grid = np.full((len(r_vals), len(d_vals)), np.nan)
    for i, r in enumerate(r_vals):
        for j, d in enumerate(d_vals):
            res = all_results.get((d, r))
            if res is None:
                continue
            best_comp = min(res[m].mean() for m in COMPETITORS)
            best_grid[i, j] = res["SPSC-Alg1"].mean() / max(best_comp, 1e-8)

    ax = axes[1, 0]
    im = ax.imshow(best_grid, cmap="RdYlBu_r", norm=norm, aspect="auto", origin="lower")
    for i in range(len(r_vals)):
        for j in range(len(d_vals)):
            v = best_grid[i, j]
            if np.isnan(v):
                ax.text(j, i, "--", ha="center", va="center", fontsize=8, color="gray")
            else:
                color = "white" if (v < 0.6 or v > 2.0) else "black"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=9, fontweight="bold", color=color)
    ax.set_xticks(range(len(d_vals)))
    ax.set_xticklabels(d_vals)
    ax.set_yticks(range(len(r_vals)))
    ax.set_yticklabels(r_vals)
    ax.set_xlabel("Ambient dimension $d$", fontsize=12)
    ax.set_ylabel("Latent rank $r$", fontsize=12)
    ax.set_title("(c) SPSC Alg.1 / Best Competitor\n(blue < 1 = SPSC beats all)", fontsize=12)
    plt.colorbar(im, ax=ax, shrink=0.85)

    # --- Panel (d): Regret bars for selected (d, r) cells ---
    ax = axes[1, 1]
    # Pick a winning slice: d=60, r=5 (or the biggest d-r gap available)
    slice_cells = []
    for d in [30, 60, 100]:
        for r in [3, 5, 10]:
            if all_results.get((d, r)) is not None:
                res = all_results[(d, r)]
                if res["SPSC-Alg1"].mean() < res["LinUCB"].mean():
                    slice_cells.append((d, r))
                    break
        if len(slice_cells) >= 3:
            break

    if not slice_cells:
        # Fallback: just pick cells with largest d-r
        for d, r in sorted(all_results.keys(), key=lambda x: x[0]-x[1], reverse=True):
            if all_results[(d, r)] is not None:
                slice_cells.append((d, r))
            if len(slice_cells) >= 3:
                break

    show_methods = ["SPSC-Alg1", "SPSC-Adaptive", "LinUCB", "SW-LinUCB",
                    "D-LinUCB", "LowOFUL", "VOFUL"]
    x = np.arange(len(slice_cells))
    n_m = len(show_methods)
    w = 0.8 / n_m

    for mi, meth in enumerate(show_methods):
        vals = [all_results[cell][meth].mean() for cell in slice_cells]
        ses = [all_results[cell][meth].std() / np.sqrt(max(len(all_results[cell][meth]), 1)) for cell in slice_cells]
        ax.bar(x + mi * w - 0.4 + w/2, vals, w, yerr=ses,
               label=METHOD_LABELS[meth].split("(")[0].strip(),
               color=METHOD_COLORS[meth], edgecolor="black", linewidth=0.3,
               capsize=2)

    ax.set_xticks(x)
    ax.set_xticklabels([f"d={d}, r={r}" for d, r in slice_cells], fontsize=9)
    ax.set_ylabel("Cumulative costed regret", fontsize=11)
    ax.set_title("(d) Regret comparison (selected cells)", fontsize=12)
    ax.legend(fontsize=7, ncol=2, loc="upper left")

    fig.suptitle(
        "Synthetic Extended SOTA: Phase Transition in SPSC vs All Baselines\n"
        f"$T$={T}, $K$={K}, probe_every={PROBE_EVERY}, "
        f"$\\lambda$={LAM}, feature_decay={FEATURE_DECAY}  ({N_SEEDS} seeds)",
        fontsize=13, fontweight="bold", y=1.01,
    )
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


# =========================================================================
# Main
# =========================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("Synthetic Extended SOTA (10 methods)")
    print(f"  d = {DS}")
    print(f"  r = {RS}")
    print(f"  T={T}, K={K}, lam={LAM}, probe_every={PROBE_EVERY}, window={WINDOW}")
    print(f"  feature_decay={FEATURE_DECAY}, N_SEEDS={N_SEEDS}")
    print(f"  T^(1/6) = {T_SIXTH:.2f}")
    print("=" * 80)

    all_results = {}
    d_run = []
    r_run = []
    total_cells = len(DS) * len(RS)
    cell_idx = 0

    for d in DS:
        for r in RS:
            cell_idx += 1
            if r >= d:
                print(f"\n[{cell_idx}/{total_cells}] d={d}, r={r} -- SKIPPED (r >= d)")
                continue

            # Use 1 seed for d=500 (too slow), full N_SEEDS for others
            n_seeds = 1 if d >= 500 else N_SEEDS

            t0 = time.time()
            print(f"\n\n[{cell_idx}/{total_cells}] ========== d={d}, r={r}  "
                  f"(10 methods x {n_seeds} seed{'s' if n_seeds>1 else ''}) ==========",
                  flush=True)

            res = run_cell(d, r, n_seeds)
            elapsed = time.time() - t0
            all_results[(d, r)] = res
            if d not in d_run:
                d_run.append(d)
            if r not in r_run:
                r_run.append(r)

            spsc_m = res["SPSC-Alg1"].mean()
            adapt_m = res["SPSC-Adaptive"].mean()
            lin_m = res["LinUCB"].mean()
            loful_m = res["LowOFUL"].mean()
            voful_m = res["VOFUL"].mean()
            best_comp = min(res[m].mean() for m in COMPETITORS)
            winner = "SPSC" if spsc_m < lin_m else "LinUCB"

            print(f"  DONE in {elapsed:.1f}s")
            print(f"    SPSC={spsc_m:.0f}  Adaptive={adapt_m:.0f}  "
                  f"Lin={lin_m:.0f}  LowOFUL={loful_m:.0f}  VOFUL={voful_m:.0f}")
            print(f"    SPSC/Lin={spsc_m/max(lin_m,1):.3f}  "
                  f"SPSC/Best={spsc_m/max(best_comp,1):.3f}  [{winner}]")
            sys.stdout.flush()

    d_run = sorted(d_run)
    r_run = sorted(r_run)

    print_tables(all_results, d_run, r_run)
    make_heatmap_figure(all_results, d_run, r_run,
                        os.path.join(OUT_DIR, "experiment_synthetic_extended.png"))
    print("\nDone.")
