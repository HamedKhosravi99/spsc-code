"""
Experiment: Rank misspecification robustness on Covertype at d=155.

Runs SPSC with specified rank r in {1, 3, 5, 10, 15, 20, 30, 50, 80}
on the Covertype environment with d=155, true effective rank r*=10.
Also runs LinUCB as a baseline.

At high r, SPSC should approach LinUCB (recovering full ambient space),
showing a U-shape: underestimation hurts, moderate overestimation helps,
extreme overestimation converges to ambient baseline.
"""

import os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import RealCovtypeEnvironmentV2
from algorithm import SPSC_Algorithm1, LinUCB, RunMetrics

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

D            = 155      # High ambient dimension — SPSC's strong regime
TRUE_R       = 10       # Environment built with r=10
TEST_RANKS   = [1, 3, 5, 10, 15, 20, 30, 50, 80]
PROBE_EVERY  = 10
PROBE_COST   = 0.02
WINDOW       = 600
SEG_SIZE     = 2500     # T = SEG_SIZE * N_SEGMENTS = 10,000
N_SEGMENTS   = 4
N_SEEDS      = 5
LAM          = 0.01
DELTA        = 0.05


def make_env(seed):
    return RealCovtypeEnvironmentV2(
        d=D, r=TRUE_R, n_actions=40, segment_size=SEG_SIZE,
        n_segments=N_SEGMENTS, seed=seed * 13 + 7,
    )


def final_regret(runs):
    vals = np.array([r.cumulative_costed_regret[-1] for r in runs])
    return vals.mean(), vals.std() / np.sqrt(len(vals))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

print("=" * 70)
print(f"Rank Misspecification Experiment (Covertype, d={D})")
print(f"True rank: {TRUE_R}, K={N_SEGMENTS}, "
      f"T={SEG_SIZE * N_SEGMENTS}, {N_SEEDS} seeds")
print("=" * 70)

# LinUCB baseline
print("\nRunning LinUCB baseline...")
linucb_runs = []
for seed in range(N_SEEDS):
    env = make_env(seed)
    linucb_runs.append(
        LinUCB(env, probe_cost=PROBE_COST, seed=seed).run()
    )
linucb_mu, linucb_se = final_regret(linucb_runs)
print(f"  LinUCB: {linucb_mu:.0f} +/- {linucb_se:.0f}")

# SPSC with varying rank
results = {}
for r_spec in TEST_RANKS:
    print(f"\nRunning SPSC with r={r_spec}...")
    runs = []
    for seed in range(N_SEEDS):
        env = make_env(seed)
        env.r = r_spec  # Override rank for SPSC
        run = SPSC_Algorithm1(
            env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
            normalize_gamma_by_d=True,
        ).run()
        env.r = TRUE_R  # Restore
        runs.append(run)

    mu, se = final_regret(runs)
    results[r_spec] = (mu, se)
    ratio_linucb = mu / linucb_mu
    marker = " <-- true rank" if r_spec == TRUE_R else ""
    print(f"  SPSC(r={r_spec:3d}): {mu:8.0f} +/- {se:4.0f}  "
          f"vs LinUCB: {ratio_linucb:.3f}{marker}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n" + "=" * 70)
print("SUMMARY TABLE")
print("=" * 70)
print(f"LinUCB baseline: {linucb_mu:.0f} +/- {linucb_se:.0f}")
print()

r10_mu = results[TRUE_R][0]
print(f"{'r':>5s}  {'SPSC regret':>12s}  {'vs LinUCB':>10s}  {'vs r=10':>8s}")
print("-" * 50)
for r_spec in TEST_RANKS:
    mu, se = results[r_spec]
    print(f"{r_spec:5d}  {mu:8.0f}+/-{se:3.0f}  "
          f"{mu/linucb_mu:10.3f}  {mu/r10_mu:8.3f}")

# LaTeX rows for the paper
print("\n% LaTeX table rows (for conference_additions.tex):")
# Only show r in {1,3,5,10,15,20,30} for the main table
main_ranks = [1, 3, 5, 10, 15, 20, 30]
print("SPSC regret & " + " & ".join(
    f"{results[r][0]:.0f}" for r in main_ranks) + " \\\\")
print("vs.\\ LinUCB & " + " & ".join(
    f"{results[r][0]/linucb_mu:.2f}" for r in main_ranks) + " \\\\")

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(1, 1, figsize=(8, 4.5))

ranks = TEST_RANKS
regrets = [results[r][0] for r in ranks]
errors = [results[r][1] for r in ranks]

ax.errorbar(ranks, regrets, yerr=errors, marker='o', color='#1f77b4',
            lw=2, ms=7, capsize=4, label='SPSC', zorder=3)
ax.axhline(linucb_mu, color='#d62728', ls='--', lw=1.5,
           label=f'LinUCB ({linucb_mu:.0f})')
ax.axvline(TRUE_R, color='gray', ls=':', lw=1, alpha=0.7,
           label=f'True rank $r^\\star={TRUE_R}$')

# Shade the "beats LinUCB" region
ax.fill_between([0, max(ranks)+5], 0, linucb_mu, alpha=0.05, color='blue')
ax.text(max(ranks)-10, linucb_mu * 0.95, 'SPSC wins', fontsize=9,
        color='#1f77b4', ha='right')

ax.set_xlabel('Specified rank $r$', fontsize=12)
ax.set_ylabel('Costed regret', fontsize=12)
ax.set_title(f'Rank misspecification robustness (Covertype, $d$={D}, '
             f'$r^\\star$={TRUE_R})', fontsize=12)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.2)
ax.set_xlim(0, max(ranks) + 5)

plt.tight_layout()
fname = os.path.join(OUT_DIR, "experiment_rank_misspec.png")
fig.savefig(fname, dpi=150, bbox_inches='tight')
plt.close()
print(f"\nSaved: {fname}")
print("\nDone.")
