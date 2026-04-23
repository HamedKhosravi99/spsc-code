"""
"LowOFUL/VOFUL + SPSC-subspace" ablation (revision W6 side table).

The main-body experiments run LowOFUL and VOFUL with their own online-PCA
subspace estimators (action-reward outer products with change-triggered
buffer reset). This script additionally runs two variants in which those
baselines are fed the probe-based subspace estimate used by SPSC itself:

    U_hat_t = TopEig_r( (1/m) sum_{probe s <= t} K^{-1}(s_s u_s u_s^T) )

keeping everything else (ridge-UCB head, betaradius, buffer reset rule)
identical to the vanilla LowOFUL/VOFUL. If the results are close to the
vanilla baselines, SPSC's empirical win is driven mostly by its drift-aware
windowed ridge head; if they are close to SPSC, the probe-based subspace
is the main source of gain.

This is a "favorable adaptation" of the baselines (in the sense of the paper
revision): representation quality is equalized, so any remaining gap is
attributable to how the representation is exploited.

Output: exps/results/experiment_baseline_shared_subspace.json

Runtime: ~30-45 min (3x3 grid x 10 seeds x 4 methods).
"""

import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from environments import LowRankLDSEnvironment
from algorithm import (
    SPSC_Algorithm1, LowOFUL, VOFUL, K_inverse, RunMetrics,
)
from results_io import save_results

# --- config matches main synthetic setup ----------------------------------
N_SEEDS = 10
T, K = 5000, 10
SIGMA_EPS, SPEC_RAD, SIGMA_ETA = 0.3, 0.99, 0.04
N_ACTIONS = 40
PROBE_EVERY, PROBE_COST = 50, 0.1
WINDOW, LAM, DELTA = 400, 0.01, 0.05
FEATURE_DECAY = 1.5

CELLS = [(55, 5), (55, 10), (105, 5), (105, 10), (105, 20),
         (200, 5), (200, 10), (200, 20)]


# ---- shared-subspace algorithms ------------------------------------------

class _LowOFULSharedSubspace:
    """LowOFUL variant that uses SPSC's probe-based subspace estimator.

    Differences vs vanilla LowOFUL:
      - probe rounds (every PROBE_EVERY steps) are used to accumulate the
        lifted sample G_t = K^{-1}(s_t u_t u_t^T) and refresh U_hat;
      - non-probe rounds run exactly as in LowOFUL (projected ridge-UCB);
      - the subspace buffer resets on the same change-triggered rule as
        vanilla LowOFUL (Frobenius projector-change > 0.3).
    """
    def __init__(self, env, probe_every=50, lam=1.0, delta=0.05, seed=0):
        self.env = env; self.probe_every = probe_every
        self.lam = lam; self.delta = delta
        self.rng = np.random.default_rng(seed)
        self.d = env.d; self.r = env.r
        self.sigma_eps = env.sigma_eps; self.S = env.S; self.L_x = env.L_x

    def _beta(self, n):
        arg = max(1.0 + n * self.L_x**2 / self.lam, 1.0 + 1e-12)
        return (self.sigma_eps * np.sqrt(self.r * np.log(arg / self.delta))
                + np.sqrt(self.lam) * self.S)

    def run(self):
        env = self.env; d, r, T = self.d, self.r, env.T
        metrics = RunMetrics(name="LowOFUL-shared", T=T)
        M_sum = np.zeros((d, d)); n_probes = 0
        U_hat = np.eye(d, r)
        V_r = self.lam * np.eye(r); b_r = np.zeros(r); n_exp = 0

        for t in range(T):
            action_set = env.get_action_set(t, rng=self.rng)
            r_opt = env.optimal_reward(action_set, t)
            if (t % self.probe_every) == 0:
                # probe round
                z = self.rng.standard_normal(d)
                u_t = np.sqrt(d) * z / (np.linalg.norm(z) + 1e-12)
                y_t = env.step(u_t, t)
                s_t = y_t**2 - self.sigma_eps**2
                G_t = K_inverse(s_t * np.outer(u_t, u_t), d)
                M_sum += G_t; n_probes += 1
                if n_probes >= 3:
                    _, eig_vecs = np.linalg.eigh(M_sum / n_probes)
                    U_new = eig_vecs[:, -r:]
                    if np.linalg.norm(U_new @ U_new.T - U_hat @ U_hat.T, 'fro') > 0.3:
                        V_r = self.lam * np.eye(r); b_r = np.zeros(r); n_exp = 0
                    U_hat = U_new
                r_t = float(u_t @ env.theta[t])
                metrics.control_regret[t] = r_opt - r_t
                metrics.costed_regret[t] = r_opt - r_t + PROBE_COST
            else:
                Z = action_set @ U_hat
                a_hat = np.linalg.solve(V_r, b_r)
                beta = self._beta(n_exp)
                V_inv_Z = np.linalg.solve(V_r, Z.T).T
                ellip = np.sqrt(np.einsum('ij,ij->i', Z, V_inv_Z))
                ucb = Z @ a_hat + beta * ellip
                x = action_set[int(np.argmax(ucb))]
                y_t = env.step(x, t)
                z_dep = U_hat.T @ x
                V_r += np.outer(z_dep, z_dep); b_r += z_dep * y_t; n_exp += 1
                r_t = float(x @ env.theta[t])
                metrics.control_regret[t] = r_opt - r_t
                metrics.costed_regret[t] = r_opt - r_t
        return metrics


