"""
Appendix Experiments A–C: Robustness and necessity.

Experiment A: Variance misspecification sweep
  - Injects delta_sigma into the s_t computation
  - Shows graceful degradation (supports Corollary 1)

Experiment B: Bounded cross-correlation sweep
  - Injects controlled eps_cross into the noise model
  - Shows graceful O(eps_cross * T) degradation (supports Cor. 2 / Remark 7)

Experiment C: Imperfect coverage sweep
  - Restricts probe directions to a lower-dimensional subspace
  - Shows recovery failure / regret blow-up (supports Props. 6–8 / Thms. 13–14)

All use d=4, r=1, K=4, T=6000, 10 seeds.
"""

import os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import LowRankLDSEnvironment
from algorithm import K_inverse, RunMetrics, OracleLinUCB, LinUCB, SPSC_Robustness

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Common parameters
D, R, K, T = 4, 1, 4, 6000
SIGMA_EPS = 0.3
SPEC_RAD = 0.99
SIGMA_ETA = 0.04
N_ACTIONS = 80
PROBE_EVERY = 30
PROBE_COST = 0.1
WINDOW = 100
N_SEEDS = 10


# =========================================================================
# Helpers
# =========================================================================

def final_stats(runs, attr="cumulative_costed_regret"):
    vals = np.array([getattr(r, attr)[-1] for r in runs])
    return vals.mean(), vals.std() / np.sqrt(len(vals))

def mean_subspace_error(runs):
    """Average late-segment subspace error (last 20% of each segment)."""
    errs = []
    for run in runs:
        se = run.subspace_error
        # Forward-fill NaNs
        last = np.nan
        for i in range(len(se)):
            if np.isnan(se[i]):
                se[i] = last
            else:
                last = se[i]
        # Take last 20% of horizon
        n = len(se)
        errs.append(np.nanmean(se[int(0.8*n):]))
    return np.mean(errs), np.std(errs) / np.sqrt(len(errs))


def make_env(seed):
    return LowRankLDSEnvironment(
        d=D, r=R, K=K, T=T, sigma_eps=SIGMA_EPS,
        spectral_radius=SPEC_RAD, n_actions=N_ACTIONS,
        sigma_eta=SIGMA_ETA, seed=seed * 100)


# =========================================================================
# Experiment A: Variance misspecification sweep
# =========================================================================

print("=" * 70)
print("Experiment A: Variance misspecification sweep")
print("=" * 70)

