"""
Experiment 1 (Final): Synthetic operating-regime benchmark.

Demonstrates the theory-predicted phase transition:
  - LinUCB wins at small d (probe cost exceeds dimensional savings)
  - SPSC wins at large d (r-dim exploitation advantage dominates)
  - Crossover at d - r ≈ T^{1/6}

Environment: piecewise-constant theta with structured (correlated) features,
matching the statistical structure of real-data benchmarks.
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import FancyArrowPatch

sys.path.insert(0, os.path.dirname(__file__))
from environment import LowRankLDSEnvironment
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB

# =========================================================================
# Parameters
# =========================================================================
DS = [5, 10, 20, 30, 45, 60, 80, 100]
RS = [1, 3, 5, 10, 15, 20]
K = 10
T = 5000
SIGMA_EPS = 0.3
SPEC_RAD = 0.99
SIGMA_ETA = 0.04
N_ACTIONS = 40
PROBE_EVERY = 50
PROBE_COST = 0.1
WINDOW = 400
LAM = 0.01
DELTA = 0.05
FEATURE_DECAY = 1.5
N_SEEDS = 10
T_SIXTH = T ** (1.0 / 6.0)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def final_stats(runs, attr="cumulative_costed_regret"):
    v = np.array([getattr(r, attr)[-1] for r in runs])
    return v.mean(), v.std() / np.sqrt(len(v))


# =========================================================================
# Run grid
# =========================================================================
results = {}

print(f"Synthetic Operating-Regime Benchmark (Final)")
print(f"T={T} K={K} pe={PROBE_EVERY} W={WINDOW} lam={LAM} fd={FEATURE_DECAY}")
print(f"Grid: d={DS}, r={RS}, seeds={N_SEEDS}")
print(f"T^(1/6)={T_SIXTH:.2f}")
print("-" * 80)

for d in DS:
    for r in RS:
        if r >= d:
            continue
        t0 = time.time()
        res = {"SPSC": [], "LinUCB": [], "Oracle": []}
        for seed in range(N_SEEDS):
            kw = dict(K=K, T=T, sigma_eps=SIGMA_EPS, spectral_radius=SPEC_RAD,
                      n_actions=N_ACTIONS, sigma_eta=SIGMA_ETA, seed=seed * 100,
                      piecewise_constant=True, feature_decay=FEATURE_DECAY)
            env = LowRankLDSEnvironment(d=d, r=r, **kw)
            res["SPSC"].append(SPSC_Algorithm1(
                env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                normalize_gamma_by_d=True).run())
            env2 = LowRankLDSEnvironment(d=d, r=r, **kw)
            res["LinUCB"].append(LinUCB(
                env2, lam=LAM, delta=DELTA, seed=seed).run())
            env3 = LowRankLDSEnvironment(d=d, r=r, **kw)
            res["Oracle"].append(OracleLinUCB(
                env3, window=WINDOW, lam=LAM, delta=DELTA, seed=seed).run())

        results[(d, r)] = res
        s, _ = final_stats(res["SPSC"])
        l, _ = final_stats(res["LinUCB"])
        o, _ = final_stats(res["Oracle"])
        print(f"d={d:3d} r={r:2d} | SPSC={s:7.0f} Lin={l:7.0f} Orc={o:7.0f} | "
              f"ratio={s/l:.3f} thr={np.sqrt(r/d):.3f} [{time.time()-t0:.0f}s]",
              flush=True)

# =========================================================================
# Collect ratio grids
# =========================================================================
valid = sorted(results.keys())
d_vals = sorted(set(d for d, r in valid))
r_vals = sorted(set(r for d, r in valid))

ratio_grid = np.full((len(r_vals), len(d_vals)), np.nan)
theory_grid = np.full((len(r_vals), len(d_vals)), np.nan)
oracle_grid = np.full((len(r_vals), len(d_vals)), np.nan)

for i, r in enumerate(r_vals):
    for j, d in enumerate(d_vals):
        if (d, r) not in results:
            continue
        s, _ = final_stats(results[(d, r)]["SPSC"])
        l, _ = final_stats(results[(d, r)]["LinUCB"])
        o, _ = final_stats(results[(d, r)]["Oracle"])
        ratio_grid[i, j] = s / l if l > 0 else np.nan
        # New theory ratio (Thm 1 with d^{2/3} probe term):
        #   SPSC/LinUCB = r/d + d^{-1/3}(T/K)^{1/6}
        theory_grid[i, j] = r / d + (T / K) ** (1.0 / 6.0) / d ** (1.0 / 3.0)
        oracle_grid[i, j] = o / l if l > 0 else np.nan

# =========================================================================
# Figure — 4-panel
# =========================================================================
fig = plt.figure(figsize=(18, 14))

# --- Panel (a): Phase-transition heatmap ---
ax1 = fig.add_subplot(2, 2, 1)
norm1 = TwoSlopeNorm(vmin=0.3, vcenter=1.0, vmax=3.0)
im1 = ax1.imshow(ratio_grid, cmap="RdYlBu_r", norm=norm1, aspect="auto",
                  origin="lower")
for i in range(len(r_vals)):
    for j in range(len(d_vals)):
        v = ratio_grid[i, j]
        if np.isnan(v):
            ax1.text(j, i, "—", ha="center", va="center", fontsize=8, color="gray")
        else:
            color = "white" if (v < 0.6 or v > 2.0) else "black"
            ax1.text(j, i, f"{v:.2f}", ha="center", va="center",
                     fontsize=9, fontweight="bold", color=color)
ax1.set_xticks(range(len(d_vals)))
ax1.set_xticklabels(d_vals)
ax1.set_yticks(range(len(r_vals)))
ax1.set_yticklabels(r_vals)
ax1.set_xlabel("Ambient dimension $d$", fontsize=12)
ax1.set_ylabel("Latent rank $r$", fontsize=12)
ax1.set_title("(a) SPSC / LinUCB regret ratio\n(blue < 1 = SPSC wins)", fontsize=12)
cb1 = plt.colorbar(im1, ax=ax1, shrink=0.85)
cb1.set_label("Ratio", fontsize=10)

# Draw the new theory boundary CURVE in (d, r) space:
#     d - r = d^{2/3} (T/K)^{1/6}    <=>    r = d - d^{2/3}(T/K)^{1/6}
factor = (T / K) ** (1.0 / 6.0)
for i, r in enumerate(r_vals):
    # Solve  r = d - d^{2/3} * factor  for d (numerically: scan over d).
    d_grid = np.linspace(d_vals[0], d_vals[-1], 400)
    r_pred = d_grid - d_grid ** (2.0 / 3.0) * factor
    idx = np.argmin(np.abs(r_pred - r))
    d_at_r = d_grid[idx]
    if d_vals[0] <= d_at_r <= d_vals[-1] and abs(r_pred[idx] - r) < 1.5:
        j_frac = np.interp(d_at_r, d_vals, range(len(d_vals)))
        ax1.plot(j_frac, i, "k*", markersize=11, zorder=5)
ax1.plot([], [], "k*", markersize=11,
         label=f"Theory boundary $d - r = d^{{2/3}}(T/K)^{{1/6}}$")
ax1.legend(loc="upper left", fontsize=9)

# --- Panel (b): Ratio vs d for each r (line plot) ---
ax2 = fig.add_subplot(2, 2, 2)
cmap = plt.cm.viridis
colors = [cmap(i / max(len(r_vals) - 1, 1)) for i in range(len(r_vals))]

for i, r in enumerate(r_vals):
    ds_valid = []
    rats_valid = []
    thrs_valid = []
    for j, d in enumerate(d_vals):
        if not np.isnan(ratio_grid[i, j]):
            ds_valid.append(d)
            rats_valid.append(ratio_grid[i, j])
            thrs_valid.append(theory_grid[i, j])
    if ds_valid:
        ax2.plot(ds_valid, rats_valid, "o-", color=colors[i], lw=2,
                 markersize=6, label=f"$r={r}$", zorder=3)
        ax2.plot(ds_valid, thrs_valid, "--", color=colors[i], lw=1,
                 alpha=0.5, zorder=2)

ax2.axhline(1.0, color="black", ls=":", lw=1.5, alpha=0.7)
ax2.fill_between([d_vals[0], d_vals[-1]], 0, 1, alpha=0.06, color="blue",
                  label="SPSC wins")
ax2.fill_between([d_vals[0], d_vals[-1]], 1, 5, alpha=0.06, color="red",
                  label="LinUCB wins")
ax2.set_xlabel("Ambient dimension $d$", fontsize=12)
ax2.set_ylabel("SPSC / LinUCB ratio", fontsize=12)
ax2.set_title("(b) Regret ratio vs $d$\n"
              "(solid = empirical, dashed = theory $r/d + d^{-1/3}(T/K)^{1/6}$)",
              fontsize=12)
ax2.legend(fontsize=8, ncol=2, loc="upper right")
ax2.set_ylim(0, 4)
ax2.set_xlim(d_vals[0] - 2, d_vals[-1] + 2)

# --- Panel (c): Empirical ratio vs theory sqrt(r/d) scatter ---
ax3 = fig.add_subplot(2, 2, 3)
emp_all = []
thr_all = []
d_all = []
r_all = []
for i, r in enumerate(r_vals):
    for j, d in enumerate(d_vals):
        if not np.isnan(ratio_grid[i, j]):
            emp_all.append(ratio_grid[i, j])
            thr_all.append(theory_grid[i, j])
            d_all.append(d)
            r_all.append(r)

emp_all = np.array(emp_all)
thr_all = np.array(thr_all)
d_all = np.array(d_all)

# Color by d
sc = ax3.scatter(thr_all, emp_all, c=d_all, cmap="plasma", s=80,
                  edgecolors="black", linewidths=0.5, zorder=3)
ax3.plot([0, 1.5], [0, 1.5], "k--", lw=1, alpha=0.4, label="Empirical = Theory")
ax3.axhline(1.0, color="gray", ls=":", lw=1, alpha=0.5)
ax3.set_xlabel(r"Theory ratio: $r/d + d^{-1/3}(T/K)^{1/6}$", fontsize=12)
ax3.set_ylabel("Empirical: SPSC / LinUCB", fontsize=12)
ax3.set_title("(c) Theory vs empirical ratio\n(colored by $d$)", fontsize=12)
cb3 = plt.colorbar(sc, ax=ax3, shrink=0.85)
cb3.set_label("$d$", fontsize=10)
ax3.legend(fontsize=9)
ax3.set_xlim(0, 1.0)
ax3.set_ylim(0, 4.0)

# --- Panel (d): Regret decomposition stacked bars ---
ax4 = fig.add_subplot(2, 2, 4)
# Pick r=10 slice for decomposition
r_target = 10
ds_slice = [d for d in d_vals if (d, r_target) in results]
spsc_vals = []
lin_vals = []
orc_vals = []
for d in ds_slice:
    s, _ = final_stats(results[(d, r_target)]["SPSC"])
    l, _ = final_stats(results[(d, r_target)]["LinUCB"])
    o, _ = final_stats(results[(d, r_target)]["Oracle"])
    spsc_vals.append(s)
    lin_vals.append(l)
    orc_vals.append(o)

x = np.arange(len(ds_slice))
w = 0.28
bars_s = ax4.bar(x - w, spsc_vals, w, label="SPSC", color="#1f77b4", edgecolor="black", lw=0.5)
bars_l = ax4.bar(x, lin_vals, w, label="LinUCB", color="#d62728", edgecolor="black", lw=0.5)
bars_o = ax4.bar(x + w, orc_vals, w, label="Oracle", color="#2ca02c", edgecolor="black", lw=0.5)

ax4.set_xticks(x)
ax4.set_xticklabels([f"$d$={d}" for d in ds_slice], fontsize=9)
ax4.set_ylabel("Cumulative costed regret", fontsize=12)
ax4.set_title(f"(d) Regret comparison at $r={r_target}$\n(SPSC overtakes LinUCB as $d$ grows)",
              fontsize=12)
ax4.legend(fontsize=9)

# Annotate crossover
for i in range(len(ds_slice)):
    if spsc_vals[i] < lin_vals[i]:
        ax4.annotate("SPSC\nwins", xy=(x[i] - w, spsc_vals[i]),
                     xytext=(x[i] - w, spsc_vals[i] + 200),
                     fontsize=7, ha="center", color="#1f77b4",
                     arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=0.8))
        break

fig.suptitle(
    "Synthetic Operating-Regime Benchmark: Phase Transition in SPSC vs LinUCB\n"
    f"$T$={T}, $K$={K}, probe every {PROBE_EVERY}, "
    f"feature decay={FEATURE_DECAY}, {N_SEEDS} seeds",
    fontsize=14, fontweight="bold", y=1.01)

plt.tight_layout()
# Save to the filename the paper actually references in §5.1.
out_path = os.path.join(OUT_DIR, "experiment1_synthetic_phase.png")
plt.savefig(out_path, bbox_inches="tight", dpi=150)
print(f"\nSaved: {out_path}")

# =========================================================================
# Summary table
# =========================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"{'d':>4} {'r':>3} | {'SPSC':>8} {'LinUCB':>8} {'Oracle':>8} | "
      f"{'ratio':>6} {'theory':>6} | {'verdict':>12}")
print("-" * 80)
for d in d_vals:
    for r in r_vals:
        if (d, r) not in results:
            continue
        s, _ = final_stats(results[(d, r)]["SPSC"])
        l, _ = final_stats(results[(d, r)]["LinUCB"])
        o, _ = final_stats(results[(d, r)]["Oracle"])
        rat = s / l
        thr = np.sqrt(r / d)
        verdict = "SPSC wins" if rat < 0.95 else ("tie" if rat < 1.05 else "LinUCB wins")
        print(f"{d:4d} {r:3d} | {s:8.0f} {l:8.0f} {o:8.0f} | "
              f"{rat:6.3f} {thr:6.3f} | {verdict:>12}")
print("=" * 80)
