"""
Plot-only re-render of the oracle-quality figure
(`figures/experiment_oracle_quality.png`)
from the cached per-seed JSON in
`code/results/experiment_oracle_quality.json`.

Single-panel, paper-quality figure with no inline title (the caption
in the .tex carries the description).

Usage:
    cd code/
    python3 plot_oracle_quality.py
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# -------------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(HERE, "results", "experiment_oracle_quality.json")
FIG_PATH = os.path.join(os.path.dirname(HERE), "figures",
                        "experiment_oracle_quality.png")


# -------------------------------------------------------------------------
# Paper-quality matplotlib settings
# -------------------------------------------------------------------------
plt.rcParams.update({
    "figure.dpi":         300,
    "savefig.dpi":        300,
    "font.family":        "serif",
    "font.size":          14,
    "axes.labelsize":     16,
    "axes.linewidth":     1.4,
    "xtick.labelsize":    13,
    "ytick.labelsize":    13,
    "xtick.major.width":  1.2,
    "ytick.major.width":  1.2,
    "xtick.major.size":   5,
    "ytick.major.size":   5,
    "legend.fontsize":    13,
    "legend.frameon":     True,
    "legend.framealpha":  0.95,
    "legend.edgecolor":   "0.3",
    "lines.linewidth":    2.6,
    "lines.markersize":   10,
    "lines.markeredgewidth": 1.4,
    "axes.grid":          True,
    "grid.alpha":         0.30,
    "grid.linestyle":     "--",
    "grid.linewidth":     0.7,
    "axes.axisbelow":     True,
})

STYLE = {
    "SPSC-Alg1":     ("#1f4e79", "o",  "-",  "SPSC Alg. 1"),
    "SPSC-Adaptive": ("#c0392b", "s",  "-",  "SPSC-Adaptive"),
    "LinUCB":        ("#555555", "^",  "--", "LinUCB"),
}


def main():
    with open(JSON_PATH) as f:
        data = json.load(f)

    cfg = data["config"]
    results = data["results"]
    K_vals = cfg["K_ORACLE_SWEEP"]
    K_real = cfg["K_REAL"]

    fig, ax = plt.subplots(figsize=(10.0, 6.0))

    for method, (color, marker, ls, label) in STYLE.items():
        means, ses = [], []
        for K in K_vals:
            vals = np.array(results[f"K_oracle={K}"][method])
            means.append(vals.mean())
            ses.append(vals.std(ddof=1) / np.sqrt(len(vals)))
        means = np.array(means)
        ses = np.array(ses)
        ax.errorbar(
            K_vals, means, yerr=ses,
            color=color, marker=marker, linestyle=ls, label=label,
            capsize=4, capthick=1.4, elinewidth=1.4,
            markeredgecolor="black",
        )

    # Mark the true K_real
    ax.axvline(
        K_real, color="#27ae60", linestyle=":", linewidth=2.4, alpha=0.85,
        label=rf"True $K_{{\rm real}} = {K_real}$",
    )

    ax.set_xlabel(r"Oracle-supplied number of segments "
                  r"$K_{\rm oracle}$ (log scale)")
    ax.set_ylabel("Final cumulative costed regret")
    ax.set_xscale("log")
    ax.set_xticks(K_vals)
    ax.set_xticklabels([str(K) for K in K_vals])
    ax.legend(loc="upper left", framealpha=0.93)

    plt.tight_layout()
    os.makedirs(os.path.dirname(FIG_PATH), exist_ok=True)
    plt.savefig(FIG_PATH, bbox_inches="tight", dpi=300, facecolor="white")
    print(f"Saved figure to {FIG_PATH}")


if __name__ == "__main__":
    main()