delta_sigmas = [0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
results_a = []

for ds in delta_sigmas:
    runs = []
    for seed in range(N_SEEDS):
        env = make_env(seed)
        runs.append(SPSC_Robustness(
            env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
            window=WINDOW, delta_sigma=ds, seed=seed).run())
    mu_reg, se_reg = final_stats(runs)
    mu_sub, se_sub = mean_subspace_error(runs)
    results_a.append((ds, mu_reg, se_reg, mu_sub, se_sub))
    print(f"  delta_sigma={ds:6.3f}  regret={mu_reg:7.0f}±{se_reg:4.0f}  "
          f"subspace_err={mu_sub:.4f}±{se_sub:.4f}")


# =========================================================================
# Experiment B: Cross-correlation sweep
# =========================================================================

print("\n" + "=" * 70)
print("Experiment B: Bounded cross-correlation sweep")
print("=" * 70)

eps_crosses = [0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
results_b = []

for ec in eps_crosses:
    runs = []
    for seed in range(N_SEEDS):
        env = make_env(seed)
        runs.append(SPSC_Robustness(
            env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
            window=WINDOW, eps_cross=ec, seed=seed).run())
    mu_reg, se_reg = final_stats(runs)
    mu_sub, se_sub = mean_subspace_error(runs)
    results_b.append((ec, mu_reg, se_reg, mu_sub, se_sub))
    print(f"  eps_cross={ec:6.3f}  regret={mu_reg:7.0f}±{se_reg:4.0f}  "
          f"subspace_err={mu_sub:.4f}±{se_sub:.4f}")


# =========================================================================
# Experiment C: Imperfect coverage sweep
# =========================================================================

print("\n" + "=" * 70)
print("Experiment C: Imperfect probe coverage sweep")
print("=" * 70)

coverage_dims = [1, 2, 3, D]  # D=4 is full coverage
results_c = []

# Also run LinUCB as reference
linucb_runs = []
for seed in range(N_SEEDS):
    env = make_env(seed)
    linucb_runs.append(LinUCB(env, probe_cost=PROBE_COST, seed=seed).run())
linucb_mu, linucb_se = final_stats(linucb_runs)
print(f"  LinUCB (reference): regret={linucb_mu:.0f}±{linucb_se:.0f}")

for cd in coverage_dims:
    runs = []
    for seed in range(N_SEEDS):
        env = make_env(seed)
        runs.append(SPSC_Robustness(
            env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
            window=WINDOW, coverage_dim=cd, seed=seed).run())
    mu_reg, se_reg = final_stats(runs)
    mu_sub, se_sub = mean_subspace_error(runs)
    results_c.append((cd, mu_reg, se_reg, mu_sub, se_sub))
    label = f"coverage={cd}/{D}" + (" (full)" if cd == D else "")
    print(f"  {label:<22s}  regret={mu_reg:7.0f}±{se_reg:4.0f}  "
          f"subspace_err={mu_sub:.4f}±{se_sub:.4f}")


# =========================================================================
# Plot: 3-panel figure
# =========================================================================

plt.rcParams.update({
    'text.color': 'black',
    'axes.labelcolor': 'black',
    'xtick.color': 'black',
    'ytick.color': 'black',
    'axes.edgecolor': 'black',
    'font.size': 10,
})
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

# Standard academic colors: black + dark gray, distinguishable by marker/linestyle
C_REG = 'black'
C_SUB = '#555555'
C_BAR_BAD = '#888888'
C_BAR_GOOD = 'black'

# --- Panel A: Variance misspecification ---
ax = axes[0]
xs = [r[0] for r in results_a]
regrets = [r[1] for r in results_a]
reg_ses = [r[2] for r in results_a]
sub_errs = [r[3] for r in results_a]
sub_ses = [r[4] for r in results_a]

ax.errorbar(xs, regrets, yerr=reg_ses, marker='o', color=C_REG,
            label='Costed regret', capsize=3, lw=1.5, ms=5)
ax.set_xlabel(r'Variance misspecification $|\delta_\sigma|$')
ax.set_ylabel('Costed regret')

ax2 = ax.twinx()
ax2.errorbar(xs, sub_errs, yerr=sub_ses, marker='s', color=C_SUB,
             label='Subspace error', capsize=3, lw=1.5, ls='--', ms=5)
ax2.set_ylabel('Late-segment subspace error')

ax.set_title('(a) Variance misspecification\n(Corollary 1)')
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc='upper left')

# --- Panel B: Cross-correlation ---
ax = axes[1]
xs = [r[0] for r in results_b]
regrets = [r[1] for r in results_b]
reg_ses = [r[2] for r in results_b]
sub_errs = [r[3] for r in results_b]
sub_ses = [r[4] for r in results_b]

ax.errorbar(xs, regrets, yerr=reg_ses, marker='o', color=C_REG,
            label='Costed regret', capsize=3, lw=1.5, ms=5)
ax.set_xlabel(r'Cross-correlation $\epsilon_\times$')
ax.set_ylabel('Costed regret')

ax2 = ax.twinx()
ax2.errorbar(xs, sub_errs, yerr=sub_ses, marker='s', color=C_SUB,
             label='Subspace error', capsize=3, lw=1.5, ls='--', ms=5)
ax2.set_ylabel('Late-segment subspace error')

ax.set_title('(b) Cross-correlation relaxation\n(Corollary 2)')
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc='upper left')

# --- Panel C: Coverage restriction ---
ax = axes[2]
xs = [r[0] for r in results_c]
regrets = [r[1] for r in results_c]
reg_ses = [r[2] for r in results_c]
sub_errs = [r[3] for r in results_c]
sub_ses = [r[4] for r in results_c]

bar_colors = [C_BAR_BAD if x < D else C_BAR_GOOD for x in xs]
ax.bar(range(len(xs)), regrets, yerr=reg_ses, capsize=4,
       color=bar_colors, alpha=0.8, edgecolor='black', linewidth=0.8)
ax.axhline(linucb_mu, color='black', ls=':', lw=1.5, label=f'LinUCB ({linucb_mu:.0f})')
ax.set_xticks(range(len(xs)))
ax.set_xticklabels([f'{x}/{D}' for x in xs])
ax.set_xlabel(f'Probe coverage (dims out of $d$={D})')
ax.set_ylabel('Costed regret')
ax.set_title('(c) Imperfect coverage\n(Propositions 6\u20138)')
ax.legend(fontsize=8)

# Add subspace error annotations
for i, (cd, reg, _, sub, _) in enumerate(results_c):
    ax.annotate(f'$\\varepsilon$={sub:.2f}', (i, reg + reg_ses[i] + 50),
                ha='center', fontsize=7, color='black')

fig.suptitle(f'Robustness and necessity experiments '
             f'($d$={D}, $r$={R}, $K$={K}, $T$={T}, {N_SEEDS} seeds)',
             fontsize=11, y=1.02, color='black')

plt.tight_layout()

fname = os.path.join(OUT_DIR, "experiment_robustness_abc.png")
fig.savefig(fname, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nSaved: {fname}")
print("\nDone.")
