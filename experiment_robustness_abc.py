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

sys.path.insert(0, os.path.dirname(__file__))
from environment import LowRankLDSEnvironment
from algorithm import K_inverse, RunMetrics, OracleLinUCB, LinUCB

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
# Modified SPSC that accepts injected misspecification / correlation / coverage
# =========================================================================

class SPSC_Robustness:
    """
    SPSC Algorithm 1 with three controllable robustness knobs:

    delta_sigma:    variance misspecification (s_t uses sigma^2 + delta_sigma)
    eps_cross:      cross-correlation magnitude (noise acquires eps_cross * theta component)
    coverage_dim:   probe restricted to first coverage_dim coordinates (d = full coverage)
    """

    def __init__(self, env, probe_every=30, probe_cost=0.1, window=200,
                 lam=1.0, delta=0.05, seed=0,
                 delta_sigma=0.0, eps_cross=0.0, coverage_dim=None):
        self.env = env
        self.probe_every = probe_every
        self.c = probe_cost
        self.W = window
        self.lam = lam
        self.delta = delta
        self.rng = np.random.default_rng(seed)

        d, r = env.d, env.r
        self.d, self.r = d, r
        self.L_x = env.L_x
        self.sigma_eps = env.sigma_eps
        self.S = env.S

        # Robustness knobs
        self.delta_sigma = delta_sigma
        self.eps_cross = eps_cross
        self.coverage_dim = coverage_dim if coverage_dim is not None else d

    def _is_probe(self, t, k):
        seg_start = self.env.tau[k]
        if t == seg_start:
            return True
        return ((t - seg_start) % self.probe_every) == 0

    def _beta(self, n):
        eff = min(n, self.W)
        arg = max(1.0 + eff * self.L_x**2 / self.lam, 1.0 + 1e-12)
        return (self.sigma_eps * np.sqrt(self.r * np.log(arg / self.delta))
                + np.sqrt(self.lam) * self.S)

    def _gamma(self, m, G_norms):
        if m < 2:
            return float(self.S)
        K_inv_op = (self.d + 2) / (2.0 * self.d)
        R_X_hat = (float(np.percentile(G_norms, 90)) if len(G_norms) >= 2
                   else K_inv_op * self.d * ((self.S + 1.0)**2 + self.sigma_eps**2))
        return 8.0 * self.S * R_X_hat * np.sqrt(
            np.log(2.0 * self.d / self.delta) / m)

    def run(self):
        env = self.env
        d, r, T = self.d, self.r, env.T
        metrics = RunMetrics(name="SPSC-Robust", T=T)

        M_sum = np.zeros((d, d))
        U_hat = np.eye(d, r)
        m_probe_seg = 0
        current_k = -1
        G_norms = []
        expl_buf = []

        # Misspecified sigma^2 used in s_t
        sigma_sq_used = self.sigma_eps**2 + self.delta_sigma

        for t in range(T):
            k = env.seg_of[t]
            if k != current_k:
                M_sum = np.zeros((d, d))
                m_probe_seg = 0
                G_norms = []
                expl_buf = []
                current_k = k

            action_set = env.get_action_set(t, rng=self.rng)
            r_opt = env.optimal_reward(action_set, t)

            if self._is_probe(t, k):
                metrics.probe_flags[t] = True

                # Draw probe — possibly restricted coverage
                z_probe = self.rng.standard_normal(d)
                if self.coverage_dim < d:
                    z_probe[self.coverage_dim:] = 0.0  # zero out uncovered dims
                norm_z = np.linalg.norm(z_probe)
                if norm_z < 1e-12:
                    z_probe[0] = 1.0
                    norm_z = 1.0
                u_t = np.sqrt(d) * z_probe / norm_z

                # Inject cross-correlation: noise = eps + eps_cross * (u^T theta)
                eps_base = self.rng.normal(0.0, self.sigma_eps)
                eps_base = np.clip(eps_base, -env.L_eps, env.L_eps)
                cross_term = self.eps_cross * float(u_t @ env.theta[t])
                y_t = float(u_t @ env.theta[t]) + eps_base + cross_term

                # Subspace estimation with possibly misspecified sigma^2
                s_t = y_t**2 - sigma_sq_used
                G_t = K_inverse(s_t * np.outer(u_t, u_t), d)

                G_norms.append(float(np.linalg.norm(G_t, ord=2)))
                M_sum += G_t
                m_probe_seg += 1

                if m_probe_seg >= 2:
                    M_hat = M_sum / m_probe_seg
                    _, eig_vecs = np.linalg.eigh(M_hat)
                    U_hat = eig_vecs[:, -r:]

                P_true = env.segment_projector(k)
                P_hat = U_hat @ U_hat.T
                metrics.subspace_error[t] = np.linalg.norm(P_hat - P_true, ord=2)

                r_t = float(u_t @ env.theta[t])
                metrics.control_regret[t] = r_opt - r_t
                metrics.costed_regret[t] = r_opt - r_t + self.c

            else:
                win = [(xs, ys) for xs, ys, s in expl_buf if s >= t - self.W]
                V = self.lam * np.eye(r)
                b = np.zeros(r)
                for xs, ys in win:
                    zs = U_hat.T @ xs
                    V += np.outer(zs, zs)
                    b += zs * ys
                a_hat = np.linalg.solve(V, b)
                bt = self._beta(len(win))
                gt = self._gamma(m_probe_seg, G_norms)

                Z = action_set @ U_hat
                ViZ = np.linalg.solve(V, Z.T).T
                el = np.sqrt(np.einsum('ij,ij->i', Z, ViZ))
                xn = np.linalg.norm(action_set, axis=1)
                ucb = Z @ a_hat + bt * el + gt * xn

                x_dep = action_set[int(np.argmax(ucb))]

                # Exploitation also gets cross-correlated noise
                eps_base = self.rng.normal(0.0, self.sigma_eps)
                eps_base = np.clip(eps_base, -env.L_eps, env.L_eps)
                cross_term = self.eps_cross * float(x_dep @ env.theta[t])
                y_t = float(x_dep @ env.theta[t]) + eps_base + cross_term

                expl_buf.append((x_dep, y_t, t))
                if len(expl_buf) > self.W + 10:
                    expl_buf = [(xs, ys, s) for xs, ys, s in expl_buf
                                if s >= t - self.W]

                r_t = float(x_dep @ env.theta[t])
                metrics.control_regret[t] = r_opt - r_t
                metrics.costed_regret[t] = r_opt - r_t

        return metrics


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
