"""
Phase-transition grid sweep + figure generation.

Runs SPSC, LinUCB, Oracle over (d, r) grid, then produces
experiment1_synthetic_phase.png (the 2-panel phase-transition figure).
"""

import os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import matplotlib.patheffects as pe
from scipy.interpolate import griddata

sys.path.insert(0, os.path.dirname(__file__))
from environments import LowRankLDSEnvironment
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB

K           = 4
T           = 5000
SIGMA_EPS   = 0.3
PROBE_EVERY = 30
PROBE_COST  = 0.1
WINDOW      = 100
N_ACTIONS   = 80
SPEC_RAD    = 0.99
SIGMA_ETA   = 0.04
N_SEEDS     = 10

D_VALS = [10, 20, 30, 45, 60, 80]
R_VALS = [1, 3, 5, 10, 15, 20]

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def make_env(d, r, seed):
    return LowRankLDSEnvironment(
        d=d, r=r, K=K, T=T,
        sigma_eps=SIGMA_EPS, spectral_radius=SPEC_RAD,
        n_actions=N_ACTIONS, sigma_eta=SIGMA_ETA,
        seed=seed * 100,
    )


def run_cell(d, r, n_seeds):
    spsc_finals, lin_finals, ora_finals = [], [], []
    for seed in range(n_seeds):
        env = make_env(d, r, seed)
        m = SPSC_Algorithm1(
            env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
            window=WINDOW, lam=1.0, delta=0.05, seed=seed,
            normalize_gamma_by_d=(d > 10),
        ).run()
        spsc_finals.append(m.cumulative_costed_regret[-1])

        env = make_env(d, r, seed)
        m = LinUCB(env, probe_cost=PROBE_COST, lam=1.0, delta=0.05,
                   seed=seed + 1000).run()
        lin_finals.append(m.cumulative_costed_regret[-1])

        env = make_env(d, r, seed)
        m = OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                         seed=seed + 2000).run()
        ora_finals.append(m.cumulative_costed_regret[-1])

    return (
        int(round(np.mean(spsc_finals))),
        int(round(np.mean(lin_finals))),
        int(round(np.mean(ora_finals))),
    )


def make_figure(data, out_path):
    d_vals = sorted(set(d for d, r in data))
    r_vals = sorted(set(r for d, r in data))
    T_SIXTH = T ** (1.0 / 6.0)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6),
                             gridspec_kw={"width_ratios": [1.15, 1]})

    # Panel (a): Contour map
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

    cs = ax.contour(DI, RI, ZI, levels=[1.0], colors=["black"],
                    linewidths=3, linestyles=["-"])
    ax.clabel(cs, fmt="ratio = 1.0", fontsize=9, inline_spacing=10,
              manual=[(35, 8)])

    d_line = np.linspace(8, 82, 100)
    r_line = np.clip(d_line - T_SIXTH, 0, 21)
    ax.plot(d_line, r_line, color="gray", ls="--", lw=2.5, alpha=0.6,
            label=f"Theory: $d - r = T^{{1/6}} \\approx {T_SIXTH:.1f}$")

    for (d, r), (s, l, o) in data.items():
        ratio = s / l
        if ratio < 0.95:
            ax.plot(d, r, "o", color="#1a5276", ms=7, mec="white", mew=1.2, zorder=5)
        elif ratio < 1.05:
            ax.plot(d, r, "s", color="#f39c12", ms=7, mec="white", mew=1.2, zorder=5)
        else:
            ax.plot(d, r, "^", color="#922b21", ms=7, mec="white", mew=1.2, zorder=5)

    ax.plot([], [], "o", color="#1a5276", ms=7, mec="white", label="SPSC wins ($<0.95$)")
    ax.plot([], [], "s", color="#f39c12", ms=7, mec="white", label="Tie ($0.95$--$1.05$)")
    ax.plot([], [], "^", color="#922b21", ms=7, mec="white", label="LinUCB wins ($>1.05$)")

    cb = plt.colorbar(cf, ax=ax, shrink=0.88, pad=0.02)
    cb.set_label("SPSC / LinUCB ratio", fontsize=10)
    cb.set_ticks([0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0])

    ax.set_xlabel("Ambient dimension $d$", fontsize=12)
    ax.set_ylabel("Latent rank $r$", fontsize=12)
    ax.set_title(f"(a) Phase-transition contour map ($n={N_SEEDS}$ seeds)",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9, edgecolor="gray")
    ax.set_xlim(8, 82)
    ax.set_ylim(0.5, 21)

    # Panel (b): Crossover ribbon
    ax = axes[1]
    r_groups = sorted(set(r for d, r in data))
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
            ax.plot(ds, rats, "o-", color=colors[idx], lw=2.5, ms=7,
                    label=f"$r = {r}$", zorder=3,
                    path_effects=[pe.Stroke(linewidth=4, foreground="white"),
                                  pe.Normal()])
            ax.plot(ds, thrs, ":", color=colors[idx], lw=1.2, alpha=0.5, zorder=2)

    ax.axhspan(0, 1, alpha=0.07, color="blue")
    ax.axhspan(1, 10, alpha=0.07, color="red")
    ax.axhline(1.0, color="black", lw=2, alpha=0.6)

    ax.text(68, 0.58, "SPSC\ndominates", fontsize=11, fontweight="bold",
            color="#1a5276", ha="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="#1a5276", alpha=0.85))
    ax.text(14, 3.2, "LinUCB\ndominates", fontsize=11, fontweight="bold",
            color="#922b21", ha="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="#922b21", alpha=0.85))

    ax.set_xlabel("Ambient dimension $d$", fontsize=12)
    ax.set_ylabel("SPSC / LinUCB regret ratio", fontsize=12)
    ax.set_title("(b) Ratio vs $d$ for each $r$\n"
                 "(solid = empirical, dotted = $\\sqrt{r/d}$ theory)",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=8.5, loc="upper right", title="Latent rank $r$",
              title_fontsize=9, framealpha=0.9, edgecolor="gray", ncol=2)
    ax.set_ylim(0.45, 6.5)
    ax.set_xlim(8, 82)
    ax.set_yscale("log")
    ax.set_yticks([0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0])
    ax.get_yaxis().set_major_formatter(
        plt.FuncFormatter(lambda y, _: f"{y:.1f}"))
    ax.grid(True, alpha=0.25, which="both")

    plt.tight_layout(w_pad=3)
    plt.savefig(out_path, bbox_inches="tight", dpi=200)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    total = sum(1 for d in D_VALS for r in R_VALS if r < d)
    done = 0
    data = {}

    print("=" * 60)
    print(f"Phase-transition grid: {total} cells, {N_SEEDS} seeds each")
    print(f"T={T}, K={K}, probe_every={PROBE_EVERY}, c={PROBE_COST}")
    print("=" * 60)

    for d in D_VALS:
        for r in R_VALS:
            if r >= d:
                continue
            done += 1
            print(f"[{done}/{total}] d={d}, r={r} ...", end=" ", flush=True)
            s, l, o = run_cell(d, r, N_SEEDS)
            data[(d, r)] = (s, l, o)
            ratio = s / l if l > 0 else float("inf")
            print(f"SPSC={s}, LinUCB={l}, Oracle={o}, ratio={ratio:.3f}")

    print("\nGenerating figure...")
    out_path = os.path.join(OUT_DIR, "experiment1_synthetic_phase.png")
    make_figure(data, out_path)
    print("Done.")
