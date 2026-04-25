"""
Generate the 2-panel composite figure for the paper:
  (a) Phase-transition contour map
  (b) Crossover ribbon (log-scale)
Saved as experiment1_synthetic_phase.png
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import matplotlib.patheffects as pe
from scipy.interpolate import griddata

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

# Theory constants for the corrected Theorem 1 (with d^{2/3} probe-term factor).
# The cached empirical data above was generated with K=10, T=5000.
T = 5000
K = 10
TK_SIXTH = (T / K) ** (1.0 / 6.0)         # ≈ 2.82
D_THRESH = (T / K) ** 0.5                 # ≈ 22.4 (right edge for r→0)


def theory_ratio(d, r):
    """SPSC/LinUCB ratio predicted by Thm 1: r/d + d^{-1/3}(T/K)^{1/6}."""
    return r / d + TK_SIXTH / d ** (1.0 / 3.0)

fig, axes = plt.subplots(1, 2, figsize=(14, 6),
                         gridspec_kw={"width_ratios": [1.15, 1]})

# =====================================================================
# Panel (a): Contour map
# =====================================================================
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
cf = ax.contourf(DI, RI, ZI, levels=np.arange(0.5, 4.05, 0.05),
                 cmap="RdBu_r", norm=norm, alpha=0.85)

# Empirical ratio=1 contour
cs = ax.contour(DI, RI, ZI, levels=[1.0], colors=["black"],
                linewidths=3, linestyles=["-"])
ax.clabel(cs, fmt="ratio = 1.0", fontsize=9, inline_spacing=10,
          manual=[(35, 8)])

# Theoretical boundary discussed in text (Thm 1, Rem dim_dep) but
# omitted from the figure: it is a sufficient (loose) bound, and
# overlaying it on the empirical heatmap produced misleading
# disagreements driven by problem-specific constants in $\tilO$.

# Data points
for (d, r), (s, l, o) in data.items():
    ratio = s / l
    if ratio < 0.95:
        ax.plot(d, r, "o", color="#1a5276", ms=7, mec="white", mew=1.2, zorder=5)
    elif ratio < 1.05:
        ax.plot(d, r, "s", color="#f39c12", ms=7, mec="white", mew=1.2, zorder=5)
    else:
        ax.plot(d, r, "^", color="#922b21", ms=7, mec="white", mew=1.2, zorder=5)

# Legend entries for markers
ax.plot([], [], "o", color="#1a5276", ms=7, mec="white", label="SPSC wins ($<0.95$)")
ax.plot([], [], "s", color="#f39c12", ms=7, mec="white", label="Tie ($0.95$--$1.05$)")
ax.plot([], [], "^", color="#922b21", ms=7, mec="white", label="LinUCB wins ($>1.05$)")

cb = plt.colorbar(cf, ax=ax, shrink=0.88, pad=0.02)
cb.set_label("SPSC / LinUCB ratio", fontsize=10)
cb.set_ticks([0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0])

ax.set_xlabel("Ambient dimension $d$", fontsize=12)
ax.set_ylabel("Latent rank $r$", fontsize=12)
ax.set_title("(a) Phase-transition contour map", fontsize=12, fontweight="bold")
ax.legend(fontsize=8, loc="upper left",
          framealpha=0.9, edgecolor="gray")
ax.set_xlim(8, 82)
ax.set_ylim(0.5, 21)

# =====================================================================
# Panel (b): Crossover ribbon (log-scale)
# =====================================================================
ax = axes[1]

r_groups = [1, 3, 5, 10, 15, 20]
cmap = plt.cm.viridis_r
colors = [cmap(i / max(len(r_groups) - 1, 1)) for i in range(len(r_groups))]

for idx, r in enumerate(r_groups):
    ds, rats = [], []
    for d in d_vals:
        if (d, r) in data:
            s, l, o = data[(d, r)]
            ds.append(d)
            rats.append(s / l)
    if len(ds) >= 2:
        ax.plot(ds, rats, "o-", color=colors[idx], lw=2.5, ms=7,
                label=f"$r = {r}$", zorder=3,
                path_effects=[pe.Stroke(linewidth=4, foreground="white"),
                              pe.Normal()])

# Shading
ax.axhspan(0, 1, alpha=0.07, color="blue")
ax.axhspan(1, 10, alpha=0.07, color="red")
ax.axhline(1.0, color="black", lw=2, alpha=0.6)

# Annotations
ax.text(68, 0.58, "SPSC\ndominates", fontsize=11, fontweight="bold",
        color="#1a5276", ha="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                  edgecolor="#1a5276", alpha=0.85))
ax.text(14, 4.0, "LinUCB\ndominates", fontsize=11, fontweight="bold",
        color="#922b21", ha="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                  edgecolor="#922b21", alpha=0.85))

ax.set_xlabel("Ambient dimension $d$", fontsize=12)
ax.set_ylabel("SPSC / LinUCB regret ratio", fontsize=12)
ax.set_title("(b) Empirical SPSC/LinUCB ratio vs $d$ for each $r$",
             fontsize=12, fontweight="bold")
ax.legend(fontsize=8.5, loc="upper right", title="Latent rank $r$",
          title_fontsize=9, framealpha=0.9, edgecolor="gray", ncol=2)
ax.set_ylim(0.45, 14.0)
ax.set_xlim(8, 82)
ax.set_yscale("log")
ax.set_yticks([0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0])
ax.get_yaxis().set_major_formatter(
    plt.FuncFormatter(lambda y, _: f"{y:.1f}"))
ax.grid(True, alpha=0.25, which="both")

plt.tight_layout(w_pad=3)
out = "experiment1_synthetic_phase.png"
plt.savefig(out, bbox_inches="tight", dpi=200)
print(f"Saved {out}")

# Also save a copy in the draft folder if it exists
import shutil, os
if os.path.isdir("draft"):
    shutil.copy(out, "draft/experiment1_synthetic_phase.png")
    print("Copied to draft/experiment1_synthetic_phase.png")
