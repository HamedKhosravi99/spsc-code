"""
High-resolution, paper-quality re-render of Figure 1
(experiment1_synthetic_phase.png).

Same 2-panel style as the source script (`experiment1_final_figure.py`):
  (a) Phase-transition contour map
  (b) Crossover ribbon (log-scale)

Uses the hardcoded data dict from experiment1_final_figure.py
(32 cells, d in {10,20,30,45,60,80}, r in {1,3,5,10,15,20}, r<d).
Increases DPI to 300, enlarges fonts, and tightens styling for
camera-ready quality.

Usage:
    cd code/
    python3 plot_phase_transition_hq.py
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import matplotlib.patheffects as pe
from scipy.interpolate import griddata


# -------------------------------------------------------------------------
# Paper-quality matplotlib settings
# -------------------------------------------------------------------------
plt.rcParams.update({
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "font.family": "serif",
    "font.size": 14,
    "axes.labelsize": 16,
    "axes.titlesize": 17,
    "axes.titleweight": "bold",
    "axes.linewidth": 1.4,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "xtick.major.width": 1.2,
    "ytick.major.width": 1.2,
    "xtick.major.size": 5,
    "ytick.major.size": 5,
    "legend.fontsize": 12,
    "legend.frameon": True,
    "legend.framealpha": 0.95,
    "legend.edgecolor": "0.3",
    "lines.linewidth": 2.6,
    "lines.markersize": 9,
    "lines.markeredgewidth": 1.4,
    "axes.grid": True,
    "grid.alpha": 0.30,
    "grid.linestyle": "--",
    "grid.linewidth": 0.7,
    "axes.axisbelow": True,
})

# -------------------------------------------------------------------------
# Hardcoded experimental data (copied verbatim from
# /Users/hkhosravi7/Downloads/source/code/experiment1_final_figure.py)
#   key:   (d, r)
#   value: (SPSC_regret, LinUCB_regret, Oracle_regret)
# -------------------------------------------------------------------------
data = {
    (10,  1): (2250,  414,    8), (10,  3): (1689,  436,  114), (10,  5): (1357,  414,  204),
    (20,  1): (2327, 1060,    8), (20,  3): (1970, 1081,  118), (20,  5): (1539,  953,  218),
    (20, 10): (1220,  972,  491), (20, 15): ( 986,  883,  664),
    (30,  1): (2269, 1669,    8), (30,  3): (1936, 1638,  118), (30,  5): (1593, 1516,  226),
    (30, 10): (1273, 1265,  485), (30, 15): (1193, 1236,  695), (30, 20): (1194, 1244,  888),
    (45,  1): (2283, 2258,    7), (45,  3): (1890, 2212,  117), (45,  5): (1630, 2006,  222),
    (45, 10): (1322, 1629,  467), (45, 15): (1237, 1452,  680), (45, 20): (1278, 1477,  874),
    (60,  1): (2379, 2590,    8), (60,  3): (1850, 2580,  115), (60,  5): (1696, 2333,  229),
    (60, 10): (1338, 1884,  490), (60, 15): (1245, 1571,  666), (60, 20): (1216, 1448,  821),
    (80,  1): (2430, 2896,    7), (80,  3): (2004, 2812,  115), (80,  5): (1665, 2507,  219),
    (80, 10): (1392, 2030,  479), (80, 15): (1270, 1701,  662), (80, 20): (1250, 1583,  826),
}

d_vals = sorted(set(d for d, r in data))
r_vals = sorted(set(r for d, r in data))
T_SIXTH = 5000 ** (1.0 / 6.0)


# -------------------------------------------------------------------------
# Figure layout
# -------------------------------------------------------------------------
fig, axes = plt.subplots(
    1, 2,
    figsize=(16.0, 7.0),
    gridspec_kw={"width_ratios": [1.15, 1]},
)

# =========================================================================
# Panel (a): Phase-transition contour map
# =========================================================================
ax = axes[0]

pts, vals = [], []
for (d, r), (s, l, o) in data.items():
    pts.append((d, r))
    vals.append(s / l)
pts = np.array(pts)
vals = np.array(vals)

di = np.linspace(8, 82, 300)
ri = np.linspace(0.5, 21, 300)
DI, RI = np.meshgrid(di, ri)
ZI = griddata(pts, vals, (DI, RI), method="cubic")

norm = TwoSlopeNorm(vmin=0.5, vcenter=1.0, vmax=4.0)
cf = ax.contourf(
    DI, RI, ZI,
    levels=np.arange(0.5, 4.05, 0.05),
    cmap="RdBu_r", norm=norm, alpha=0.88,
)

# Empirical ratio = 1 contour (the win/lose boundary)
cs = ax.contour(
    DI, RI, ZI, levels=[1.0],
    colors=["black"], linewidths=3.0, linestyles=["-"],
)
ax.clabel(cs, fmt="ratio = 1.0", fontsize=12, inline_spacing=10,
          manual=[(35, 8)])

# Theory boundary  d - r = T^{1/6}
d_line = np.linspace(8, 82, 100)
r_line = np.clip(d_line - T_SIXTH, 0, 21)
ax.plot(
    d_line, r_line,
    color="#222222", ls="--", lw=2.8, alpha=0.7,
    label=rf"Theory: $d - r = T^{{1/6}} \approx {T_SIXTH:.1f}$",
)

# Per-cell verdict markers
for (d, r), (s, l, o) in data.items():
    ratio = s / l
    if ratio < 0.95:
        ax.plot(d, r, "o", color="#1a5276",
                ms=10, mec="white", mew=1.5, zorder=5)
    elif ratio < 1.05:
        ax.plot(d, r, "s", color="#f39c12",
                ms=10, mec="white", mew=1.5, zorder=5)
    else:
        ax.plot(d, r, "^", color="#922b21",
                ms=10, mec="white", mew=1.5, zorder=5)

# Legend handles for marker categories
ax.plot([], [], "o", color="#1a5276", ms=10, mec="white",
        label=r"SPSC wins ($<0.95$)")
ax.plot([], [], "s", color="#f39c12", ms=10, mec="white",
        label=r"Tie ($0.95$--$1.05$)")
ax.plot([], [], "^", color="#922b21", ms=10, mec="white",
        label=r"LinUCB wins ($>1.05$)")

cb = plt.colorbar(cf, ax=ax, shrink=0.92, pad=0.02)
cb.set_label("SPSC / LinUCB regret ratio", fontsize=14)
cb.set_ticks([0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0])
cb.ax.tick_params(labelsize=12)

ax.set_xlabel(r"Ambient dimension $d$")
ax.set_ylabel(r"Latent rank $r$")
ax.set_title("(a) Phase-transition contour map", pad=12)
ax.legend(loc="upper left", framealpha=0.92, edgecolor="0.3")
ax.set_xlim(8, 82)
ax.set_ylim(0.5, 21)
ax.grid(False)  # contour panel reads cleaner without overlay grid


# =========================================================================
# Panel (b): Ratio vs d for each r (log-scale)
# =========================================================================
ax = axes[1]

r_groups = [1, 3, 5, 10, 15, 20]
cmap = plt.cm.viridis_r
colors = [cmap(i / max(len(r_groups) - 1, 1)) for i in range(len(r_groups))]

for idx, r in enumerate(r_groups):
    ds, rats, thrs = [], [], []
    for d in d_vals:
        if (d, r) in data:
            s, l, o = data[(d, r)]
            ds.append(d)
            rats.append(s / l)
            thrs.append(np.sqrt(r / d))
    if len(ds) >= 2:
        ax.plot(
            ds, rats, "o-",
            color=colors[idx], lw=3.0, ms=10,
            mec="black", mew=1.0,
            label=rf"$r = {r}$", zorder=3,
            path_effects=[pe.Stroke(linewidth=4.5, foreground="white"),
                          pe.Normal()],
        )
        ax.plot(ds, thrs, ":", color=colors[idx], lw=1.6, alpha=0.55, zorder=2)

# Win/lose shading
ax.axhspan(0, 1, alpha=0.08, color="blue")
ax.axhspan(1, 10, alpha=0.08, color="red")
ax.axhline(1.0, color="black", lw=2.0, alpha=0.65)

# Region labels
ax.text(
    68, 0.58, "SPSC\ndominates",
    fontsize=14, fontweight="bold", color="#1a5276", ha="center",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
              edgecolor="#1a5276", alpha=0.92, linewidth=1.4),
)
ax.text(
    14, 4.0, "LinUCB\ndominates",
    fontsize=14, fontweight="bold", color="#922b21", ha="center",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
              edgecolor="#922b21", alpha=0.92, linewidth=1.4),
)

ax.set_xlabel(r"Ambient dimension $d$")
ax.set_ylabel(r"SPSC / LinUCB regret ratio")
ax.set_title("(b) Ratio vs $d$ for each $r$\n"
             r"(solid = empirical, dotted = $\sqrt{r/d}$ theory)",
             pad=12)
ax.legend(
    loc="upper right", title=r"Latent rank $r$",
    title_fontsize=12, framealpha=0.92, edgecolor="0.3",
    ncol=2,
)
ax.set_ylim(0.45, 14.0)
ax.set_xlim(8, 82)
ax.set_yscale("log")
ax.set_yticks([0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0])
ax.get_yaxis().set_major_formatter(
    plt.FuncFormatter(lambda y, _: f"{y:.1f}"))
ax.grid(True, alpha=0.30, which="both", linestyle="--", linewidth=0.7)


# -------------------------------------------------------------------------
# Save
# -------------------------------------------------------------------------
plt.tight_layout(w_pad=4.0)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "figures",
                   "experiment1_synthetic_phase.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
plt.savefig(OUT, bbox_inches="tight", dpi=300, facecolor="white")
print(f"Saved: {OUT}")
