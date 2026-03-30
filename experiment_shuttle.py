"""
Experiment: Shuttle Real-Data Benchmark — Comprehensive Comparison.

Uses the Statlog Shuttle dataset (58K samples, 9 features, 7 classes)
from UCI via sklearn/OpenML.  This sensor dataset has natural low-rank
structure (few latent modes) and d=9 is in SPSC's practical sweet spot.

Compares SPSC against 4 baselines covering stationary, non-stationary,
and low-rank approaches from the recent linear bandit literature:

  1. LinUCB              — standard ridge UCB, full d-dim  (Abbasi-Yadkori+ 2011)
  2. D-LinUCB            — discounted ridge UCB            (Russac+ NeurIPS 2019)
  3. SW-LinUCB           — sliding-window ridge UCB        (Cheung+ NeurIPS 2019)
  4. Oracle-LinUCB       — oracle subspace, r-dim UCB      (≈ LowOFUL, Jun+ ICML 2019)
  5. SPSC Algorithm 1    — our method: probes + r-dim UCB

All methods receive oracle change-point information (reset at segment
boundaries), isolating the dimension-reduction effect from change-point
detection.

Outputs
-------
  experiment_shuttle.png        — cumulative regret comparison
  experiment_shuttle_table.txt  — final regret table
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB, RunMetrics

# ---------------------------------------------------------------------------
# Sliding-Window LinUCB baseline  (Cheung et al., NeurIPS 2019)
# ---------------------------------------------------------------------------

class SWLinUCB:
    """
    Sliding-window LinUCB in full ambient space.
    Uses only the last W exploitation rounds for ridge regression.
    Resets at segment boundaries (oracle change-point info).
    """
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
            # Build windowed design
            win = [(xs, ys) for xs, ys, s in buf if s >= t - self.W]
            V = self.lam * np.eye(d)
            b = np.zeros(d)
            for xs, ys in win:
                V += np.outer(xs, xs)
                b += xs * ys
            theta_hat = np.linalg.solve(V, b)
            beta_t = self._beta(len(win))
            V_inv_A = np.linalg.solve(V, action_set.T).T
            ucb = action_set @ theta_hat + beta_t * np.sqrt(np.einsum('ij,ij->i', action_set, V_inv_A))
            x_dep = action_set[int(np.argmax(ucb))]
            y = env.step(x_dep, t)
            buf.append((x_dep, y, t))
            if len(buf) > self.W + 10:
                buf = [(xs, ys, s) for xs, ys, s in buf if s >= t - self.W]
            r_t = float(x_dep @ env.theta[t])
            metrics.control_regret[t] = r_opt - r_t
            metrics.costed_regret[t] = r_opt - r_t
        return metrics


# ---------------------------------------------------------------------------
# Shuttle Environment (semi-synthetic, matches LowRankLDSEnvironment)
# ---------------------------------------------------------------------------

class ShuttleEnvironment:
    """
    Semi-synthetic environment using Statlog Shuttle features.
    d=9 real sensor features, rank-r subspaces from class centroids,
    AR(1) dynamics within K piecewise-constant segments.
    """
    def __init__(self, d=9, r=2, K=4, T=10000, sigma_eps=0.3,
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
        data = fetch_openml('shuttle', version=1, as_frame=False, parser='auto')
        X_raw = data.data.astype(float)
        y_raw = data.target.astype(int)
        # Standardize
        scaler = StandardScaler()
        X_std = scaler.fit_transform(X_raw)
        d_raw = X_std.shape[1]  # 9

        # Add pairwise interaction features if d > d_raw
        if self.d > d_raw:
            interactions = []
            for i in range(d_raw):
                for j in range(i + 1, d_raw):
                    interactions.append(X_std[:, i] * X_std[:, j])
            X_inter = np.column_stack(interactions)  # (n, 36)
            X = np.hstack([X_std, X_inter])  # (n, 45)
            # Truncate to d if needed
            X = X[:, :self.d]
        else:
            X = X_std[:, :self.d]
        # Normalize rows to unit norm
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        X = X / np.maximum(norms, 1e-8)
        idx = self.rng.permutation(len(X))
        self._action_pool = X[idx]
        self._labels = y_raw[idx]
        # Class centroids for subspace construction
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
            Bk, Ak = self.B_list[k], self.spectral_radius * np.eye(self.r)
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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

D           = 15
R           = 2
K           = 4
T           = 10000
PROBE_EVERY = 30
PROBE_COST  = 0.1
WINDOW      = 100
N_SEEDS     = 10

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def make_env(seed):
    return ShuttleEnvironment(d=D, r=R, K=K, T=T, sigma_eps=0.3,
                              spectral_radius=0.99, n_actions=80,
                              seed=seed * 100, sigma_eta=0.04)


# ---------------------------------------------------------------------------
# Run all methods
# ---------------------------------------------------------------------------

def run_all(n_seeds):
    names = ["SPSC-Alg1", "LinUCB", "D-LinUCB", "SW-LinUCB", "Oracle-LinUCB"]
    results = {n: [] for n in names}

    for seed in range(n_seeds):
        print(f"  seed {seed+1}/{n_seeds} ...", end="\r", flush=True)

        # SPSC (our method)
        env = make_env(seed)
        results["SPSC-Alg1"].append(
            SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=1.0, delta=0.05, seed=seed,
                            normalize_gamma_by_d=True).run()
        )
        # LinUCB (standard, oracle change-points)
        env = make_env(seed)
        results["LinUCB"].append(
            LinUCB(env, lam=1.0, delta=0.05, seed=seed + 1000).run()
        )
        # D-LinUCB (discounted, Russac+ 2019)
        env = make_env(seed)
        results["D-LinUCB"].append(
            LinUCB(env, lam=1.0, delta=0.05, seed=seed + 2000,
                   forgetting_factor=0.998).run()
        )
        # SW-LinUCB (sliding window, Cheung+ 2019)
        env = make_env(seed)
        results["SW-LinUCB"].append(
            SWLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                     seed=seed + 3000).run()
        )
        # Oracle-LinUCB (known subspace, ≈ LowOFUL, Jun+ 2019)
        env = make_env(seed)
        results["Oracle-LinUCB"].append(
            OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                         seed=seed + 4000).run()
        )

    print(flush=True)
    return results


def agg(runs, attr):
    data = np.stack([getattr(r, attr) for r in runs])
    return data.mean(axis=0), data.std(axis=0) / np.sqrt(len(runs))


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(results, env_ref, out_path):
    t_axis = np.arange(1, T + 1)
    change_pts = env_ref.tau[1:]

    COLORS = {
        "SPSC-Alg1":     "#1f77b4",
        "LinUCB":        "#d62728",
        "D-LinUCB":      "#ff7f0e",
        "SW-LinUCB":     "#9467bd",
        "Oracle-LinUCB": "#2ca02c",
    }
    STYLES = {
        "SPSC-Alg1":     "-",
        "LinUCB":        "--",
        "D-LinUCB":      "-.",
        "SW-LinUCB":     "-.",
        "Oracle-LinUCB": ":",
    }
    LABELS = {
        "SPSC-Alg1":     f"SPSC Alg 1 (ours, $r={R}$)",
        "LinUCB":        f"LinUCB ($d={D}$)",
        "D-LinUCB":      f"D-LinUCB ($d={D}$, $\\gamma=0.998$)",
        "SW-LinUCB":     f"SW-LinUCB ($d={D}$, $W={WINDOW}$)",
        "Oracle-LinUCB": f"Oracle ($r={R}$, known subspace)",
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.subplots_adjust(wspace=0.28)

    panel_info = [
        ("cumulative_costed_regret",
         r"Cumulative Costed Regret",
         "(a) Costed regret (incl. probe cost)"),
        ("cumulative_control_regret",
         r"Cumulative Control Regret",
         "(b) Control regret (excl. probe cost)"),
    ]

    for ax, (attr, ylabel, title) in zip(axes, panel_info):
        for name in ["Oracle-LinUCB", "SPSC-Alg1", "SW-LinUCB", "D-LinUCB", "LinUCB"]:
            runs = results[name]
            mean, se = agg(runs, attr)
            ax.plot(t_axis, mean, color=COLORS[name], ls=STYLES[name],
                    lw=2.0, label=LABELS[name], zorder=3)
            ax.fill_between(t_axis, mean - se, mean + se,
                            color=COLORS[name], alpha=0.12, zorder=2)
        for cp in change_pts:
            ax.axvline(cp, color="gray", ls=":", lw=1.0, alpha=0.5)
        ax.set_xlabel("Round $t$", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=11)
        ax.legend(fontsize=8, loc="upper left")
        ax.set_xlim(1, T)
        ax.set_ylim(bottom=0)
        ax.tick_params(labelsize=9)

    fig.suptitle(
        f"Shuttle Benchmark: $d={D}$, $r={R}$, $K={K}$, $T={T}$, "
        f"$c={PROBE_COST}$  ($n={N_SEEDS}$ seeds, bands = $\\pm 1$ SE)",
        fontsize=11, y=1.02,
    )
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

def print_table(results, env_ref):
    n = N_SEEDS
    d = env_ref.d

    print()
    print("=" * 90)
    print("Shuttle Benchmark — Comprehensive Comparison")
    print(f"d={d}, r={R}, K={K}, T={T}, probe_every={PROBE_EVERY}, W={WINDOW}, c={PROBE_COST}")
    print("-" * 90)
    header = (f"{'Method':<22} {'Source':<25} {'Costed (mean+-SE)':>18} "
              f"{'Control (mean+-SE)':>18} {'Probes':>7}")
    print(header)
    print("-" * 90)

    order = ["Oracle-LinUCB", "SPSC-Alg1", "SW-LinUCB", "D-LinUCB", "LinUCB"]
    sources = {
        "SPSC-Alg1":     "This work",
        "LinUCB":        "Abbasi-Yadkori+ 2011",
        "D-LinUCB":      "Russac+ NeurIPS 2019",
        "SW-LinUCB":     "Cheung+ NeurIPS 2019",
        "Oracle-LinUCB": "Jun+ ICML 2019",
    }
    finals = {}
    for name in order:
        runs = results[name]
        costed  = np.array([r.cumulative_costed_regret[-1] for r in runs])
        control = np.array([r.cumulative_control_regret[-1] for r in runs])
        probes  = np.array([r.total_probes for r in runs])
        finals[name] = costed.mean()
        print(
            f"  {name:<20} {sources[name]:<25} "
            f"{costed.mean():>7.1f} +- {costed.std()/np.sqrt(n):>5.1f} "
            f"{control.mean():>7.1f} +- {control.std()/np.sqrt(n):>5.1f} "
            f"{probes.mean():>7.0f}"
        )

    print("-" * 90)
    spsc = finals["SPSC-Alg1"]
    for baseline in ["LinUCB", "D-LinUCB", "SW-LinUCB"]:
        bl = finals[baseline]
        if spsc < bl:
            pct = (1 - spsc / bl) * 100
            print(f"  SPSC vs {baseline:<15}: {pct:>5.1f}% regret reduction  (ratio {spsc/bl:.3f})")
        else:
            print(f"  SPSC vs {baseline:<15}: {baseline} wins (ratio {spsc/bl:.3f})")
    ora = finals["Oracle-LinUCB"]
    print(f"  SPSC vs Oracle         : within {spsc/ora:.2f}x of oracle ceiling")
    print()
    print("  Regret scaling (theory):")
    print(f"    LinUCB / D-LinUCB / SW-LinUCB:  O(d*sqrt(T)) = O({d}*{int(T**0.5)}) = O({d*int(T**0.5)})")
    print(f"    SPSC (ours):                    O(r*sqrt(T) + sqrt(cT)) = O({R}*{int(T**0.5)} + {int((PROBE_COST*T)**0.5)}) = O({R*int(T**0.5) + int((PROBE_COST*T)**0.5)})")
    print(f"    Oracle / LowOFUL:               O(r*sqrt(T)) = O({R}*{int(T**0.5)}) = O({R*int(T**0.5)})")
    print("=" * 90)

    return finals


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading Shuttle dataset ...")
    env_ref = make_env(0)

    print(f"\n{'='*60}")
    print("Shuttle Semi-Synthetic Benchmark")
    print(f"  d={D}, r={R}, K={K}, T={T}")
    print(f"  probe_every={PROBE_EVERY}, window={WINDOW}, c={PROBE_COST}")
    print(f"  n_actions={env_ref.n_actions}, sigma_eps={env_ref.sigma_eps}")
    print(f"  Segment boundaries: {env_ref.tau}")
    print(f"  max ||theta_t|| = {env_ref.S:.4f}")
    print(f"  n_seeds={N_SEEDS}")
    print(f"{'='*60}")

    # SVD analysis
    print("\nSubspace analysis:")
    for k in range(K):
        s, e = env_ref.tau[k], env_ref.tau[k] + env_ref.segment_lengths[k]
        _, sv, _ = np.linalg.svd(env_ref.theta[s:e], full_matrices=False)
        cv = np.cumsum(sv**2) / np.sum(sv**2)
        print(f"  Seg {k+1}: top SV={sv[:3].round(3)}, rank-{R} captures {cv[R-1]*100:.1f}%")
    for k in range(1, K):
        d12 = np.linalg.norm(env_ref.segment_projector(k) - env_ref.segment_projector(k-1), 'fro')
        print(f"  ||P_{k} - P_{k+1}||_F = {d12:.3f}")

    print(f"\nRunning {N_SEEDS} seeds x 5 methods ...")
    results = run_all(N_SEEDS)
    finals = print_table(results, env_ref)
    make_figure(results, env_ref, os.path.join(OUT_DIR, "experiment_shuttle.png"))
    print("\nDone.")
