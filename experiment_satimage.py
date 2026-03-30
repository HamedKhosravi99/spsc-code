"""
Phase Diagram on Satimage (Landsat Satellite) with comprehensive baselines.

Dataset: UCI Satimage — 6,430 samples, 36 multispectral features
(4 spectral bands × 3×3 pixel neighborhood), 6 land-cover classes.

Baselines (7 methods total):
  1. SPSC Algorithm 1       — ours (probe + r-dim UCB)
  2. LinUCB                 — stationary ridge UCB, full d  (Abbasi-Yadkori+ 2011)
  3. D-LinUCB               — discounted ridge UCB          (Russac+ NeurIPS 2019)
  4. SW-LinUCB              — sliding-window ridge UCB      (Cheung+ NeurIPS 2019)
  5. Restart-LinUCB         — periodic restart, NO oracle   (Auer+ 2019 spirit)
  6. LowRank-Reward-UCB     — subspace from rewards, r-dim  (LowESTR/VOFUL spirit)
  7. Oracle-LinUCB          — known subspace, r-dim UCB     (≈ LowOFUL, Jun+ 2019)

Outputs: concentric ring + bubble chart figures.
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

sys.path.insert(0, os.path.dirname(__file__))
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB, RunMetrics

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# =====================================================================
# Additional baselines
# =====================================================================

class SWLinUCB:
    """Sliding-window LinUCB (Cheung+ NeurIPS 2019). Resets at oracle CPs."""
    def __init__(self, env, window=200, lam=1.0, delta=0.05, seed=1):
        self.env = env
        self.W = window
        self.lam = lam
        self.delta = delta
        self.rng = np.random.default_rng(seed)
        self.S = env.S
        self.sigma_eps = env.sigma_eps
        self.L_x = env.L_x

    def _beta(self, n):
        d = self.env.d
        arg = max(1.0 + n * self.L_x**2 / self.lam, 1.0 + 1e-12)
        return self.sigma_eps * np.sqrt(d * np.log(arg / self.delta)) + np.sqrt(self.lam) * self.S

    def run(self):
        env = self.env
        d, T = env.d, env.T
        metrics = RunMetrics(name="SW-LinUCB", T=T)
        buf = []
        current_k = -1
        for t in range(T):
            k = env.seg_of[t]
            if k != current_k:
                buf = []
                current_k = k
            action_set = env.get_action_set(t, rng=self.rng)
            r_opt = env.optimal_reward(action_set, t)
            win = [(xs, ys) for xs, ys, s in buf if s >= t - self.W]
            V = self.lam * np.eye(d)
            b = np.zeros(d)
            for xs, ys in win:
                V += np.outer(xs, xs)
                b += xs * ys
            theta_hat = np.linalg.solve(V, b)
            beta_t = self._beta(len(win))
            V_inv_A = np.linalg.solve(V, action_set.T).T
            ucb = action_set @ theta_hat + beta_t * np.sqrt(
                np.einsum('ij,ij->i', action_set, V_inv_A))
            x_dep = action_set[int(np.argmax(ucb))]
            y = env.step(x_dep, t)
            buf.append((x_dep, y, t))
            if len(buf) > self.W + 10:
                buf = [(xs, ys, s) for xs, ys, s in buf if s >= t - self.W]
            r_t = float(x_dep @ env.theta[t])
            metrics.control_regret[t] = r_opt - r_t
            metrics.costed_regret[t] = r_opt - r_t
        return metrics


class RestartLinUCB:
    """
    Periodic-restart LinUCB — NO oracle change-point knowledge.
    Restarts every `restart_period` rounds. (Auer+ 2019 spirit.)
    """
    def __init__(self, env, restart_period=500, lam=1.0, delta=0.05, seed=1):
        self.env = env
        self.restart_period = restart_period
        self.lam = lam
        self.delta = delta
        self.rng = np.random.default_rng(seed)
        self.S = env.S
        self.sigma_eps = env.sigma_eps
        self.L_x = env.L_x

    def _beta(self, n):
        d = self.env.d
        arg = max(1.0 + n * self.L_x**2 / self.lam, 1.0 + 1e-12)
        return self.sigma_eps * np.sqrt(d * np.log(arg / self.delta)) + np.sqrt(self.lam) * self.S

    def run(self):
        env = self.env
        d, T = env.d, env.T
        metrics = RunMetrics(name="Restart-LinUCB", T=T)
        V = self.lam * np.eye(d)
        b = np.zeros(d)
        n_since = 0
        for t in range(T):
            if n_since >= self.restart_period:
                V = self.lam * np.eye(d)
                b = np.zeros(d)
                n_since = 0
            action_set = env.get_action_set(t, rng=self.rng)
            r_opt = env.optimal_reward(action_set, t)
            theta_hat = np.linalg.solve(V, b)
            beta_t = self._beta(n_since)
            V_inv_A = np.linalg.solve(V, action_set.T).T
            ucb = action_set @ theta_hat + beta_t * np.sqrt(
                np.einsum('ij,ij->i', action_set, V_inv_A))
            x_dep = action_set[int(np.argmax(ucb))]
            y = env.step(x_dep, t)
            V += np.outer(x_dep, x_dep)
            b += x_dep * y
            n_since += 1
            r_t = float(x_dep @ env.theta[t])
            metrics.control_regret[t] = r_opt - r_t
            metrics.costed_regret[t] = r_opt - r_t
        return metrics


class LowRankRewardUCB:
    """
    Learn subspace from reward data (LowESTR/VOFUL spirit).
    Periodically re-estimates subspace via PCA on (x_t * y_t) outer products,
    then runs r-dim UCB in the estimated subspace.
    Has oracle segment boundaries (same as other methods).
    """
    def __init__(self, env, window=200, pca_warmup=50, lam=1.0, delta=0.05, seed=1):
        self.env = env
        self.W = window
        self.pca_warmup = pca_warmup
        self.lam = lam
        self.delta = delta
        self.rng = np.random.default_rng(seed)
        self.S = env.S
        self.sigma_eps = env.sigma_eps
        self.L_x = env.L_x

    def _beta_r(self, n, gamma=0.0):
        r = self.env.r
        arg = max(1.0 + n * self.L_x**2 / self.lam, 1.0 + 1e-12)
        return (self.sigma_eps * np.sqrt(r * np.log(arg / self.delta))
                + np.sqrt(self.lam) * self.S
                + gamma * self.S * self.L_x)

    def run(self):
        env = self.env
        d, r, T = env.d, env.r, env.T
        metrics = RunMetrics(name="LowRank-Reward-UCB", T=T)

        xy_buf = []  # (x, y, t) for subspace estimation
        expl_buf = []  # (z, y, t) for r-dim regression
        P_hat = np.eye(d)[:, :r]  # initial random subspace
        current_k = -1

        for t in range(T):
            k = env.seg_of[t]
            if k != current_k:
                xy_buf = []
                expl_buf = []
                P_hat = np.eye(d)[:, :r]
                current_k = k

            action_set = env.get_action_set(t, rng=self.rng)
            r_opt = env.optimal_reward(action_set, t)

            # Update subspace estimate from reward data
            if len(xy_buf) >= self.pca_warmup:
                # Build empirical covariance of x*y (gradient-like)
                M = np.zeros((d, d))
                for x_s, y_s, s in xy_buf[-(self.W):]:
                    M += np.outer(x_s * y_s, x_s * y_s)
                M /= len(xy_buf[-(self.W):])
                try:
                    eigvals, eigvecs = np.linalg.eigh(M)
                    P_hat = eigvecs[:, -r:]  # top-r eigenvectors
                except:
                    pass

            # Project actions into estimated subspace
            Z = action_set @ P_hat  # (n_actions, r)

            # Windowed r-dim regression
            win = [(zs, ys) for zs, ys, s in expl_buf if s >= t - self.W]
            V_r = self.lam * np.eye(r)
            b_r = np.zeros(r)
            for zs, ys in win:
                V_r += np.outer(zs, zs)
                b_r += zs * ys
            a_hat = np.linalg.solve(V_r, b_r)
            beta_t = self._beta_r(len(win), gamma=0.3)

            V_inv_Z = np.linalg.solve(V_r, Z.T).T
            ucb = Z @ a_hat + beta_t * np.sqrt(
                np.einsum('ij,ij->i', Z, V_inv_Z))
            idx = int(np.argmax(ucb))
            x_dep = action_set[idx]
            z_dep = Z[idx]
            y = env.step(x_dep, t)

            xy_buf.append((x_dep, y, t))
            expl_buf.append((z_dep, y, t))

            r_t = float(x_dep @ env.theta[t])
            metrics.control_regret[t] = r_opt - r_t
            metrics.costed_regret[t] = r_opt - r_t
        return metrics


# =====================================================================
# Satimage Environment
# =====================================================================

class SatimageEnvironment:
    """
    Semi-synthetic environment using Landsat Satellite (Satimage) features.
    36 multispectral features (4 bands × 3×3 neighborhood), 6 land-cover classes.
    """
    def __init__(self, d=12, r=2, K=4, T=5000, sigma_eps=0.3,
                 spectral_radius=0.99, n_actions=80, seed=42, sigma_eta=0.04):
        self.d = d
        self.r = r
        self.K = K
        self.T = T
        self.sigma_eps = sigma_eps
        self.spectral_radius = spectral_radius
        self.n_actions = n_actions
        self.rng = np.random.default_rng(seed)
        self.sigma_eta = sigma_eta
        self.L_x = 1.0
        self.L = 1.0
        self.L_eps = 1.0
        self.S = None
        self._load_data()
        self._build_segments()
        self._build_subspaces()
        self._generate_trajectory()

    def _load_data(self):
        from sklearn.datasets import fetch_openml
        from sklearn.preprocessing import StandardScaler
        data = fetch_openml('satimage', version=1, as_frame=False, parser='auto')
        X_raw = data.data.astype(float)
        y_raw = data.target
        # Convert string labels to int
        if y_raw.dtype.kind in ('U', 'S', 'O'):
            y_raw = np.array([int(float(y)) for y in y_raw])
        d_raw = X_raw.shape[1]  # 36

        scaler = StandardScaler()
        X_std = scaler.fit_transform(X_raw)

        # Add pairwise interactions if d > d_raw
        if self.d > d_raw:
            interactions = []
            for i in range(d_raw):
                for j in range(i + 1, d_raw):
                    interactions.append(X_std[:, i] * X_std[:, j])
            X_inter = np.column_stack(interactions)
            X = np.hstack([X_std, X_inter])
            X = X[:, :self.d]
        else:
            X = X_std[:, :self.d]

        norms = np.linalg.norm(X, axis=1, keepdims=True)
        X = X / np.maximum(norms, 1e-8)

        idx = self.rng.permutation(len(X))
        self._action_pool = X[idx]
        self._labels = y_raw[idx]
        self._centroids = {}
        for c in np.unique(y_raw):
            mask = self._labels == c
            if mask.sum() > 0:
                self._centroids[c] = self._action_pool[mask].mean(axis=0)

    def _build_segments(self):
        base = self.T // self.K
        lengths = [base] * self.K
        lengths[-1] += self.T - sum(lengths)
        self.segment_lengths = lengths
        self.tau = [0]
        for l in lengths[:-1]:
            self.tau.append(self.tau[-1] + l)
        self.seg_of = np.zeros(self.T, dtype=int)
        for k, start in enumerate(self.tau):
            end = start + self.segment_lengths[k]
            self.seg_of[start:end] = k

    def _build_subspaces(self):
        self.B_list = []
        centroid_mat = np.array(list(self._centroids.values()))
        n_c = len(self._centroids)
        for k in range(self.K):
            combo = np.zeros((self.r, self.d))
            for j in range(self.r):
                w = self.rng.dirichlet(np.ones(n_c) * 0.5)
                w = np.roll(w, (k * n_c // self.K + j) % n_c)
                combo[j] = w @ centroid_mat + 0.1 * self.rng.standard_normal(self.d)
            Q, _ = np.linalg.qr(combo.T)
            B_k = Q[:, :self.r]
            if k > 0:
                P_prev = self.B_list[-1] @ self.B_list[-1].T
                P_new = B_k @ B_k.T
                att = 0
                while np.linalg.norm(P_new - P_prev, 2) < 0.5 and att < 10:
                    combo += 0.3 * self.rng.standard_normal(combo.shape)
                    Q, _ = np.linalg.qr(combo.T)
                    B_k = Q[:, :self.r]
                    P_new = B_k @ B_k.T
                    att += 1
            self.B_list.append(B_k)

    def _generate_trajectory(self):
        self.theta = np.zeros((self.T, self.d))
        self.w = np.zeros((self.T, self.r))
        t = 0
        for k in range(self.K):
            Bk = self.B_list[k]
            Ak = self.spectral_radius * np.eye(self.r)
            Sigma = self.sigma_eta * np.eye(self.r)
            n_k = self.segment_lengths[k]
            wt = self.rng.multivariate_normal(np.zeros(self.r), Sigma)
            for step in range(n_k):
                self.w[t] = wt
                self.theta[t] = Bk @ wt
                t += 1
                if step < n_k - 1:
                    wt = Ak @ wt + self.rng.multivariate_normal(np.zeros(self.r), Sigma)
        self.S = float(np.max(np.linalg.norm(self.theta, axis=1)))

    def get_action_set(self, t, rng=None):
        _rng = rng if rng is not None else self.rng
        idx = _rng.choice(len(self._action_pool), size=self.n_actions, replace=False)
        return self._action_pool[idx].copy()

    def step(self, action, t):
        eps = self.rng.normal(0.0, self.sigma_eps)
        eps = np.clip(eps, -self.L_eps, self.L_eps)
        return float(action @ self.theta[t]) + eps

    def optimal_reward(self, action_set, t):
        return float(np.max(action_set @ self.theta[t]))

    def segment_projector(self, k):
        B = self.B_list[k]
        return B @ B.T


# =====================================================================
# Sweep parameters
# =====================================================================

D_GRID = [18, 24, 30, 36]
R_GRID = [1, 2, 3, 5]
T_SWEEP = 5000
K = 4
N_SEEDS = 5
PROBE_EVERY = 40
PROBE_COST = 0.1
WINDOW = 100

# Method names — order matters for display
METHOD_NAMES = [
    "Oracle-LinUCB",
    "SPSC-Alg1",
    "LowRank-Reward",
    "SW-LinUCB",
    "D-LinUCB",
    "Restart-LinUCB",
    "LinUCB",
]

METHOD_LABELS = {
    "Oracle-LinUCB":    "Oracle (Jun+ '19)",
    "SPSC-Alg1":        "SPSC (ours)",
    "LowRank-Reward":   "LowRank-Reward",
    "SW-LinUCB":        "SW-LinUCB (Cheung+ '19)",
    "D-LinUCB":         "D-LinUCB (Russac+ '19)",
    "Restart-LinUCB":   "Restart-LinUCB (Auer+ '19)",
    "LinUCB":           "LinUCB (Abbasi+ '11)",
}


def run_single(d, r, seed):
    """Run all 7 methods on a single (d, r, seed) config."""
    results = {}

    def make():
        return SatimageEnvironment(d=d, r=r, K=K, T=T_SWEEP, sigma_eps=0.3,
                                    spectral_radius=0.99, n_actions=80,
                                    seed=seed * 100, sigma_eta=0.04)

    # SPSC
    env = make()
    results["SPSC-Alg1"] = SPSC_Algorithm1(
        env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
        window=WINDOW, lam=1.0, delta=0.05, seed=seed,
        normalize_gamma_by_d=True
    ).run().cumulative_costed_regret[-1]

    # LinUCB
    env = make()
    results["LinUCB"] = LinUCB(env, lam=1.0, delta=0.05,
                                seed=seed + 1000).run().cumulative_costed_regret[-1]

    # D-LinUCB
    env = make()
    results["D-LinUCB"] = LinUCB(env, lam=1.0, delta=0.05, seed=seed + 2000,
                                  forgetting_factor=0.998).run().cumulative_costed_regret[-1]

    # SW-LinUCB
    env = make()
    results["SW-LinUCB"] = SWLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                                     seed=seed + 3000).run().cumulative_costed_regret[-1]

    # Oracle-LinUCB
    env = make()
    results["Oracle-LinUCB"] = OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                                             seed=seed + 4000).run().cumulative_costed_regret[-1]

    # Restart-LinUCB (no oracle CPs, restart every T/K)
    env = make()
    results["Restart-LinUCB"] = RestartLinUCB(
        env, restart_period=T_SWEEP // K, lam=1.0, delta=0.05,
        seed=seed + 5000).run().cumulative_costed_regret[-1]

    # LowRank-Reward-UCB
    env = make()
    results["LowRank-Reward"] = LowRankRewardUCB(
        env, window=WINDOW, pca_warmup=50, lam=1.0, delta=0.05,
        seed=seed + 6000).run().cumulative_costed_regret[-1]

    return results


def run_sweep():
    n_d, n_r = len(D_GRID), len(R_GRID)
    # Store per-method regret grids
    regret_grids = {m: np.zeros((n_r, n_d)) for m in METHOD_NAMES}
    ratio_grids = {m: np.ones((n_r, n_d)) for m in METHOD_NAMES}

    total = n_d * n_r
    done = 0
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r >= d:
                done += 1
                continue

            print(f"  [{done+1}/{total}] d={d}, r={r} ({N_SEEDS} seeds) ...",
                  end="", flush=True)

            accum = {m: [] for m in METHOD_NAMES}
            for seed in range(N_SEEDS):
                res = run_single(d, r, seed)
                for m in METHOD_NAMES:
                    accum[m].append(res[m])

            for m in METHOD_NAMES:
                regret_grids[m][i, j] = np.mean(accum[m])

            # Compute ratios vs SPSC
            spsc_mean = regret_grids["SPSC-Alg1"][i, j]
            lin_mean = regret_grids["LinUCB"][i, j]
            ratio = spsc_mean / max(lin_mean, 1e-8)
            ratio_grids["SPSC-Alg1"][i, j] = ratio

            pct = (1 - ratio) * 100
            tag = "SPSC wins" if pct > 0 else "LinUCB wins"
            print(f"  SPSC/Lin={ratio:.3f} ({tag}, {abs(pct):.0f}%)")
            done += 1

    return regret_grids, ratio_grids


# =====================================================================
# Concentric Ring Chart
# =====================================================================

def fig_concentric_rings(regret_grids):
    """Rings = rank r, sectors = dimension d, color = SPSC/LinUCB ratio."""
    plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

    n_d = len(D_GRID)
    n_r = len(R_GRID)

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    sector_width = 2 * np.pi / n_d
    angles = np.linspace(0, 2 * np.pi, n_d, endpoint=False)

    # Compute ratio grid
    ratio = np.ones((n_r, n_d))
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r < d:
                ratio[i, j] = regret_grids["SPSC-Alg1"][i, j] / max(
                    regret_grids["LinUCB"][i, j], 1e-8)

    vmin = min(0.55, ratio.min() - 0.02)
    vmax = max(1.15, ratio.max() + 0.02)
    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)
    cmap = plt.cm.RdBu_r

    ring_inner = 0.3
    ring_width = 0.18

    for i, r in enumerate(R_GRID):
        r_bottom = ring_inner + i * ring_width
        r_height = ring_width * 0.92

        for j, d in enumerate(D_GRID):
            angle = angles[j]
            val = ratio[i, j]

            if r >= d:
                color = "#e0e0e0"
                val_text = "n/a"
            else:
                color = cmap(norm(val))
                val_text = f"{val:.2f}"

            ax.bar(angle, r_height, width=sector_width * 0.92,
                   bottom=r_bottom, color=color,
                   edgecolor="white", linewidth=1.8)

            text_r = r_bottom + r_height / 2
            txt_color = "white" if r < d and abs(val - 1.0) > 0.18 else "#333333"
            rot = np.degrees(angle) - 90 if angle < np.pi else np.degrees(angle) + 90
            ax.text(angle, text_r, val_text,
                    ha="center", va="center", fontsize=8,
                    fontweight="bold", color=txt_color, rotation=rot)

    # Ring labels
    for i, r in enumerate(R_GRID):
        r_center = ring_inner + i * ring_width + ring_width * 0.46
        ax.text(np.pi * 1.08, r_center, f"$r={r}$",
                ha="center", va="center", fontsize=11, fontweight="bold",
                color="#333333",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="gray",
                          alpha=0.9, lw=0.8))

    # Sector labels
    outer_r = ring_inner + n_r * ring_width + 0.06
    for j, d in enumerate(D_GRID):
        ax.text(angles[j], outer_r, f"$d={d}$",
                ha="center", va="center", fontsize=11, fontweight="bold")

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(0, ring_inner + n_r * ring_width + 0.15)
    ax.grid(False)
    ax.spines['polar'].set_visible(False)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.45, pad=0.08, aspect=20)
    cbar.set_label("SPSC / LinUCB ratio", fontsize=11, labelpad=8)
    cbar.ax.axhline(1.0, color="black", lw=2)

    ax.set_title("Satimage Operating Regime\n"
                 "Rings = rank $r$ · Sectors = dimension $d$",
                 fontsize=14, fontweight="bold", pad=30, y=1.05)

    ax.text(0, 0.12, "SPSC\nAdvantage\nRegime",
            ha="center", va="center", fontsize=9, fontweight="bold",
            color="#1a3a6b", transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.4", fc="#dbe9f6", ec="#3b7dd8",
                      alpha=0.9, lw=1.5))

    out = os.path.join(OUT_DIR, "satimage_rings.png")
    plt.savefig(out, bbox_inches="tight", dpi=200)
    print(f"Saved: {out}")


# =====================================================================
# Bubble Chart — 7 methods at a fixed (d, r)
# =====================================================================

def fig_bubble_multi_method(regret_grids):
    """
    Bubble chart across (d, r) grid.
    For each cell: bubbles for all 7 methods, sized by regret, colored by method.
    """
    plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

    METHOD_COLORS = {
        "Oracle-LinUCB":    "#2ca02c",
        "SPSC-Alg1":        "#1f77b4",
        "LowRank-Reward":   "#17becf",
        "SW-LinUCB":        "#9467bd",
        "D-LinUCB":         "#ff7f0e",
        "Restart-LinUCB":   "#8c564b",
        "LinUCB":           "#d62728",
    }

    n_d, n_r = len(D_GRID), len(R_GRID)
    fig, ax = plt.subplots(figsize=(16, 8))

    # x-axis: (d, r) configs as categorical
    configs = []
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r < d:
                configs.append((i, j, r, d))

    n_configs = len(configs)
    x_positions = np.arange(n_configs)

    # Scale bubble sizes
    all_regrets = []
    for m in METHOD_NAMES:
        for i, j, r, d in configs:
            all_regrets.append(regret_grids[m][i, j])
    max_regret = max(all_regrets) if all_regrets else 1

    method_offsets = np.linspace(-0.35, 0.35, len(METHOD_NAMES))

    for m_idx, method in enumerate(METHOD_NAMES):
        xs, ys, sizes = [], [], []
        for c_idx, (i, j, r, d) in enumerate(configs):
            reg = regret_grids[method][i, j]
            xs.append(x_positions[c_idx] + method_offsets[m_idx])
            ys.append(reg)
            sizes.append(max(30, 400 * reg / max_regret))

        ax.scatter(xs, ys, s=sizes, c=METHOD_COLORS[method],
                   alpha=0.7, edgecolors="white", linewidths=0.8,
                   zorder=3, label=METHOD_LABELS[method])

    # Connect SPSC dots with a line for readability
    spsc_ys = [regret_grids["SPSC-Alg1"][i, j] for i, j, r, d in configs]
    spsc_xs = x_positions + method_offsets[1]
    ax.plot(spsc_xs, spsc_ys, color="#1f77b4", lw=1.5, ls="--", alpha=0.5, zorder=2)

    ax.set_xticks(x_positions)
    ax.set_xticklabels([f"$d$={d}\n$r$={r}" for _, _, r, d in configs],
                        fontsize=8.5, rotation=0)
    ax.set_ylabel("Cumulative Costed Regret", fontsize=12)
    ax.set_xlabel("Configuration $(d, r)$", fontsize=12)
    ax.set_title("Satimage Benchmark: 7-Method Comparison\n"
                 "Bubble size $\\propto$ regret · "
                 f"$K={K}$, $T={T_SWEEP:,}$, {N_SEEDS} seeds",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=9, loc="upper left", ncol=2, framealpha=0.9,
              edgecolor="#cccccc")
    ax.grid(True, alpha=0.2, ls="--")
    ax.set_facecolor("#fafafa")
    ax.tick_params(labelsize=10)

    out = os.path.join(OUT_DIR, "satimage_bubble_7methods.png")
    plt.savefig(out, bbox_inches="tight", dpi=200)
    print(f"Saved: {out}")


# =====================================================================
# Summary table
# =====================================================================

def print_summary(regret_grids):
    print("\n" + "=" * 90)
    print("Satimage Benchmark — SPSC / Baseline Regret Ratios (< 1 = SPSC wins)")
    print("=" * 90)

    for method in METHOD_NAMES:
        if method == "SPSC-Alg1":
            continue
        print(f"\n  vs {METHOD_LABELS[method]}:")
        header = f"  {'r \\\\ d':>6}" + "".join(f"{d:>8}" for d in D_GRID)
        print(header)
        print("  " + "-" * (6 + 8 * len(D_GRID)))
        for i, r in enumerate(R_GRID):
            row = f"  {r:>6}"
            for j, d in enumerate(D_GRID):
                if r >= d:
                    row += f"{'---':>8}"
                else:
                    ratio = regret_grids["SPSC-Alg1"][i, j] / max(
                        regret_grids[method][i, j], 1e-8)
                    row += f"{ratio:>8.3f}"
            print(row)

    # Count wins
    print("\n" + "=" * 90)
    print("Win counts (SPSC regret < baseline regret):")
    total_valid = sum(1 for i, r in enumerate(R_GRID)
                      for j, d in enumerate(D_GRID) if r < d)
    for method in METHOD_NAMES:
        if method in ("SPSC-Alg1", "Oracle-LinUCB"):
            continue
        wins = 0
        for i, r in enumerate(R_GRID):
            for j, d in enumerate(D_GRID):
                if r < d and regret_grids["SPSC-Alg1"][i, j] < regret_grids[method][i, j]:
                    wins += 1
        print(f"  SPSC beats {METHOD_LABELS[method]:<30}: {wins}/{total_valid}")
    print("=" * 90)


# =====================================================================
# Entry point
# =====================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("Satimage Phase Diagram Sweep")
    print(f"  d in {D_GRID}")
    print(f"  r in {R_GRID}")
    print(f"  Methods: {len(METHOD_NAMES)}")
    print(f"  T={T_SWEEP}, K={K}, seeds={N_SEEDS}")
    print("=" * 65)

    regret_grids, ratio_grids = run_sweep()

    print_summary(regret_grids)

    fig_concentric_rings(regret_grids)
    fig_bubble_multi_method(regret_grids)

    # Save data
    save_dict = {f"{m}_regret": regret_grids[m] for m in METHOD_NAMES}
    save_dict["d_grid"] = np.array(D_GRID)
    save_dict["r_grid"] = np.array(R_GRID)
    np.savez_compressed(os.path.join(OUT_DIR, "satimage_phase_data.npz"), **save_dict)
    print("Saved: satimage_phase_data.npz")
    print("\nDone.")
