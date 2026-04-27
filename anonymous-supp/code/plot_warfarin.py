"""Plot Warfarin results from the experiment output."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Data from experiment output
R_VALUES = [1, 2, 3, 5, 10]

# SPSC results
spsc_mean = [1482.0, 1404.2, 1371.7, 1368.8, 1480.8]
spsc_se   = [49.2, 35.2, 33.3, 30.1, 18.6]

# Baselines (constant across r since they don't use r)
oracle_mean   = [5.8, 94.0, 177.2, 273.5, 574.2]
oracle_se     = [0.4, 2.0, 3.9, 7.1, 7.7]
dlinucb_mean  = [2176.6]*5
dlinucb_se    = [19.8]*5
swlinucb_mean = [2088.7]*5
swlinucb_se   = [17.6]*5
restart_mean  = [1972.8]*5
restart_se    = [16.4]*5
linucb_mean   = [2003.2]*5
linucb_se     = [14.7]*5

# Ratios
spsc_linucb_ratio = [s/l for s,l in zip(spsc_mean, linucb_mean)]
spsc_best_ratio   = [s/min(d,sw,r,l) for s,d,sw,r,l in
                      zip(spsc_mean, dlinucb_mean, swlinucb_mean, restart_mean, linucb_mean)]

# Subspace error
sub_error = [0.9610, 0.9957, 0.9984, 0.9990, 0.9995]
sub_se    = [0.0015, 0.0004, 0.0001, 0.0001, 0.0000]

# Probe overhead %
probe_overhead = [3.3, 3.5, 3.5, 3.6, 3.3]

# -----------------------------------------------------------------------
# Figure 1: 4-panel comprehensive
# -----------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(12, 9))

# Panel (a): Absolute regret bar chart (best r=5 cell)
ax = axes[0, 0]
methods = ["SPSC\n(ours)", "Oracle", "D-LinUCB", "SW-LinUCB", "Restart\nLinUCB", "LinUCB"]
means = [1368.8, 273.5, 2176.6, 2088.7, 1972.8, 2003.2]
ses   = [30.1, 7.1, 19.8, 17.6, 16.4, 14.7]
colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b", "#d62728"]
bars = ax.bar(range(6), means, yerr=ses, color=colors, capsize=4, edgecolor="white", linewidth=0.5)
ax.set_xticks(range(6))
ax.set_xticklabels(methods, fontsize=8)
ax.set_ylabel("Cumulative Control Regret")
ax.set_title("(a) Absolute regret at $r{=}5$ (best SPSC)", fontsize=10)
for i, (m, s) in enumerate(zip(means, ses)):
    ax.text(i, m + s + 30, f"{m:.0f}", ha="center", va="bottom", fontsize=8)
# Add improvement annotation
ax.annotate(f"$-31.7\\%$", xy=(0, 1368.8), xytext=(0.5, 1700),
            fontsize=10, fontweight="bold", color="#1f77b4",
            arrowprops=dict(arrowstyle="->", color="#1f77b4"))

# Panel (b): SPSC/LinUCB and SPSC/Best ratio vs r
ax = axes[0, 1]
ax.plot(R_VALUES, spsc_linucb_ratio, "o-", lw=2.5, markersize=9, color="#1f77b4",
        label="SPSC / LinUCB", zorder=3)
ax.plot(R_VALUES, spsc_best_ratio, "s--", lw=2, markersize=8, color="#d62728",
        label="SPSC / Best Competitor", zorder=3)
ax.axhline(1.0, color="gray", ls=":", lw=1, alpha=0.7)
ax.fill_between(R_VALUES, [0.6]*5, [1.0]*5, alpha=0.08, color="green")
ax.text(6, 0.95, "SPSC wins", fontsize=9, color="green", alpha=0.7)
ax.set_xlabel("Rank $r$", fontsize=10)
ax.set_ylabel("Regret ratio", fontsize=10)
ax.set_title("(b) SPSC vs baselines across ranks", fontsize=10)
ax.legend(fontsize=9, loc="upper right")
ax.set_xticks(R_VALUES)
ax.set_ylim(0.55, 1.15)
# Annotate best point
best_idx = np.argmin(spsc_linucb_ratio)
ax.annotate(f"{spsc_linucb_ratio[best_idx]:.3f}",
            xy=(R_VALUES[best_idx], spsc_linucb_ratio[best_idx]),
            xytext=(R_VALUES[best_idx]+1.5, spsc_linucb_ratio[best_idx]-0.03),
            fontsize=9, fontweight="bold", color="#1f77b4",
            arrowprops=dict(arrowstyle="->", color="#1f77b4"))

# Panel (c): Subspace recovery
ax = axes[1, 0]
ax.errorbar(R_VALUES, sub_error, yerr=sub_se, fmt="o-", lw=2, markersize=8,
            capsize=4, color="#2ca02c")
ax.set_xlabel("Rank $r$", fontsize=10)
ax.set_ylabel("Avg subspace error $\\|\\hat{P}_k - P_k^*\\|_2$", fontsize=10)
ax.set_title("(c) Subspace recovery", fontsize=10)
ax.set_xticks(R_VALUES)
ax.set_ylim(0.9, 1.02)
ax.axhline(1.0, color="gray", ls=":", lw=0.8)
ax.text(7, 0.965, "Error ≈ 1.0:\napproximate\nlow-rank", fontsize=8, color="gray", ha="center")

# Panel (d): Probe overhead
ax = axes[1, 1]
ax.bar(R_VALUES, probe_overhead, width=0.8, color="#ff7f0e", edgecolor="white", alpha=0.85)
ax.set_xlabel("Rank $r$", fontsize=10)
ax.set_ylabel("Probe overhead (\\% of costed regret)", fontsize=10)
ax.set_title("(d) Probe-cost tradeoff", fontsize=10)
ax.set_xticks(R_VALUES)
ax.set_ylim(0, 8)
for i, (r, v) in enumerate(zip(R_VALUES, probe_overhead)):
    ax.text(r, v + 0.2, f"{v:.1f}\\%", ha="center", va="bottom", fontsize=9)

fig.suptitle(
    "Warfarin Clinical Dosing — Real-Domain Bandit  |  "
    "$d{=}93$, $K{=}8$, $T{=}5{,}000$, 10 seeds",
    fontsize=12, y=1.01)
plt.tight_layout()
plt.savefig("experiment_warfarin.png", bbox_inches="tight", dpi=150)
print("Saved: experiment_warfarin.png")


# -----------------------------------------------------------------------
# Figure 2: Summary table as figure (for paper)
# -----------------------------------------------------------------------
fig2, ax2 = plt.subplots(figsize=(10, 3.5))
ax2.axis("off")

headers = ["$r$", "SPSC", "Oracle", "D-LinUCB", "SW-LinUCB", "Restart", "LinUCB",
           "SPSC/\nLinUCB", "SPSC/\nBest"]
cell_text = []
for i, r in enumerate(R_VALUES):
    row = [
        f"${r}$",
        f"${spsc_mean[i]:.0f} \\pm {spsc_se[i]:.0f}$",
        f"${oracle_mean[i]:.0f}$",
        f"${dlinucb_mean[i]:.0f}$",
        f"${swlinucb_mean[i]:.0f}$",
        f"${restart_mean[i]:.0f}$",
        f"${linucb_mean[i]:.0f}$",
        f"**{spsc_linucb_ratio[i]:.3f}**",
        f"{spsc_best_ratio[i]:.3f}",
    ]
    cell_text.append(row)

table = ax2.table(cellText=cell_text, colLabels=headers, loc="center",
                  cellLoc="center", colColours=["#f0f0f0"]*9)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1.0, 1.6)

# Bold SPSC column
for i in range(len(R_VALUES)):
    table[i+1, 1].set_text_props(fontweight="bold")
    table[i+1, 7].set_text_props(fontweight="bold")

fig2.suptitle("Warfarin: Cumulative Control Regret ($d{=}93$, 10 seeds, $\\pm 1$ SE)",
              fontsize=11)
plt.savefig("experiment_warfarin_table.png", bbox_inches="tight", dpi=150)
print("Saved: experiment_warfarin_table.png")

print("\nDone!")
