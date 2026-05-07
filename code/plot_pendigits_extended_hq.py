"""
High-resolution, paper-quality re-render of the Pendigits operating-regime
figure (`figures/experiment_pendigits_extended.png`).

Uses the exact mean/SE values from `appendix_tables.tex`'s
`tab:app-pendigits`, so the figure is guaranteed to match the table.

Layout: 4 horizontal-bar panels in a 1x4 row, one panel per (d, r) cell:
    (d=55, r=20), (d=105, r=10), (d=105, r=20), (d=105, r=30)
All panels use the same fixed method ordering (best at bottom).

Usage:
    cd code/
    python3 plot_pendigits_extended_hq.py
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# -------------------------------------------------------------------------
# Verified per-cell data, copied from appendix_tables.tex / tab:app-pendigits
# Each entry is (mean, SE) for one method at one (d, r).
# -------------------------------------------------------------------------
DATA = {
    (55, 20): {
        "Oracle LinUCB":        (1816,  4),
        "SPSC-Adaptive (ours)": (2490, 56),
        "SPSC (ours)":          (2803, 60),
        "Restart-LinUCB":       (3620,  7),
        "LinUCB":               (3658,  9),
        "LowOFUL":              (3689, 54),
        "VOFUL":                (3854, 58),
        "SW-LinUCB":            (3863, 11),
        "D-LinUCB":             (4056,  9),
        "LowRank-Reward":       (4271, 39),
        "LinTS":                (4343, 16),
        "SW-LinTS":             (4648,  9),
    },
    (105, 10): {
        "Oracle LinUCB":        ( 666,  3),
        "SPSC-Adaptive (ours)": (1693, 38),
        "SPSC (ours)":          (2066, 64),
        "VOFUL":                (2816, 55),
        "LowOFUL":              (2927, 74),
        "LowRank-Reward":       (3027, 43),
        "LinTS":                (3117, 10),
        "Restart-LinUCB":       (3152,  6),
        "LinUCB":               (3184,  5),
        "SW-LinUCB":            (3297,  6),
        "D-LinUCB":             (3400,  6),
        "SW-LinTS":             (3557,  4),
    },
    (105, 20): {
        "Oracle LinUCB":        (1242,  3),
        "SPSC-Adaptive (ours)": (1571, 67),
        "SPSC (ours)":          (2067, 62),
        "VOFUL":                (2835, 35),
        "LowOFUL":              (2840, 41),
        "LinTS":                (3117, 10),
        "LowRank-Reward":       (3123, 18),
        "Restart-LinUCB":       (3152,  6),
        "LinUCB":               (3184,  5),
        "SW-LinUCB":            (3297,  6),
        "D-LinUCB":             (3400,  6),
        "SW-LinTS":             (3557,  4),
    },
    (105, 30): {
        "SPSC-Adaptive (ours)": (1722, 58),
        "Oracle LinUCB":        (1745,  4),
        "SPSC (ours)":          (2247, 58),
        "LowOFUL":              (2826, 75),
        "VOFUL":                (2839, 56),
        "LinTS":                (3117, 10),
        "Restart-LinUCB":       (3152,  6),
        "LinUCB":               (3184,  5),
        "LowRank-Reward":       (3283, 19),
        "SW-LinUCB":            (3297,  6),
        "D-LinUCB":             (3400,  6),
        "SW-LinTS":             (3557,  4),
    },
}


# -------------------------------------------------------------------------
# Fixed method ordering for the y-axis (top = worst, bottom = best).
# Putting Oracle at the very bottom and our methods just above it keeps
# the visual hierarchy clear across all panels.
# -------------------------------------------------------------------------
METHOD_ORDER = [
    "SW-LinTS",                # top (worst)
    "LinTS",
    "LowRank-Reward",
    "D-LinUCB",
    "SW-LinUCB",
    "LinUCB",
    "Restart-LinUCB",
    "LowOFUL",
    "VOFUL",
    "SPSC (ours)",
    "SPSC-Adaptive (ours)",
    "Oracle LinUCB",           # bottom (best)
]

# Color and emphasis: highlight ours and Oracle.
COLOR = {
    "Oracle LinUCB":        "#27ae60",  # green
    "SPSC-Adaptive (ours)": "#c0392b",  # crimson
    "SPSC (ours)":          "#1f4e79",  # navy
    "VOFUL":                "#8e44ad",  # purple
    "LowOFUL":              "#e91e63",  # pink
    "LowRank-Reward":       "#7f8c8d",  # gray
    "Restart-LinUCB":       "#795548",  # brown
    "LinUCB":               "#d35400",  # dark orange
    "SW-LinUCB":            "#bdb76b",  # olive
    "D-LinUCB":             "#e67e22",  # orange
    "LinTS":                "#16a085",  # teal
    "SW-LinTS":             "#9b59b6",  # light purple
}


# -------------------------------------------------------------------------
# Paper-quality matplotlib settings
# -------------------------------------------------------------------------
plt.rcParams.update({
    "figure.dpi":         300,
    "savefig.dpi":        300,
    "font.family":        "serif",
    "font.size":          14,
    "axes.labelsize":     16,
    "axes.titlesize":     17,
    "axes.titleweight":   "bold",
    "axes.linewidth":     1.4,
    "xtick.labelsize":    13,
    "ytick.labelsize":    13,
    "xtick.major.width":  1.2,
    "ytick.major.width":  1.2,
    "legend.fontsize":    13,
    "lines.linewidth":    2.0,
    "axes.grid":          True,
    "grid.alpha":         0.30,
    "grid.linestyle":     "--",
    "grid.linewidth":     0.7,
    "axes.axisbelow":     True,
})


def plot_panel(ax, cell_dict, title, show_yticks=True):
    """Draw one (d, r) panel."""
    methods = METHOD_ORDER
    means   = [cell_dict[m][0] for m in methods]
    ses     = [cell_dict[m][1] for m in methods]
    colors  = [COLOR[m] for m in methods]

    y = np.arange(len(methods))
    bars = ax.barh(
        y, means, xerr=ses,
        color=colors, edgecolor="black", linewidth=1.0,
        height=0.78,
        error_kw=dict(ecolor="black", lw=1.4, capsize=4, capthick=1.4),
        zorder=3,
    )

    if show_yticks:
        ax.set_yticks(y)
        ax.set_yticklabels(methods)
        # Bold labels for our methods and Oracle (best); color-code Oracle
        for ticklabel, m in zip(ax.get_yticklabels(), methods):
            if "(ours)" in m:
                ticklabel.set_fontweight("bold")
            elif m == "Oracle LinUCB":
                ticklabel.set_fontweight("bold")
                ticklabel.set_color("#27ae60")
    else:
        ax.set_yticks(y)
        ax.set_yticklabels([])

    ax.set_xlabel("Costed regret")
    ax.set_title(title, pad=10)
    ax.set_xlim(left=0)
    ax.grid(True, axis="x", alpha=0.30, linestyle="--", linewidth=0.7)
    ax.set_axisbelow(True)


def main():
    # Order panels: increasing d, then increasing r
    panels = [
        ((55,  20), r"$d{=}55,\ r{=}20$"),
        ((105, 10), r"$d{=}105,\ r{=}10$"),
        ((105, 20), r"$d{=}105,\ r{=}20$"),
        ((105, 30), r"$d{=}105,\ r{=}30$"),
    ]

    fig, axes = plt.subplots(
        nrows=1, ncols=4,
        figsize=(20.0, 6.5),
        gridspec_kw={"width_ratios": [1.35, 1, 1, 1]},
    )

    for i, ((d, r), title) in enumerate(panels):
        plot_panel(axes[i], DATA[(d, r)], title, show_yticks=(i == 0))

    plt.tight_layout(w_pad=1.2)

    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(os.path.dirname(HERE), "figures",
                       "experiment_pendigits_extended.png")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    plt.savefig(OUT, bbox_inches="tight", dpi=300, facecolor="white")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
