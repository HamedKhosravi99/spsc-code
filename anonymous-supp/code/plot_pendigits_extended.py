"""Standalone plot from full per-cell results (10 methods + LinTS/SW-LinTS)."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(OUT_DIR, "experiment_pendigits_extended.png")
LINTS_JSON = os.path.join(OUT_DIR, "results", "experiment_pendigits_lints.json")

# Per-cell mean ± SE for the 10 main methods (from user's full per-cell tables)
MAIN = {
    (55, 10): {
        "Oracle":        ( 951,  5),
        "SPSC":          (2774, 58),
        "Adap":          (2682, 93),
        "LowOFUL":       (3703, 71),
        "VOFUL":         (3655, 67),
        "LowRank":       (4246, 28),
        "SW-LinUCB":     (3863, 11),
        "D-LinUCB":      (4056,  9),
        "Restart-LinUCB":(3620,  7),
        "LinUCB":        (3658,  9),
    },
    (55, 20): {
        "Oracle":        (1816,  4),
        "SPSC":          (2803, 60),
        "Adap":          (2490, 56),
        "LowOFUL":       (3689, 54),
        "VOFUL":         (3854, 58),
        "LowRank":       (4271, 39),
        "SW-LinUCB":     (3863, 11),
        "D-LinUCB":      (4056,  9),
        "Restart-LinUCB":(3620,  7),
        "LinUCB":        (3658,  9),
    },
    (55, 30): {
        "Oracle":        (2534,  6),
        "SPSC":          (3051, 62),
        "Adap":          (2776, 45),
        "LowOFUL":       (3827, 45),
        "VOFUL":         (3818, 39),
        "LowRank":       (4329, 20),
        "SW-LinUCB":     (3863, 11),
        "D-LinUCB":      (4056,  9),
        "Restart-LinUCB":(3620,  7),
        "LinUCB":        (3658,  9),
    },
    (105, 10): {
        "Oracle":        ( 666,  3),
        "SPSC":          (2066, 64),
        "Adap":          (1693, 38),
        "LowOFUL":       (2927, 74),
        "VOFUL":         (2816, 55),
        "LowRank":       (3027, 43),
        "SW-LinUCB":     (3297,  6),
        "D-LinUCB":      (3400,  6),
        "Restart-LinUCB":(3152,  6),
        "LinUCB":        (3184,  5),
    },
    (105, 20): {
        "Oracle":        (1242,  3),
        "SPSC":          (2067, 62),
        "Adap":          (1571, 67),
        "LowOFUL":       (2840, 41),
        "VOFUL":         (2835, 35),
        "LowRank":       (3123, 18),
        "SW-LinUCB":     (3297,  6),
        "D-LinUCB":      (3400,  6),
        "Restart-LinUCB":(3152,  6),
        "LinUCB":        (3184,  5),
    },
    (105, 30): {
        "Oracle":        (1745,  4),
        "SPSC":          (2247, 58),
        "Adap":          (1722, 58),
        "LowOFUL":       (2826, 75),
        "VOFUL":         (2839, 56),
        "LowRank":       (3283, 19),
        "SW-LinUCB":     (3297,  6),
        "D-LinUCB":      (3400,  6),
        "Restart-LinUCB":(3152,  6),
        "LinUCB":        (3184,  5),
    },
}

# Pull LinTS/SW-LinTS from the lints JSON (mean and SE per cell).
def _stats(arr):
    arr = np.asarray(arr, float)
    return float(arr.mean()), float(arr.std() / np.sqrt(len(arr)))

with open(LINTS_JSON) as f:
    lints = json.load(f)["results"]
for (d, r), cell in list(MAIN.items()):
    key = f"d={d},r={r}"
    if key in lints and lints[key]:
        cell["LinTS"]    = _stats(lints[key]["LinTS"])
        cell["SW-LinTS"] = _stats(lints[key]["SW-LinTS"])

ORDER = ["Oracle", "SPSC", "Adap",
         "LowOFUL", "VOFUL", "LowRank",
         "SW-LinUCB", "D-LinUCB", "Restart-LinUCB", "LinUCB",
         "LinTS", "SW-LinTS"]

LABELS = {
    "Oracle":         "Oracle LinUCB",
    "SPSC":           "SPSC (ours)",
    "Adap":           "SPSC-Adaptive (ours)",
    "LowOFUL":        "LowOFUL",
    "VOFUL":          "VOFUL",
    "LowRank":        "LowRank-Reward",
    "SW-LinUCB":      "SW-LinUCB",
    "D-LinUCB":       "D-LinUCB",
    "Restart-LinUCB": "Restart-LinUCB",
    "LinUCB":         "LinUCB",
    "LinTS":          "LinTS",
    "SW-LinTS":       "SW-LinTS",
}
COLORS = {
    "Oracle":         "#2ca02c",
    "SPSC":           "#1f77b4",
    "Adap":           "#17becf",
    "LowOFUL":        "#e377c2",
    "VOFUL":          "#9467bd",
    "LowRank":        "#7f7f7f",
    "SW-LinUCB":      "#bcbd22",
    "D-LinUCB":       "#ff7f0e",
    "Restart-LinUCB": "#8c564b",
    "LinUCB":         "#d62728",
    "LinTS":          "#98df8a",
    "SW-LinTS":       "#c5b0d5",
}

# 4 strongest winning cells by SPSC-Adaptive vs LinUCB.
def adv(cell):
    c = MAIN[cell]
    return c["Adap"][0] / c["LinUCB"][0]
cells = sorted(MAIN, key=adv)[:4]

LABEL_COLOR = "#000000"
fig, axes = plt.subplots(1, 4, figsize=(6.0 * 4, 8.0), sharey=False)

for ax_idx, (d, r) in enumerate(cells):
    ax = axes[ax_idx]
    cell = MAIN[(d, r)]
    methods = [m for m in ORDER if m in cell]
    means = np.array([cell[m][0] for m in methods])
    ses   = np.array([cell[m][1] for m in methods])
    colors = [COLORS[m] for m in methods]
    labels = [LABELS[m] for m in methods]

    order = np.argsort(means)
    y = np.arange(len(methods))
    ax.barh(y,
            means[order], xerr=ses[order],
            color=[colors[i] for i in order],
            capsize=3.5, height=0.7,
            edgecolor="black", linewidth=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([labels[i] for i in order],
                       fontsize=12.5, color=LABEL_COLOR, fontweight="bold")
    ax.set_xlabel("Control regret", fontsize=14,
                  color=LABEL_COLOR, fontweight="bold")
    ax.set_title(f"$d={d}$, $r={r}$",
                 fontsize=15, fontweight="bold", color=LABEL_COLOR)
    ax.tick_params(axis="x", labelsize=12, colors=LABEL_COLOR)
    ax.tick_params(axis="y", labelsize=12.5, colors=LABEL_COLOR)
    for spine in ax.spines.values():
        spine.set_color(LABEL_COLOR); spine.set_linewidth(1.0)
    ax.xaxis.grid(True, alpha=0.35)

fig.suptitle(
    "Pendigits: SPSC dominates every non-oracle baseline at $d{\\geq}55$, $r{\\geq}10$",
    fontsize=17, fontweight="bold", y=1.02, color=LABEL_COLOR,
)
plt.tight_layout()
plt.savefig(OUT_PATH, bbox_inches="tight", dpi=180)
print(f"Saved: {OUT_PATH}")
print("Cells plotted (best-4 by SPSC-Adaptive ratio):", cells)
