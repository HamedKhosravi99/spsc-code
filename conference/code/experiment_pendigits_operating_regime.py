"""
Pendigits Operating Regime Study.

Grid: d in {5, 55, 105, 155}, r in {1, 10, 20, 30}
Algorithms: SPSC Alg 1, LinUCB (d-dim), Oracle LinUCB (r-dim, knows true subspace)
All use oracle change-points (reset at segment boundaries).

Prints each cell as it completes.
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

from environments import RealPendigitsEnvironment
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB, RunMetrics

# ---------------------------------------------------------------------------
# Fixed parameters
# ---------------------------------------------------------------------------
N_SEEDS     = 1
SEG_SIZE    = 500
N_SEGMENTS  = 10
PROBE_EVERY = 10
WINDOW      = 400
LAM         = 0.01
DELTA       = 0.05
PROBE_COST  = 0.02

D_VALUES = [5, 55, 105, 155]
R_VALUES = [1, 10, 20, 30]


def make_env(seed, d, r):
    return RealPendigitsEnvironment(
        d=d, r=r, n_actions=40, segment_size=SEG_SIZE,
        n_segments=N_SEGMENTS, seed=seed * 13 + 7,
    )


def run_cell(d, r):
    """Run one (d, r) cell. Returns dict with regret values."""
    spsc_reg, lin_reg, ora_reg = [], [], []

    for seed in range(N_SEEDS):
        # SPSC Alg 1
        env = make_env(seed, d, r)
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
        spsc_reg.append(m.cumulative_control_regret[-1])

        # LinUCB (d-dim, oracle CPs)
        env = make_env(seed, d, r)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 4000).run()
        lin_reg.append(m.cumulative_control_regret[-1])

        # Oracle LinUCB (r-dim, knows true subspace)
        env = make_env(seed, d, r)
        m = OracleLinUCB(env, window=10000, lam=LAM, delta=DELTA,
                         seed=seed + 1000).run()
        ora_reg.append(m.cumulative_control_regret[-1])

    return {
        "spsc": np.mean(spsc_reg),
        "linucb": np.mean(lin_reg),
        "oracle": np.mean(ora_reg),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 80)
    print("Pendigits Operating Regime Study")
    print(f"  d = {D_VALUES}")
    print(f"  r = {R_VALUES}")
    print(f"  lam={LAM}, probe_every={PROBE_EVERY}, window={WINDOW}")
    print(f"  N_SEEDS={N_SEEDS}, SEG_SIZE={SEG_SIZE}, N_SEGMENTS={N_SEGMENTS}")
    print("=" * 80)

    all_results = {}
    total_cells = len(D_VALUES) * len(R_VALUES)
    cell_idx = 0

    for d in D_VALUES:
        for r in R_VALUES:
            cell_idx += 1

            # Skip if r >= d
            if r >= d:
                print(f"\n[{cell_idx}/{total_cells}] d={d}, r={r} -- SKIPPED (r >= d)")
                all_results[(d, r)] = None
                continue

            t0 = time.time()
            print(f"\n[{cell_idx}/{total_cells}] Running d={d}, r={r} ...", flush=True)

            res = run_cell(d, r)
            elapsed = time.time() - t0
            all_results[(d, r)] = res

            spsc_ratio = res["spsc"] / res["linucb"] if res["linucb"] > 0 else float("inf")
            ora_ratio = res["oracle"] / res["linucb"] if res["linucb"] > 0 else float("inf")
            winner = "SPSC" if res["spsc"] < res["linucb"] else "LinUCB"

            print(f"  DONE in {elapsed:.1f}s")
            print(f"    SPSC Alg1  = {res['spsc']:.0f}")
            print(f"    LinUCB     = {res['linucb']:.0f}")
            print(f"    Oracle     = {res['oracle']:.0f}")
            print(f"    SPSC/Lin   = {spsc_ratio:.3f}  Oracle/Lin = {ora_ratio:.3f}  [{winner}]")
            sys.stdout.flush()

    # ---------------------------------------------------------------------------
    # Summary tables
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 100)
    print("OPERATING REGIME TABLE: Pendigits Real Data")
    print("=" * 100)

    # Table 1: SPSC/LinUCB ratio
    print("\nTable 1: SPSC Alg1 / LinUCB ratio (< 1 = SPSC wins)")
    header = f"{'d\\r':>6}"
    for r in R_VALUES:
        header += f"  {'r='+str(r):>8}"
    print(header)
    print("-" * (6 + 10 * len(R_VALUES)))
    for d in D_VALUES:
        row = f"{d:>6}"
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>8}"
            else:
                ratio = res["spsc"] / res["linucb"] if res["linucb"] > 0 else float("inf")
                marker = "*" if ratio < 1.0 else " "
                row += f"  {ratio:>7.3f}{marker}"
        print(row)

    # Table 2: Oracle/LinUCB ratio (theoretical ceiling)
    print(f"\nTable 2: Oracle / LinUCB ratio (theoretical ceiling)")
    header = f"{'d\\r':>6}"
    for r in R_VALUES:
        header += f"  {'r='+str(r):>8}"
    print(header)
    print("-" * (6 + 10 * len(R_VALUES)))
    for d in D_VALUES:
        row = f"{d:>6}"
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>8}"
            else:
                ratio = res["oracle"] / res["linucb"] if res["linucb"] > 0 else float("inf")
                row += f"  {ratio:>8.3f}"
        print(row)

    # Table 3: Absolute regrets
    print(f"\nTable 3: Absolute regrets")
    print(f"{'d':>4} {'r':>3}  {'SPSC':>10} {'LinUCB':>10} {'Oracle':>10}  {'SPSC/Lin':>9} {'Ora/Lin':>9}  {'sqrt(r/d)':>9}  Winner")
    print("-" * 90)
    for d in D_VALUES:
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                print(f"{d:>4} {r:>3}  {'SKIPPED':>10}")
                continue
            spsc_r = res["spsc"] / res["linucb"] if res["linucb"] > 0 else float("inf")
            ora_r = res["oracle"] / res["linucb"] if res["linucb"] > 0 else float("inf")
            theory = np.sqrt(r / d)
            best = min(res["spsc"], res["linucb"])
            winner = "SPSC" if res["spsc"] < res["linucb"] else "LinUCB"
            print(f"{d:>4} {r:>3}  {res['spsc']:>10.0f} {res['linucb']:>10.0f} "
                  f"{res['oracle']:>10.0f}  {spsc_r:>9.3f} {ora_r:>9.3f}  {theory:>9.3f}  {winner}")

    print("\n" + "=" * 100)
    print("Note: sqrt(r/d) is the theoretical regret ratio prediction.")
    print("* = SPSC wins (ratio < 1)")
    print("=" * 100)

    # ------------------------------------------------------------------
    # Figure: 3-panel operating regime plot
    # ------------------------------------------------------------------
    make_figure(all_results,
                os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "experiment_pendigits_operating_regime.png"))


def make_figure(all_results, out_path):
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    # ---- collect data into matrices (rows=d, cols=r) ----
    spsc_lin = np.full((len(D_VALUES), len(R_VALUES)), np.nan)
    ora_lin  = np.full((len(D_VALUES), len(R_VALUES)), np.nan)
    spsc_ora = np.full((len(D_VALUES), len(R_VALUES)), np.nan)
    theory   = np.full((len(D_VALUES), len(R_VALUES)), np.nan)

    for i, d in enumerate(D_VALUES):
        for j, r in enumerate(R_VALUES):
            res = all_results.get((d, r))
            if res is None:
                continue
            spsc_lin[i, j] = res["spsc"] / res["linucb"]
            ora_lin[i, j]  = res["oracle"] / res["linucb"]
            spsc_ora[i, j] = res["spsc"] / res["oracle"]
            theory[i, j]   = np.sqrt(r / d)

    d_labels = [str(d) for d in D_VALUES]
    r_labels = [str(r) for r in R_VALUES]

    # ================================================================
    # (a) SPSC/LinUCB heatmap
    # ================================================================
    ax = axes[0]
    # Diverging colormap centred at 1.0
    valid = spsc_lin[~np.isnan(spsc_lin)]
    vmin, vmax = min(valid.min(), 0.5), max(valid.max(), 1.5)
    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)
    im = ax.imshow(spsc_lin, cmap="RdYlGn_r", norm=norm,
                   aspect="auto", origin="upper")

    # Annotate cells
    for i in range(len(D_VALUES)):
        for j in range(len(R_VALUES)):
            v = spsc_lin[i, j]
            if np.isnan(v):
                ax.text(j, i, "--", ha="center", va="center",
                        fontsize=10, color="gray")
            else:
                color = "white" if abs(v - 1.0) > 0.6 else "black"
                bold = "bold" if v < 1.0 else "normal"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=11, fontweight=bold, color=color)

    ax.set_xticks(range(len(R_VALUES)))
    ax.set_xticklabels(r_labels)
    ax.set_yticks(range(len(D_VALUES)))
    ax.set_yticklabels(d_labels)
    ax.set_xlabel("Latent rank $r$", fontsize=11)
    ax.set_ylabel("Ambient dimension $d$", fontsize=11)
    ax.set_title("(a) SPSC / LinUCB regret ratio", fontsize=11)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("Ratio (< 1 = SPSC wins)", fontsize=9)

    # ================================================================
    # (b) Empirical ratio vs sqrt(r/d)
    # ================================================================
    ax = axes[1]
    # Scatter all valid cells
    emp_vals, thy_vals, d_for_color = [], [], []
    for i, d in enumerate(D_VALUES):
        for j, r in enumerate(R_VALUES):
            if np.isnan(spsc_lin[i, j]):
                continue
            emp_vals.append(spsc_lin[i, j])
            thy_vals.append(theory[i, j])
            d_for_color.append(d)

    emp_vals = np.array(emp_vals)
    thy_vals = np.array(thy_vals)
    d_for_color = np.array(d_for_color)

    # Color by d
    d_colors = {5: "#d62728", 55: "#ff7f0e", 105: "#2ca02c", 155: "#1f77b4"}
    for d in D_VALUES:
        mask = d_for_color == d
        if mask.sum() == 0:
            continue
        ax.scatter(thy_vals[mask], emp_vals[mask], s=90, color=d_colors[d],
                   edgecolors="black", linewidths=0.5, zorder=3,
                   label=f"$d={d}$")

    # Reference line: empirical = sqrt(r/d)
    xx = np.linspace(0, 0.85, 100)
    ax.plot(xx, xx, "k--", lw=1.2, alpha=0.5, label=r"$y = \sqrt{r/d}$")
    # Reference line: ratio = 1
    ax.axhline(1.0, color="gray", ls=":", lw=1, alpha=0.6)

    ax.set_xlabel(r"Theoretical $\sqrt{r/d}$", fontsize=11)
    ax.set_ylabel("Empirical SPSC / LinUCB", fontsize=11)
    ax.set_title(r"(b) Empirical vs $\sqrt{r/d}$", fontsize=11)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_xlim(0, 0.85)
    ax.set_ylim(0.4, max(emp_vals.max() * 1.1, 1.5))

    # ================================================================
    # (c) SPSC / Oracle ratio (how much room to improve)
    # ================================================================
    ax = axes[2]
    valid_ora = spsc_ora.copy()
    # Cap for display (r=1 oracle is near 0 so ratio is huge)
    valid_ora = np.clip(valid_ora, 0, 500)

    norm2 = TwoSlopeNorm(vmin=1.0, vcenter=50, vmax=max(300, np.nanmax(valid_ora)))
    im2 = ax.imshow(valid_ora, cmap="YlOrRd", aspect="auto", origin="upper")

    for i in range(len(D_VALUES)):
        for j in range(len(R_VALUES)):
            v = spsc_ora[i, j]
            if np.isnan(v):
                ax.text(j, i, "--", ha="center", va="center",
                        fontsize=10, color="gray")
            else:
                if v > 100:
                    txt = f"{v:.0f}x"
                else:
                    txt = f"{v:.1f}x"
                color = "white" if v > 50 else "black"
                ax.text(j, i, txt, ha="center", va="center",
                        fontsize=10, color=color)

    ax.set_xticks(range(len(R_VALUES)))
    ax.set_xticklabels(r_labels)
    ax.set_yticks(range(len(D_VALUES)))
    ax.set_yticklabels(d_labels)
    ax.set_xlabel("Latent rank $r$", fontsize=11)
    ax.set_ylabel("Ambient dimension $d$", fontsize=11)
    ax.set_title("(c) SPSC / Oracle ratio", fontsize=11)
    cb2 = fig.colorbar(im2, ax=ax, fraction=0.046, pad=0.04)
    cb2.set_label("Ratio (closer to 1 = tighter)", fontsize=9)

    fig.suptitle(
        "Pendigits operating-regime study  "
        r"($T\!=\!5000$, $K\!=\!10$ segments, $\lambda\!=\!0.01$)",
        fontsize=11, y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", dpi=200)
    print(f"Saved: {out_path}")
