"""
Plot-only re-render of `experiment_synthetic_extended.png`
(SPSC-Alg.1 vs SPSC-Adaptive: d-sweep + oracle-quality sweep)
from the cached per-seed JSON in code/results/experiment_synthetic_comparison.json.

Produces a high-resolution, large-font, paper-ready 2-panel figure.

Usage:
    cd code/
    python3 plot_synthetic_extended_from_json.py
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
    "axes.linewidth": 1.4,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "xtick.major.width": 1.2,
    "ytick.major.width": 1.2,
    "xtick.major.size": 5,
    "ytick.major.size": 5,
    "legend.fontsize": 13,
    "legend.frameon": True,
    "legend.framealpha": 0.95,
    "legend.edgecolor": "0.3",
    "lines.linewidth": 2.4,
    "lines.markersize": 9,
    "lines.markeredgewidth": 1.4,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
})

# -------------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(HERE, "results", "experiment_synthetic_comparison.json")
OUT_PATH = os.path.join(os.path.dirname(HERE), "figures",
                        "experiment_synthetic_extended.png")

# -------------------------------------------------------------------------
# Method styling — strong, paper-friendly contrast
# -------------------------------------------------------------------------
STYLE = {
    "SPSC-Alg1":     dict(color="#1f4e79", marker="o", linestyle="-",
                          label="SPSC Alg. 1"),
    "SPSC-Adaptive": dict(color="#c0392b", marker="s", linestyle="-",
                          label="SPSC-Adaptive"),
    "LinUCB":        dict(color="#555555", marker="^", linestyle="--",
                          label="LinUCB"),
}


def mean_se(seed_values):
    arr = np.asarray(seed_values, dtype=float)
    n = len(arr)
    return float(arr.mean()), float(arr.std(ddof=1) / np.sqrt(n))


def plot_panel(ax, x_vals, x_label, sweep_dict, title):
    for method, sty in STYLE.items():
        means, ses = [], []
        for x in x_vals:
            key = list(sweep_dict.keys())[x_vals.index(x)]
            mu, se = mean_se(sweep_dict[key][method])
            means.append(mu)
            ses.append(se)
        means = np.array(means)
        ses = np.array(ses)
        ax.errorbar(x_vals, means, yerr=ses,
                    color=sty["color"], marker=sty["marker"],
                    linestyle=sty["linestyle"], label=sty["label"],
                    capsize=4, capthick=1.4, elinewidth=1.4,
                    markeredgecolor="black")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Final cumulative regret")
    ax.set_title(title, pad=10)
    ax.legend(loc="best")


def main():
    with open(JSON_PATH) as f:
        data = json.load(f)

    cfg = data["config"]
    sweep1 = data["results"]["sweep1_d"]
    sweep2 = data["results"]["sweep2_oracle_quality"]

    d_vals = sorted(int(k.split("=")[1]) for k in sweep1.keys())
    k_vals = sorted(int(k.split("=")[1]) for k in sweep2.keys())

    # Re-key in the order we want to plot
    sweep1_ord = {f"d={d}": sweep1[f"d={d}"] for d in d_vals}
    sweep2_ord = {f"K_oracle={k}": sweep2[f"K_oracle={k}"] for k in k_vals}

    # ---------------------------------------------------------------
    # Figure layout: 2 stacked panels, generous height for readability
    # ---------------------------------------------------------------
    fig, (ax_top, ax_bot) = plt.subplots(
        nrows=2, ncols=1,
        figsize=(9.5, 9.0),
        gridspec_kw={"hspace": 0.36},
    )

    # Top panel: d-sweep
    plot_panel(
        ax_top, d_vals, r"Ambient dimension $d$",
        sweep1_ord,
        title=(r"\textbf{(a)} $d$-sweep with correct oracle "
               rf"($K_{{\mathrm{{oracle}}}}=K_{{\mathrm{{real}}}}={cfg['K']}$, $r={cfg['R_FIXED']}$)")
        if False else
        rf"(a) $d$-sweep with correct oracle  ($K_{{\rm oracle}}=K_{{\rm real}}={cfg['K']}$, $r={cfg['R_FIXED']}$)",
    )

    # Bottom panel: oracle-quality sweep (K_oracle varies; K_real fixed)
    plot_panel(
        ax_bot, k_vals, r"Oracle-supplied number of segments $K_{\rm oracle}$",
        sweep2_ord,
        title=(rf"(b) Oracle quality "
               rf"(true $K_{{\rm real}}={cfg['SWEEP2_K_REAL']}$, "
               rf"$d={cfg['SWEEP2_D']}$, $r={cfg['SWEEP2_R']}$)"),
    )

    # Mark the "true" K_real on the bottom panel
    ax_bot.axvline(cfg["SWEEP2_K_REAL"], color="green",
                   linestyle=":", linewidth=2.0, alpha=0.7,
                   label=rf"True $K_{{\rm real}}={cfg['SWEEP2_K_REAL']}$")
    # Re-draw legend on bottom panel to include the vline
    ax_bot.legend(loc="best")

    # Tight layout, save
    plt.tight_layout()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH, bbox_inches="tight", dpi=300, facecolor="white")
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
