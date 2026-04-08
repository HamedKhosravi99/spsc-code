"""
Final polished visualizations for Satimage benchmark.
Generates from cached data.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Patch

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
data = np.load(os.path.join(OUT_DIR, "satimage_phase_data.npz"))

D_GRID = list(data["d_grid"])
R_GRID = list(data["r_grid"])

METHOD_NAMES = [
    "Oracle-LinUCB",
    "SPSC-Alg1",
    "LowRank-Reward",
    "SW-LinUCB",
    "D-LinUCB",
    "Restart-LinUCB",
    "LinUCB",
]

grids = {}
for m in METHOD_NAMES:
    key = f"{m}_regret"
    grids[m] = data[key]

plt.rcParams.update({
    "font.family": "serif",
    "mathtext.fontset": "cm",
    "axes.linewidth": 1.2,
})

NON_ORACLE_FULL_DIM = ["LinUCB", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB"]
NON_ORACLE_ALL = ["LinUCB", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB", "LowRank-Reward"]


# =====================================================================
# 1. Double ring chart: vs LinUCB (left) + vs best competitor (right)
# =====================================================================

def make_ring(ax, ratio_grid, title, cbar_ax=None, fig=None):
    n_d, n_r = len(D_GRID), len(R_GRID)
    sector_width = 2 * np.pi / n_d
    angles = np.linspace(0, 2 * np.pi, n_d, endpoint=False)

    vmin = min(0.50, ratio_grid.min() - 0.02)
    vmax = max(1.25, ratio_grid.max() + 0.02)
    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)
    cmap = plt.cm.RdBu_r

    ring_inner = 0.3
    ring_width = 0.18

    for i, r in enumerate(R_GRID):
        r_bottom = ring_inner + i * ring_width
        r_height = ring_width * 0.90

        for j, d in enumerate(D_GRID):
            angle = angles[j]
            val = ratio_grid[i, j]

            if r >= d:
                color = "#e0e0e0"
                val_text = ""
            else:
                color = cmap(norm(val))
                pct = (1 - val) * 100
                val_text = f"{val:.2f}"

            ax.bar(angle, r_height, width=sector_width * 0.90,
                   bottom=r_bottom, color=color,
                   edgecolor="white", linewidth=1.5)

            text_r = r_bottom + r_height / 2
            txt_color = "white" if r < d and abs(val - 1.0) > 0.15 else "#333333"
            rot = np.degrees(angle) - 90 if angle < np.pi else np.degrees(angle) + 90
            ax.text(angle, text_r, val_text,
                    ha="center", va="center", fontsize=7.5,
                    fontweight="bold", color=txt_color, rotation=rot)

    # Ring labels
    for i, r in enumerate(R_GRID):
        r_center = ring_inner + i * ring_width + ring_width * 0.45
        ax.text(np.pi * 1.08, r_center, f"$r$={r}",
                ha="center", va="center", fontsize=9.5, fontweight="bold",
                color="#333333",
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="gray",
                          alpha=0.9, lw=0.6))

    outer_r = ring_inner + n_r * ring_width + 0.05
    for j, d in enumerate(D_GRID):
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


def fig_double_rings():
    n_d, n_r = len(D_GRID), len(R_GRID)

    # Compute ratio grids
    ratio_vs_lin = np.ones((n_r, n_d))
    ratio_vs_best = np.ones((n_r, n_d))
    best_name = np.empty((n_r, n_d), dtype=object)

    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r >= d:
                continue
            spsc = grids["SPSC-Alg1"][i, j]
            ratio_vs_lin[i, j] = spsc / max(grids["LinUCB"][i, j], 1e-8)

            # Best non-oracle competitor
            best_reg = 0
            best_m = ""
            for m in NON_ORACLE_ALL:
                if grids[m][i, j] > best_reg:
                    best_reg = grids[m][i, j]
                    best_m = m
            # Actually find the LOWEST regret (strongest competitor)
            best_reg = float("inf")
            for m in NON_ORACLE_ALL:
                if grids[m][i, j] < best_reg:
                    best_reg = grids[m][i, j]
                    best_m = m
            ratio_vs_best[i, j] = spsc / max(best_reg, 1e-8)
            best_name[i, j] = best_m

    fig = plt.figure(figsize=(16, 7.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.05], wspace=0.15)

    ax1 = fig.add_subplot(gs[0], polar=True)
    ax2 = fig.add_subplot(gs[1], polar=True)
    cbar_ax = fig.add_subplot(gs[2])

    make_ring(ax1, ratio_vs_lin,
              "(a) SPSC / LinUCB")
    make_ring(ax2, ratio_vs_best,
              "(b) SPSC / Best Competitor",
              cbar_ax=cbar_ax, fig=fig)

    fig.suptitle(
        r"$\mathbf{Satimage\ Phase\ Diagram}$:  "
        r"SPSC Operating Regime"
        f"\n$K=4$,  $T=5,000$,  $n_{{act}}=80$,  15 seeds / cell",
        fontsize=13, y=1.02,
    )

    out = os.path.join(OUT_DIR, "satimage_double_rings.png")
    plt.savefig(out, bbox_inches="tight", dpi=200)
    print(f"Saved: {out}")


# =====================================================================
# 2. Dot-strip chart: all 7 methods at each (d,r) — cleaner than bubble
# =====================================================================

def fig_dot_strip():
    METHOD_COLORS = {
        "Oracle-LinUCB":    "#2ca02c",
        "SPSC-Alg1":        "#1f77b4",
        "LowRank-Reward":   "#17becf",
        "SW-LinUCB":        "#9467bd",
        "D-LinUCB":         "#ff7f0e",
        "Restart-LinUCB":   "#8c564b",
        "LinUCB":           "#d62728",
    }
    METHOD_MARKERS = {
        "Oracle-LinUCB":    "v",
        "SPSC-Alg1":        "*",
        "LowRank-Reward":   "D",
        "SW-LinUCB":        "s",
        "D-LinUCB":         "^",
        "Restart-LinUCB":   "P",
        "LinUCB":           "o",
    }
    METHOD_LABELS = {
        "Oracle-LinUCB":    "Oracle (Jun+ '19)",
        "SPSC-Alg1":        "SPSC (ours)",
        "LowRank-Reward":   "LowRank-Reward (LowESTR spirit)",
        "SW-LinUCB":        "SW-LinUCB (Cheung+ '19)",
        "D-LinUCB":         "D-LinUCB (Russac+ '19)",
        "Restart-LinUCB":   "Restart-LinUCB (Auer+ '19)",
        "LinUCB":           "LinUCB (Abbasi+ '11)",
    }
    METHOD_SIZES = {
        "Oracle-LinUCB":    60,
        "SPSC-Alg1":        120,
        "LowRank-Reward":   50,
        "SW-LinUCB":        55,
        "D-LinUCB":         55,
        "Restart-LinUCB":   55,
        "LinUCB":           55,
    }

    configs = []
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r < d:
                configs.append((i, j, r, d))

    n_configs = len(configs)

    fig, ax = plt.subplots(figsize=(16, 6.5))

    for m_idx, method in enumerate(METHOD_NAMES):
        xs, ys = [], []
        for c_idx, (i, j, r, d) in enumerate(configs):
            xs.append(c_idx)
            ys.append(grids[method][i, j])

        ax.scatter(xs, ys, s=METHOD_SIZES[method],
                   c=METHOD_COLORS[method],
                   marker=METHOD_MARKERS[method],
                   alpha=0.8, edgecolors="white", linewidths=0.5,
                   zorder=4 if method == "SPSC-Alg1" else 3,
                   label=METHOD_LABELS[method])

    # Connect SPSC with a line
    spsc_ys = [grids["SPSC-Alg1"][i, j] for i, j, r, d in configs]
    ax.plot(range(n_configs), spsc_ys, color="#1f77b4", lw=1.8,
            ls="-", alpha=0.4, zorder=2)

    # Shade SPSC advantage region vs each baseline
    lin_ys = [grids["LinUCB"][i, j] for i, j, r, d in configs]
    ax.fill_between(range(n_configs), spsc_ys, lin_ys,
                     where=[s < l for s, l in zip(spsc_ys, lin_ys)],
                     color="#1f77b4", alpha=0.08, zorder=1)

    # Add r-group separators
    group_boundaries = []
    prev_r = configs[0][2]
    for c_idx, (i, j, r, d) in enumerate(configs):
        if r != prev_r:
            group_boundaries.append(c_idx - 0.5)
            prev_r = r
    for gb in group_boundaries:
        ax.axvline(gb, color="gray", ls=":", lw=1, alpha=0.4)

    # Group labels
    group_centers = []
    start = 0
    for gb in group_boundaries + [n_configs]:
        center = (start + gb) / 2
        group_centers.append(center)
        start = gb
    for gc, r_val in zip(group_centers, R_GRID):
        ax.text(gc, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 7500,
                f"$r={r_val}$", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color="#555555")

    ax.set_xticks(range(n_configs))
    ax.set_xticklabels([f"$d$={d}" for _, _, r, d in configs],
                        fontsize=8, rotation=45, ha="right")
    ax.set_ylabel("Cumulative Costed Regret", fontsize=12)
    ax.set_xlabel("Configuration", fontsize=12)
    ax.set_title(
        "Satimage Benchmark: 7-Method Comparison across $(d, r)$\n"
        f"$K=4$,  $T=5,000$,  $n_{{act}}=80$,  5 seeds / cell   "
        r"($\bigstar$ = SPSC)",
        fontsize=12, fontweight="bold")
    ax.legend(fontsize=8.5, loc="upper left", ncol=2, framealpha=0.92,
              edgecolor="#cccccc", markerscale=1.2)
    ax.grid(True, alpha=0.15, ls="--")
    ax.set_facecolor("#fafafa")
    ax.tick_params(labelsize=9)

    out = os.path.join(OUT_DIR, "satimage_dot_strip.png")
    plt.savefig(out, bbox_inches="tight", dpi=200)
    print(f"Saved: {out}")


# =====================================================================
# 3. Win-count horizontal bar chart — at a glance "who beats whom"
# =====================================================================

def fig_wincount():
    n_r, n_d = len(R_GRID), len(D_GRID)
    total_valid = sum(1 for i, r in enumerate(R_GRID)
                      for j, d in enumerate(D_GRID) if r < d)

    competitors = ["LinUCB", "D-LinUCB", "Restart-LinUCB",
                    "LowRank-Reward", "SW-LinUCB"]
    comp_labels = {
        "LinUCB": "LinUCB",
        "D-LinUCB": "D-LinUCB",
        "Restart-LinUCB": "Restart-LinUCB",
        "LowRank-Reward": "LowRank-Reward",
        "SW-LinUCB": "SW-LinUCB",
    }

    wins = {}
    avg_ratio = {}
    for m in competitors:
        w = 0
        ratios = []
        for i, r in enumerate(R_GRID):
            for j, d in enumerate(D_GRID):
                if r < d:
                    ratio = grids["SPSC-Alg1"][i, j] / max(grids[m][i, j], 1e-8)
                    if ratio < 1.0:
                        w += 1
                    ratios.append(ratio)
        wins[m] = w
        avg_ratio[m] = np.mean(ratios)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4),
                                     gridspec_kw={"width_ratios": [1, 1], "wspace": 0.4})

    # Panel (a): win counts
    y_pos = np.arange(len(competitors))
    win_vals = [wins[m] for m in competitors]
    colors = ["#1f77b4" if w > total_valid // 2 else "#aec7e8" for w in win_vals]

    bars = ax1.barh(y_pos, win_vals, color=colors, edgecolor="white", height=0.65)
    ax1.axvline(total_valid / 2, color="gray", ls="--", lw=1, alpha=0.5)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels([comp_labels[m] for m in competitors], fontsize=10)
    ax1.set_xlabel(f"Cells where SPSC wins (out of {total_valid})", fontsize=11)
    ax1.set_title("(a) Win Count: SPSC vs Each Baseline", fontsize=12, fontweight="bold")
    ax1.set_xlim(0, total_valid + 1)
    for bar, w in zip(bars, win_vals):
        ax1.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                 f"{w}/{total_valid}", va="center", fontsize=10, fontweight="bold")

    # Panel (b): average ratio
    ratio_vals = [avg_ratio[m] for m in competitors]
    colors2 = ["#1f77b4" if r < 1.0 else "#d62728" for r in ratio_vals]
    bars2 = ax1_b = ax2.barh(y_pos, ratio_vals, color=colors2, edgecolor="white", height=0.65)
    ax2.axvline(1.0, color="black", ls="-", lw=2, alpha=0.5)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([comp_labels[m] for m in competitors], fontsize=10)
    ax2.set_xlabel("Avg SPSC / Baseline ratio (< 1 = SPSC wins)", fontsize=11)
    ax2.set_title("(b) Average Regret Ratio", fontsize=12, fontweight="bold")
    ax2.set_xlim(0.5, 1.3)
    for bar, r in zip(bars2, ratio_vals):
        ax2.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                 f"{r:.3f}", va="center", fontsize=10, fontweight="bold")

    fig.suptitle("Satimage: SPSC vs 5 Non-Oracle Baselines", fontsize=13,
                 fontweight="bold", y=1.02)

    out = os.path.join(OUT_DIR, "satimage_wincount.png")
    plt.savefig(out, bbox_inches="tight", dpi=200)
    print(f"Saved: {out}")


if __name__ == "__main__":
    fig_double_rings()
    fig_dot_strip()
    fig_wincount()
    print("\nAll Satimage final plots generated.")
