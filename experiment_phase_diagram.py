"""
Phase Diagram: Where does subspace exploitation pay off?

Sweeps (d, r) on the Pendigits dataset and renders a filled-contour
"phase diagram" of the SPSC / baseline regret ratio.  Blue = SPSC wins,
red = SPSC loses, white = break-even.

This visualization is rare in the bandit literature and immediately
conveys the *operating regime* of the method.

Dataset: UCI Pendigits (10,992 samples, 16 features, 10 digit classes).
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib import ticker

sys.path.insert(0, os.path.dirname(__file__))
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Pendigits Environment
# ---------------------------------------------------------------------------

class PendigitsEnvironment:
    """
    Semi-synthetic environment using UCI Pendigits features.
    16 raw features (x,y coords of pen strokes), augmented with
    pairwise interactions for higher d.
    """
    def __init__(self, d=16, r=2, K=4, T=5000, sigma_eps=0.3,
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
        data = fetch_openml('pendigits', version=1, as_frame=False, parser='auto')
        X_raw = data.data.astype(float)
        y_raw = data.target.astype(int)
        d_raw = X_raw.shape[1]  # 16

        scaler = StandardScaler()
        X_std = scaler.fit_transform(X_raw)

        # Augment with pairwise interactions if d > d_raw
        if self.d > d_raw:
            interactions = []
            for i in range(d_raw):
                for j in range(i + 1, d_raw):
                    interactions.append(X_std[:, i] * X_std[:, j])
            X_inter = np.column_stack(interactions)  # (n, 120)
            X = np.hstack([X_std, X_inter])  # (n, 136)
            X = X[:, :self.d]
        else:
            X = X_std[:, :self.d]

        # Normalize rows to unit norm
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


# ---------------------------------------------------------------------------
# Sweep parameters
# ---------------------------------------------------------------------------

D_GRID = [6, 8, 10, 14, 20, 30]
R_GRID = [1, 2, 3, 5]
T_SWEEP = 5000
K = 4
N_SEEDS = 5
PROBE_EVERY = 30
PROBE_COST = 0.1
WINDOW = 100


def run_single(d, r, seed):
    """Run SPSC, LinUCB, Oracle on a single (d, r, seed) config."""
    env = PendigitsEnvironment(d=d, r=r, K=K, T=T_SWEEP, sigma_eps=0.3,
                                spectral_radius=0.99, n_actions=80,
                                seed=seed * 100, sigma_eta=0.04)

    spsc_result = SPSC_Algorithm1(
        env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
        window=WINDOW, lam=1.0, delta=0.05, seed=seed,
        normalize_gamma_by_d=True
    ).run()

    env2 = PendigitsEnvironment(d=d, r=r, K=K, T=T_SWEEP, sigma_eps=0.3,
                                 spectral_radius=0.99, n_actions=80,
                                 seed=seed * 100, sigma_eta=0.04)
    linucb_result = LinUCB(env2, lam=1.0, delta=0.05, seed=seed + 1000).run()

    env3 = PendigitsEnvironment(d=d, r=r, K=K, T=T_SWEEP, sigma_eps=0.3,
                                 spectral_radius=0.99, n_actions=80,
                                 seed=seed * 100, sigma_eta=0.04)
    oracle_result = OracleLinUCB(env3, window=WINDOW, lam=1.0, delta=0.05,
                                  seed=seed + 2000).run()

    return (spsc_result.cumulative_costed_regret[-1],
            linucb_result.cumulative_costed_regret[-1],
            oracle_result.cumulative_costed_regret[-1])


# ---------------------------------------------------------------------------
# Main sweep
# ---------------------------------------------------------------------------

def run_sweep():
    n_d, n_r = len(D_GRID), len(R_GRID)
    ratio_spsc_lin = np.zeros((n_r, n_d))
    ratio_spsc_oracle = np.zeros((n_r, n_d))
    spsc_regret = np.zeros((n_r, n_d))
    lin_regret = np.zeros((n_r, n_d))
    oracle_regret = np.zeros((n_r, n_d))

    total = n_d * n_r
    done = 0
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r >= d:
                # Skip: rank can't exceed dimension
                ratio_spsc_lin[i, j] = 1.0
                ratio_spsc_oracle[i, j] = 1.0
                done += 1
                continue

            print(f"  [{done+1}/{total}] d={d}, r={r} ({N_SEEDS} seeds) ...",
                  end="", flush=True)

            spsc_vals, lin_vals, ora_vals = [], [], []
            for seed in range(N_SEEDS):
                s, l, o = run_single(d, r, seed)
                spsc_vals.append(s)
                lin_vals.append(l)
                ora_vals.append(o)

            s_mean = np.mean(spsc_vals)
            l_mean = np.mean(lin_vals)
            o_mean = np.mean(ora_vals)

            ratio_spsc_lin[i, j] = s_mean / max(l_mean, 1e-8)
            ratio_spsc_oracle[i, j] = s_mean / max(o_mean, 1e-8)
            spsc_regret[i, j] = s_mean
            lin_regret[i, j] = l_mean
            oracle_regret[i, j] = o_mean

            pct = (1 - ratio_spsc_lin[i, j]) * 100
            tag = "SPSC wins" if pct > 0 else "LinUCB wins"
            print(f"  ratio={ratio_spsc_lin[i,j]:.3f}  ({tag}, {abs(pct):.0f}%)")

            done += 1

    return ratio_spsc_lin, ratio_spsc_oracle, spsc_regret, lin_regret, oracle_regret


# ---------------------------------------------------------------------------
# Phase Diagram Figure
# ---------------------------------------------------------------------------

def make_phase_diagram(ratio_spsc_lin, ratio_spsc_oracle,
                       spsc_regret, lin_regret, oracle_regret):

    # ---- Use a high-quality style ----
    plt.rcParams.update({
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.linewidth": 1.2,
    })

    fig = plt.figure(figsize=(14.5, 5.8))

    # Three-panel layout: heatmap (wide) | theory curves | oracle gap
    gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 1, 1], wspace=0.35)
    ax_heat = fig.add_subplot(gs[0])
    ax_theory = fig.add_subplot(gs[1])
    ax_oracle = fig.add_subplot(gs[2])

    d_arr = np.array(D_GRID, dtype=float)
    r_arr = np.array(R_GRID, dtype=float)

    # ======================================================================
    # Panel (a): SPSC / LinUCB heatmap — the main eye-catcher
    # ======================================================================
    ax = ax_heat

    vmin = min(0.55, ratio_spsc_lin.min() - 0.03)
    vmax = max(1.15, ratio_spsc_lin.max() + 0.03)
    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)

    # Use integer grid indices for equal-width cells
    n_d, n_r = len(D_GRID), len(R_GRID)
    im = ax.imshow(ratio_spsc_lin, cmap="RdBu_r", norm=norm,
                   aspect="auto", origin="lower",
                   extent=[-0.5, n_d - 0.5, -0.5, n_r - 0.5],
                   interpolation="nearest")

    # Draw white grid lines
    for xi in range(n_d + 1):
        ax.axvline(xi - 0.5, color="white", lw=2)
    for yi in range(n_r + 1):
        ax.axhline(yi - 0.5, color="white", lw=2)

    # Annotate each cell
    for i, r_val in enumerate(R_GRID):
        for j, d_val in enumerate(D_GRID):
            val = ratio_spsc_lin[i, j]
            if r_val >= d_val:
                ax.text(j, i, "n/a", ha="center", va="center",
                        fontsize=8, color="gray", style="italic")
            else:
                pct = (1 - val) * 100
                txt_color = "white" if abs(val - 1.0) > 0.20 else "#222222"
                # Ratio + direction arrow
                arrow = r"$\downarrow$" if pct > 0 else r"$\uparrow$"
                label = f"{val:.2f}\n{arrow}{abs(pct):.0f}%"
                ax.text(j, i, label, ha="center", va="center",
                        fontsize=9.5, fontweight="bold", color=txt_color,
                        linespacing=1.3)

    cbar = fig.colorbar(im, ax=ax, shrink=0.82, pad=0.03, aspect=25)
    cbar.set_label("SPSC / LinUCB  regret ratio", fontsize=10.5, labelpad=8)
    # Mark ratio=1.0 on colorbar
    cbar.ax.axhline(1.0, color="black", lw=2, ls="-")
    cbar.ax.tick_params(labelsize=9)

    ax.set_xlabel("Ambient dimension $d$", fontsize=12)
    ax.set_ylabel("Subspace rank $r$", fontsize=12)
    ax.set_title("(a)  Operating Regime", fontsize=13, fontweight="bold", pad=10)
    ax.set_xticks(range(n_d))
    ax.set_xticklabels([str(d) for d in D_GRID])
    ax.set_yticks(range(n_r))
    ax.set_yticklabels([str(r) for r in R_GRID])
    ax.tick_params(labelsize=10)

    # ======================================================================
    # Panel (b): Empirical ratio vs theory — per rank
    # ======================================================================
    ax2 = ax_theory
    markers = ['o', 's', 'D', '^']
    cmap_r = plt.cm.cool(np.linspace(0.1, 0.9, len(R_GRID)))

    for i, r_val in enumerate(R_GRID):
        emp, thy, dv = [], [], []
        for j, d_val in enumerate(D_GRID):
            if r_val >= d_val:
                continue
            emp.append(ratio_spsc_lin[i, j])
            thy.append(np.sqrt(r_val / d_val))
            dv.append(d_val)
        ax2.plot(dv, emp, marker=markers[i], color=cmap_r[i], lw=2.2,
                 markersize=7.5, zorder=4, label=f"$r={r_val}$",
                 markeredgecolor="white", markeredgewidth=0.8)
        ax2.plot(dv, thy, ls="--", color=cmap_r[i], lw=1.0, alpha=0.45, zorder=2)

    ax2.plot([], [], ls="--", color="gray", lw=1.0,
             label=r"$\sqrt{r/d}$ (asymptotic)")
    ax2.axhline(1.0, color="black", ls=":", lw=0.8, alpha=0.4)
    ax2.fill_between([D_GRID[0] - 1, D_GRID[-1] + 4], 0, 1.0,
                     color="#2166ac", alpha=0.05, zorder=0)
    ax2.fill_between([D_GRID[0] - 1, D_GRID[-1] + 4], 1.0, 1.8,
                     color="#b2182b", alpha=0.05, zorder=0)

    ax2.set_xlabel("Ambient dimension $d$", fontsize=12)
    ax2.set_ylabel("Regret ratio", fontsize=12)
    ax2.set_title("(b)  Empirical vs Theory", fontsize=13, fontweight="bold", pad=10)
    ax2.legend(fontsize=8.5, loc="upper right", framealpha=0.92,
               edgecolor="#cccccc")
    ax2.set_xlim(D_GRID[0] - 1, D_GRID[-1] + 4)
    ax2.set_ylim(0.15, 1.35)
    ax2.tick_params(labelsize=10)

    # ======================================================================
    # Panel (c): Oracle gap — how close SPSC gets to the ceiling
    # ======================================================================
    ax3 = ax_oracle

    bar_width = 0.18
    x_pos = np.arange(len(D_GRID))

    for i, r_val in enumerate(R_GRID):
        gaps = []
        for j, d_val in enumerate(D_GRID):
            if r_val >= d_val or oracle_regret[i, j] < 1:
                gaps.append(0)
            else:
                gaps.append(spsc_regret[i, j] / oracle_regret[i, j])
        offset = (i - len(R_GRID) / 2 + 0.5) * bar_width
        bars = ax3.bar(x_pos + offset, gaps, bar_width * 0.92,
                       color=cmap_r[i], edgecolor="white", lw=0.6,
                       label=f"$r={r_val}$", alpha=0.88, zorder=3)

    ax3.axhline(1.0, color="#2ca02c", ls="-", lw=2.5, alpha=0.7,
                label="Oracle ceiling", zorder=5)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels([str(d) for d in D_GRID])
    ax3.set_xlabel("Ambient dimension $d$", fontsize=12)
    ax3.set_ylabel("SPSC / Oracle ratio", fontsize=12)
    ax3.set_title("(c)  Distance to Oracle", fontsize=13, fontweight="bold", pad=10)
    ax3.legend(fontsize=8, loc="upper right", framealpha=0.92,
               edgecolor="#cccccc")
    ax3.set_ylim(0, 3.5)
    ax3.tick_params(labelsize=10)

    fig.suptitle(
        r"$\mathbf{Pendigits\ Phase\ Diagram}$:  "
        r"Subspace Exploitation Regime"
        f"\n$K={K}$,  $T={T_SWEEP:,}$,  "
        f"$n_{{\\mathrm{{act}}}}=80$,  "
        r"probe\_every$=30$,  $c=0.1$"
        f"   ({N_SEEDS} seeds / cell)",
        fontsize=12.5, y=1.04,
    )

    out_path = os.path.join(OUT_DIR, "experiment_phase_diagram.png")
    plt.savefig(out_path, bbox_inches="tight", dpi=200)
    print(f"\nSaved: {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cache_path = os.path.join(OUT_DIR, "phase_diagram_data.npz")

    # If --replot flag, just regenerate figure from cached data
    if len(sys.argv) > 1 and sys.argv[1] == "--replot" and os.path.isfile(cache_path):
        print("Replotting from cached data ...")
        cached = np.load(cache_path)
        ratio_sl = cached["ratio_spsc_lin"]
        ratio_so = cached["ratio_spsc_oracle"]
        spsc_r = cached["spsc_regret"]
        lin_r = cached["lin_regret"]
        ora_r = cached["oracle_regret"]
        make_phase_diagram(ratio_sl, ratio_so, spsc_r, lin_r, ora_r)
        print("Done.")
        sys.exit(0)

    print("=" * 65)
    print("Phase Diagram Sweep: Pendigits (d, r) grid")
    print(f"  d in {D_GRID}")
    print(f"  r in {R_GRID}")
    print(f"  T={T_SWEEP}, K={K}, seeds={N_SEEDS}")
    print("=" * 65)

    ratio_sl, ratio_so, spsc_r, lin_r, ora_r = run_sweep()

    # Print summary table
    print("\n" + "=" * 65)
    print("SPSC / LinUCB regret ratio  (< 1 = SPSC wins)")
    print("-" * 65)
    header = f"{'r \\\\ d':>6}" + "".join(f"{d:>8}" for d in D_GRID)
    print(header)
    print("-" * 65)
    for i, r in enumerate(R_GRID):
        row = f"{r:>6}"
        for j, d in enumerate(D_GRID):
            if r >= d:
                row += f"{'---':>8}"
            else:
                row += f"{ratio_sl[i,j]:>8.3f}"
        print(row)
    print("=" * 65)

    make_phase_diagram(ratio_sl, ratio_so, spsc_r, lin_r, ora_r)

    # Save raw data
    np.savez_compressed(
        os.path.join(OUT_DIR, "phase_diagram_data.npz"),
        d_grid=np.array(D_GRID), r_grid=np.array(R_GRID),
        ratio_spsc_lin=ratio_sl, ratio_spsc_oracle=ratio_so,
        spsc_regret=spsc_r, lin_regret=lin_r, oracle_regret=ora_r,
    )
    print("Saved raw data to phase_diagram_data.npz")
    print("\nDone.")
