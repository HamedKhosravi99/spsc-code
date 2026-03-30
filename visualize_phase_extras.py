"""
Extra creative visualizations from the cached phase diagram data.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.cm as cm

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
data = np.load(os.path.join(OUT_DIR, "phase_diagram_data.npz"))

D_GRID = data["d_grid"]
R_GRID = data["r_grid"]
ratio_sl = data["ratio_spsc_lin"]
ratio_so = data["ratio_spsc_oracle"]
spsc_r = data["spsc_regret"]
lin_r = data["lin_regret"]
ora_r = data["oracle_regret"]

plt.rcParams.update({
    "font.family": "serif",
    "mathtext.fontset": "cm",
    "axes.linewidth": 1.2,
})


# ======================================================================
# 1. 3D Surface: SPSC vs LinUCB vs Oracle regret landscapes
# ======================================================================

def fig_3d_surface():
    fig = plt.figure(figsize=(12, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Create meshgrid using indices for even spacing
    d_idx = np.arange(len(D_GRID))
    r_idx = np.arange(len(R_GRID))
    D_mesh, R_mesh = np.meshgrid(d_idx, r_idx)

    # Mask invalid cells (r >= d)
    mask = np.ones_like(ratio_sl, dtype=bool)
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r >= d:
                mask[i, j] = False

    # Normalize regrets for better visualization
    spsc_plot = np.where(mask, spsc_r, np.nan)
    lin_plot = np.where(mask, lin_r, np.nan)
    ora_plot = np.where(mask, ora_r, np.nan)

    # Plot surfaces
    surf_lin = ax.plot_surface(D_mesh, R_mesh, lin_plot,
                                alpha=0.35, color="#d62728",
                                edgecolor="#d62728", linewidth=0.5,
                                label="LinUCB")
    surf_spsc = ax.plot_surface(D_mesh, R_mesh, spsc_plot,
                                 alpha=0.55, color="#1f77b4",
                                 edgecolor="#1f77b4", linewidth=0.5,
                                 label="SPSC")
    surf_ora = ax.plot_surface(D_mesh, R_mesh, ora_plot,
                                alpha=0.35, color="#2ca02c",
                                edgecolor="#2ca02c", linewidth=0.5,
                                label="Oracle")

    # Add scatter points on surfaces for clarity
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if not mask[i, j]:
                continue
            ax.scatter(j, i, lin_r[i,j], color="#d62728", s=30, zorder=5,
                       edgecolor="white", linewidth=0.5)
            ax.scatter(j, i, spsc_r[i,j], color="#1f77b4", s=30, zorder=5,
                       edgecolor="white", linewidth=0.5)
            ax.scatter(j, i, ora_r[i,j], color="#2ca02c", s=30, zorder=5,
                       edgecolor="white", linewidth=0.5)

    # Drop lines from SPSC to Oracle (showing the gap)
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if not mask[i, j]:
                continue
            ax.plot([j, j], [i, i], [ora_r[i,j], spsc_r[i,j]],
                    color="#1f77b4", alpha=0.3, lw=1, ls=":")

    ax.set_xticks(d_idx)
    ax.set_xticklabels([str(d) for d in D_GRID], fontsize=9)
    ax.set_yticks(r_idx)
    ax.set_yticklabels([str(r) for r in R_GRID], fontsize=9)
    ax.set_xlabel("\nAmbient dimension $d$", fontsize=11, labelpad=8)
    ax.set_ylabel("\nSubspace rank $r$", fontsize=11, labelpad=8)
    ax.set_zlabel("Cumulative regret", fontsize=11, labelpad=8)
    ax.view_init(elev=25, azim=-55)

    # Legend proxy
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#d62728", alpha=0.5, label="LinUCB (full $d$-dim)"),
        Patch(facecolor="#1f77b4", alpha=0.7, label="SPSC (learned $r$-dim)"),
        Patch(facecolor="#2ca02c", alpha=0.5, label="Oracle (known $r$-dim)"),
    ]
    ax.legend(handles=legend_elements, fontsize=10, loc="upper right",
              framealpha=0.9)

    ax.set_title("Regret Landscape over $(d, r)$\n"
                 "Pendigits Semi-Synthetic Benchmark",
                 fontsize=13, fontweight="bold", pad=15)

    out = os.path.join(OUT_DIR, "phase_3d_surface.png")
    plt.savefig(out, bbox_inches="tight", dpi=200)
    print(f"Saved: {out}")


# ======================================================================
# 2. Polar Radar: Each (d,r) config as a petal showing 3 methods
# ======================================================================

def fig_polar_radar():
    """
    Polar 'flower' chart: one petal per (d,r) config.
    Each petal has 3 concentric layers: Oracle (inner), SPSC (mid), LinUCB (outer).
    The visual: where SPSC petals are much smaller than LinUCB, SPSC wins.
    """
    # Valid configs (r < d)
    configs = []
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r < d:
                configs.append((i, j, r, d))

    n = len(configs)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    width = 2 * np.pi / n * 0.85

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    # Normalize all regrets to [0, 1] for radial display
    all_vals = np.concatenate([lin_r[lin_r > 0], spsc_r[spsc_r > 0], ora_r[ora_r > 0]])
    vmax = all_vals.max() * 1.05

    for idx, (i, j, r, d) in enumerate(configs):
        angle = angles[idx]
        lin_val = lin_r[i, j] / vmax
        spsc_val = spsc_r[i, j] / vmax
        ora_val = ora_r[i, j] / vmax

        # LinUCB bar (outermost, red)
        ax.bar(angle, lin_val, width=width, bottom=0,
               color="#d62728", alpha=0.30, edgecolor="#d62728", linewidth=0.5)
        # SPSC bar (middle, blue)
        ax.bar(angle, spsc_val, width=width, bottom=0,
               color="#1f77b4", alpha=0.50, edgecolor="#1f77b4", linewidth=0.5)
        # Oracle bar (innermost, green)
        ax.bar(angle, ora_val, width=width, bottom=0,
               color="#2ca02c", alpha=0.50, edgecolor="#2ca02c", linewidth=0.5)

    # Labels around the circle
    ax.set_xticks(angles)
    labels = [f"$d$={d}\n$r$={r}" for (_, _, r, d) in configs]
    ax.set_xticklabels(labels, fontsize=8)

    # Remove radial labels for cleanliness
    ax.set_yticklabels([])
    ax.set_ylim(0, 1.0)

    # Ring at ratio=1 reference
    ax.set_rgrids([0.25, 0.5, 0.75], labels=["25%", "50%", "75%"],
                   fontsize=7, alpha=0.5)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#d62728", alpha=0.4, label="LinUCB"),
        Patch(facecolor="#1f77b4", alpha=0.6, label="SPSC (ours)"),
        Patch(facecolor="#2ca02c", alpha=0.6, label="Oracle"),
    ]
    ax.legend(handles=legend_elements, fontsize=11, loc="upper right",
              bbox_to_anchor=(1.25, 1.12), framealpha=0.9)

    ax.set_title("Algorithm Regret Comparison\nacross $(d, r)$ Configurations",
                 fontsize=14, fontweight="bold", pad=25, y=1.08)

    out = os.path.join(OUT_DIR, "phase_polar_radar.png")
    plt.savefig(out, bbox_inches="tight", dpi=200)
    print(f"Saved: {out}")


# ======================================================================
# 3. Concentric ring chart: r as rings, d as sectors, color = ratio
# ======================================================================

def fig_concentric_rings():
    """
    Concentric rings: each ring = a rank r, each sector = a dimension d.
    Cell color = SPSC/LinUCB ratio (blue=win, red=lose).
    Like a dartboard showing the operating regime.
    """
    n_d = len(D_GRID)
    n_r = len(R_GRID)

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))

    sector_width = 2 * np.pi / n_d
    angles = np.linspace(0, 2 * np.pi, n_d, endpoint=False)

    vmin = min(0.55, ratio_sl.min() - 0.02)
    vmax = max(1.15, ratio_sl.max() + 0.02)
    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)
    cmap = plt.cm.RdBu_r

    ring_inner = 0.3  # innermost ring start
    ring_width = 0.18

    for i, r in enumerate(R_GRID):
        r_bottom = ring_inner + i * ring_width
        r_height = ring_width * 0.92

        for j, d in enumerate(D_GRID):
            angle = angles[j]
            val = ratio_sl[i, j]

            if r >= d:
                color = "#e0e0e0"
                val_text = "n/a"
            else:
                color = cmap(norm(val))
                val_text = f"{val:.2f}"

            ax.bar(angle, r_height, width=sector_width * 0.92,
                   bottom=r_bottom, color=color,
                   edgecolor="white", linewidth=1.8)

            # Text annotation
            text_r = r_bottom + r_height / 2
            text_angle = angle
            txt_color = "white" if r < d and abs(val - 1.0) > 0.18 else "#333333"
            ax.text(text_angle, text_r, val_text,
                    ha="center", va="center", fontsize=8,
                    fontweight="bold", color=txt_color,
                    rotation=np.degrees(text_angle) - 90 if text_angle < np.pi else np.degrees(text_angle) + 90)

    # Ring labels (r values) on the left
    for i, r in enumerate(R_GRID):
        r_center = ring_inner + i * ring_width + ring_width * 0.46
        ax.text(np.pi * 1.08, r_center, f"$r={r}$",
                ha="center", va="center", fontsize=11, fontweight="bold",
                color="#333333",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="gray",
                          alpha=0.9, lw=0.8))

    # Sector labels (d values) outside outermost ring
    outer_r = ring_inner + n_r * ring_width + 0.06
    for j, d in enumerate(D_GRID):
        angle = angles[j]
        ax.text(angle, outer_r, f"$d={d}$",
                ha="center", va="center", fontsize=11, fontweight="bold")

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(0, ring_inner + n_r * ring_width + 0.15)
    ax.grid(False)
    ax.spines['polar'].set_visible(False)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.45, pad=0.08, aspect=20)
    cbar.set_label("SPSC / LinUCB ratio", fontsize=11, labelpad=8)
    cbar.ax.axhline(1.0, color="black", lw=2)

    ax.set_title("Operating Regime Compass\n"
                 "Rings = rank $r$ · Sectors = dimension $d$",
                 fontsize=14, fontweight="bold", pad=30, y=1.05)

    # Center annotation
    ax.text(0, 0.12, "SPSC\nAdvantage\nRegime",
            ha="center", va="center", fontsize=9, fontweight="bold",
            color="#1a3a6b", transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.4", fc="#dbe9f6", ec="#3b7dd8",
                      alpha=0.9, lw=1.5))

    out = os.path.join(OUT_DIR, "phase_concentric_rings.png")
    plt.savefig(out, bbox_inches="tight", dpi=200)
    print(f"Saved: {out}")


# ======================================================================
# 4. 3D bar chart rising from the (d, r) plane
# ======================================================================

def fig_3d_bars():
    """
    3D grouped bars: for each (d,r) cell, 3 bars (Oracle, SPSC, LinUCB)
    rising from the plane. Color-coded. Very visual.
    """
    fig = plt.figure(figsize=(14, 8))
    ax = fig.add_subplot(111, projection='3d')

    n_d = len(D_GRID)
    n_r = len(R_GRID)

    bar_w = 0.25
    colors = {"Oracle": "#2ca02c", "SPSC": "#1f77b4", "LinUCB": "#d62728"}
    alphas = {"Oracle": 0.7, "SPSC": 0.85, "LinUCB": 0.6}

    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r >= d:
                continue
            x_base = j

            # Oracle
            ax.bar3d(x_base - bar_w, i - bar_w/2, 0, bar_w, bar_w,
                     ora_r[i,j], color=colors["Oracle"],
                     alpha=alphas["Oracle"], edgecolor="white", linewidth=0.3)
            # SPSC
            ax.bar3d(x_base, i - bar_w/2, 0, bar_w, bar_w,
                     spsc_r[i,j], color=colors["SPSC"],
                     alpha=alphas["SPSC"], edgecolor="white", linewidth=0.3)
            # LinUCB
            ax.bar3d(x_base + bar_w, i - bar_w/2, 0, bar_w, bar_w,
                     lin_r[i,j], color=colors["LinUCB"],
                     alpha=alphas["LinUCB"], edgecolor="white", linewidth=0.3)

    ax.set_xticks(range(n_d))
    ax.set_xticklabels([str(d) for d in D_GRID], fontsize=10)
    ax.set_yticks(range(n_r))
    ax.set_yticklabels([f"$r$={r}" for r in R_GRID], fontsize=10)
    ax.set_zlabel("Cumulative Regret", fontsize=11, labelpad=10)
    ax.set_xlabel("\n$d$ (ambient dim)", fontsize=11, labelpad=10)
    ax.set_ylabel("\n$r$ (rank)", fontsize=11, labelpad=10)

    ax.view_init(elev=22, azim=-50)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=colors["Oracle"], alpha=0.7, label="Oracle"),
        Patch(facecolor=colors["SPSC"], alpha=0.85, label="SPSC (ours)"),
        Patch(facecolor=colors["LinUCB"], alpha=0.6, label="LinUCB"),
    ]
    ax.legend(handles=legend_elements, fontsize=11, loc="upper left",
              framealpha=0.9)

    ax.set_title("Regret Comparison: 3D Bar Landscape\n"
                 "Pendigits · $K=4$, $T=5{,}000$",
                 fontsize=13, fontweight="bold", pad=15)

    out = os.path.join(OUT_DIR, "phase_3d_bars.png")
    plt.savefig(out, bbox_inches="tight", dpi=200)
    print(f"Saved: {out}")


# ======================================================================
# 5. Bubble chart on (d, r) plane — bubble size = regret gap, color = ratio
# ======================================================================

def fig_bubble_chart():
    """
    Bubble chart: position = (d, r), size = |LinUCB - SPSC| regret gap,
    color = ratio. Bubbles with halos for Oracle.
    """
    fig, ax = plt.subplots(figsize=(10, 6.5))

    vmin = min(0.55, ratio_sl.min() - 0.02)
    vmax = max(1.15, ratio_sl.max() + 0.02)
    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)
    cmap = plt.cm.RdBu_r

    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r >= d:
                ax.scatter(d, r, s=80, color="#e0e0e0", marker="x",
                           zorder=3, linewidths=2)
                continue

            ratio = ratio_sl[i, j]
            gap = abs(lin_r[i, j] - spsc_r[i, j])
            ora_gap = spsc_r[i, j] - ora_r[i, j]

            # Oracle halo (light green ring)
            halo_size = (ora_gap / 30) ** 1.0 + 100
            ax.scatter(d, r, s=halo_size, facecolors="none",
                       edgecolors="#2ca02c", linewidths=2.5, alpha=0.5,
                       zorder=2)

            # Main bubble: size = regret gap, color = ratio
            bubble_size = (gap / 15) ** 1.0 + 80
            color = cmap(norm(ratio))
            ax.scatter(d, r, s=bubble_size, c=[color], edgecolors="white",
                       linewidths=1.5, zorder=4)

            # Annotation
            pct = (1 - ratio) * 100
            sign = "+" if pct > 0 else ""
            ax.annotate(f"{ratio:.2f}\n({sign}{pct:.0f}%)",
                        (d, r), textcoords="offset points",
                        xytext=(0, -max(np.sqrt(bubble_size)/2 + 8, 15)),
                        ha="center", va="top", fontsize=8, fontweight="bold",
                        color="#333333")

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.85, pad=0.02, aspect=25)
    cbar.set_label("SPSC / LinUCB ratio", fontsize=11)
    cbar.ax.axhline(1.0, color="black", lw=2)

    ax.set_xlabel("Ambient dimension $d$", fontsize=12)
    ax.set_ylabel("Subspace rank $r$", fontsize=12)
    ax.set_title("Bubble Chart: Regret Gap Magnitude & Direction\n"
                 "Size = $|$LinUCB $-$ SPSC$|$ gap · "
                 "Green halo = Oracle gap · Color = ratio",
                 fontsize=12, fontweight="bold")
    ax.set_xticks(D_GRID)
    ax.set_yticks(R_GRID)
    ax.tick_params(labelsize=10)

    # Background shading
    ax.set_facecolor("#fafafa")
    ax.grid(True, alpha=0.3, ls="--")

    out = os.path.join(OUT_DIR, "phase_bubble_chart.png")
    plt.savefig(out, bbox_inches="tight", dpi=200)
    print(f"Saved: {out}")


# ======================================================================
# Run all
# ======================================================================

if __name__ == "__main__":
    fig_3d_surface()
    fig_polar_radar()
    fig_concentric_rings()
    fig_3d_bars()
    fig_bubble_chart()
    print("\nAll visualizations generated.")