class _VOFULSharedSubspace(_LowOFULSharedSubspace):
    """VOFUL with shared subspace: same as _LowOFULSharedSubspace but with
    variance-weighted ridge updates on exploitation rounds."""
    def run(self):
        env = self.env; d, r, T = self.d, self.r, env.T
        metrics = RunMetrics(name="VOFUL-shared", T=T)
        M_sum = np.zeros((d, d)); n_probes = 0
        U_hat = np.eye(d, r)
        V_r = self.lam * np.eye(r); b_r = np.zeros(r); n_exp = 0
        for t in range(T):
            action_set = env.get_action_set(t, rng=self.rng)
            r_opt = env.optimal_reward(action_set, t)
            if (t % self.probe_every) == 0:
                z = self.rng.standard_normal(d)
                u_t = np.sqrt(d) * z / (np.linalg.norm(z) + 1e-12)
                y_t = env.step(u_t, t)
                s_t = y_t**2 - self.sigma_eps**2
                G_t = K_inverse(s_t * np.outer(u_t, u_t), d)
                M_sum += G_t; n_probes += 1
                if n_probes >= 3:
                    _, eig_vecs = np.linalg.eigh(M_sum / n_probes)
                    U_new = eig_vecs[:, -r:]
                    if np.linalg.norm(U_new @ U_new.T - U_hat @ U_hat.T, 'fro') > 0.3:
                        V_r = self.lam * np.eye(r); b_r = np.zeros(r); n_exp = 0
                    U_hat = U_new
                r_t = float(u_t @ env.theta[t])
                metrics.control_regret[t] = r_opt - r_t
                metrics.costed_regret[t] = r_opt - r_t + PROBE_COST
            else:
                Z = action_set @ U_hat
                a_hat = np.linalg.solve(V_r, b_r)
                beta = self._beta(n_exp)
                V_inv_Z = np.linalg.solve(V_r, Z.T).T
                ellip = np.sqrt(np.einsum('ij,ij->i', Z, V_inv_Z))
                ucb = Z @ a_hat + beta * ellip
                x = action_set[int(np.argmax(ucb))]
                y_t = env.step(x, t)
                # Variance-weighted ridge (VOFUL style)
                x_norm_sq = float(np.dot(x, x))
                w_t = 1.0 / (x_norm_sq + self.sigma_eps**2)
                z_dep = U_hat.T @ x
                V_r += w_t * np.outer(z_dep, z_dep); b_r += w_t * z_dep * y_t
                n_exp += 1
                r_t = float(x @ env.theta[t])
                metrics.control_regret[t] = r_opt - r_t
                metrics.costed_regret[t] = r_opt - r_t
        return metrics


METHODS = ["LowOFUL", "LowOFUL-shared", "VOFUL", "VOFUL-shared"]


def make_env(seed, d, r):
    return LowRankLDSEnvironment(
        d=d, r=r, K=K, T=T, sigma_eps=SIGMA_EPS, spectral_radius=SPEC_RAD,
        n_actions=N_ACTIONS, sigma_eta=SIGMA_ETA, seed=seed * 100,
        piecewise_constant=True, feature_decay=FEATURE_DECAY,
    )


def run_method(name, env, seed):
    if name == "LowOFUL":
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 5000).run()
        return float(m.cumulative_control_regret[-1])
    if name == "LowOFUL-shared":
        m = _LowOFULSharedSubspace(env, probe_every=PROBE_EVERY, lam=LAM,
                                    delta=DELTA, seed=seed + 5500).run()
        return float(m.cumulative_costed_regret[-1])
    if name == "VOFUL":
        m = VOFUL(env, lam=LAM, delta=DELTA, seed=seed + 6000).run()
        return float(m.cumulative_control_regret[-1])
    if name == "VOFUL-shared":
        m = _VOFULSharedSubspace(env, probe_every=PROBE_EVERY, lam=LAM,
                                 delta=DELTA, seed=seed + 6500).run()
        return float(m.cumulative_costed_regret[-1])
    raise ValueError(name)


def run_cell(d, r):
    print(f"\n[d={d}, r={r}]")
    t0 = time.time()
    res = {m: [] for m in METHODS}
    for s in range(N_SEEDS):
        for m in METHODS:
            env = make_env(s, d, r)
            res[m].append(run_method(m, env, s))
    for m in METHODS:
        arr = np.array(res[m])
        print(f"  {m:<16} {arr.mean():>7.0f} +/- {arr.std()/np.sqrt(N_SEEDS):>5.0f}")
    print(f"  [{time.time()-t0:.1f}s]")
    return {m: np.array(v) for m, v in res.items()}


if __name__ == "__main__":
    print("=" * 80)
    print(f"Baseline shared-subspace ablation  T={T}, K={K}, seeds={N_SEEDS}")
    print("=" * 80)
    all_results = {}
    overall_t0 = time.time()
    for (d, r) in CELLS:
        all_results[(d, r)] = run_cell(d, r)
    print(f"\nTotal: {(time.time()-overall_t0)/60:.1f} min")
    save_results(
        __file__,
        config={"N_SEEDS": N_SEEDS, "T": T, "K": K, "CELLS": CELLS,
                "SIGMA_EPS": SIGMA_EPS, "SPEC_RAD": SPEC_RAD, "SIGMA_ETA": SIGMA_ETA,
                "N_ACTIONS": N_ACTIONS, "PROBE_EVERY": PROBE_EVERY,
                "PROBE_COST": PROBE_COST, "WINDOW": WINDOW,
                "LAM": LAM, "DELTA": DELTA, "FEATURE_DECAY": FEATURE_DECAY,
                "METHODS": METHODS},
        results=all_results)
    print("Done.")
