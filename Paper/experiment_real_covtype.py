"""
Experiment: Forest Covertype -- Real-Data-Calibrated Bandit.

Real data from UCI Covertype (581K samples, 54 features, 7 cover types).
theta_t derived from real OLS of features -> cover type labels.
d=55 (10 quantitative + 45 interactions), r=3, sorted by elevation.

Compares SPSC Alg 1, LinUCB, D-LinUCB, SW-LinUCB, Oracle-LinUCB.

Outputs:
  experiment_real_covtype.png  -- 3-panel figure
  Printed summary table
"""

import os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from real_covtype_environment import RealCovtypeEnvironment
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB, RunMetrics

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Non-stationary baselines
# ---------------------------------------------------------------------------

class SWLinUCB:
    def __init__(self, env, window=200, lam=0.01, delta=0.05, seed=1):
        self.env, self.W, self.lam, self.delta = env, window, lam, delta
        self.rng = np.random.default_rng(seed)
        self.S, self.sigma_eps, self.L_x = env.S, env.sigma_eps, env.L_x

    def _beta(self, n):
        d = self.env.d
        arg = max(1.0 + n * self.L_x**2 / self.lam, 1.0 + 1e-12)
        return self.sigma_eps * np.sqrt(d * np.log(arg / self.delta)) + np.sqrt(self.lam) * self.S

    def run(self):
        env = self.env; d, T = env.d, env.T
        metrics = RunMetrics(name="SW-LinUCB", T=T)
        buf, current_k = [], -1
        for t in range(T):
            k = env.seg_of[t]
            if k != current_k:
                buf, current_k = [], k
            action_set = env.get_action_set(t, rng=self.rng)
            r_opt = env.optimal_reward(action_set, t)
            win = [(xs, ys) for xs, ys, s in buf if s >= t - self.W]
            V = self.lam * np.eye(d); b = np.zeros(d)
            for xs, ys in win:
                V += np.outer(xs, xs); b += xs * ys
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


class DLinUCB:
    def __init__(self, env, gamma=0.995, lam=0.01, delta=0.05, seed=1):
        self.env, self.gamma, self.lam, self.delta = env, gamma, lam, delta
        self.rng = np.random.default_rng(seed)
        self.S, self.sigma_eps, self.L_x = env.S, env.sigma_eps, env.L_x

    def _beta(self, t):
        d = self.env.d
        arg = max(1.0 + t * self.L_x**2 / self.lam, 1.0 + 1e-12)
        return self.sigma_eps * np.sqrt(d * np.log(arg / self.delta)) + np.sqrt(self.lam) * self.S

    def run(self):
        env = self.env; d, T = env.d, env.T
        metrics = RunMetrics(name="D-LinUCB", T=T)
        V = self.lam * np.eye(d); b = np.zeros(d)
        current_k = -1
        for t in range(T):
            k = env.seg_of[t]
            if k != current_k:
                V = self.lam * np.eye(d); b = np.zeros(d); current_k = k
            action_set = env.get_action_set(t, rng=self.rng)
            r_opt = env.optimal_reward(action_set, t)
            theta_hat = np.linalg.solve(V, b)
            beta_t = self._beta(t)
            V_inv_A = np.linalg.solve(V, action_set.T).T
            ucb = action_set @ theta_hat + beta_t * np.sqrt(
                np.einsum('ij,ij->i', action_set, V_inv_A))
            x_dep = action_set[int(np.argmax(ucb))]
            y = env.step(x_dep, t)
            V = self.gamma * V + np.outer(x_dep, x_dep)
            b = self.gamma * b + x_dep * y
            r_t = float(x_dep @ env.theta[t])
            metrics.control_regret[t] = r_opt - r_t
            metrics.costed_regret[t] = r_opt - r_t
        return metrics


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

R            = 3
PROBE_EVERY  = 10
PROBE_COST   = 0.02
WINDOW       = 600
SEG_SIZE     = 500
N_SEGMENTS   = 20
N_SEEDS      = 3

NAMES  = ["SPSC-Alg1", "Oracle-LinUCB", "D-LinUCB", "SW-LinUCB", "LinUCB"]
COLORS = {
    "SPSC-Alg1":     "#1f77b4",
    "Oracle-LinUCB": "#2ca02c",
    "D-LinUCB":      "#ff7f0e",
    "SW-LinUCB":     "#9467bd",
    "LinUCB":        "#d62728",
}
STYLES = {"SPSC-Alg1": "-", "Oracle-LinUCB": ":", "D-LinUCB": "--",
          "SW-LinUCB": "-.", "LinUCB": "--"}


def _labels(r, d):
    return {
        "SPSC-Alg1":     f"SPSC Alg. 1 (ours, $r={r}$)",
        "Oracle-LinUCB": f"Oracle LinUCB ($r={r}$)",
        "D-LinUCB":      "D-LinUCB ($\\gamma\\!=\\!0.995$)",
        "SW-LinUCB":     "SW-LinUCB ($W\\!=\\!200$)",
        "LinUCB":        f"LinUCB (ambient $d\\!=\\!{d}$)",
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def make_env(seed):
    return RealCovtypeEnvironment(
        r=R, n_actions=40, segment_size=SEG_SIZE,
        n_segments=N_SEGMENTS, seed=seed * 13 + 7,
    )


def run_all(n_seeds):
    results = {n: [] for n in NAMES}
    for seed in range(n_seeds):
        print(f"  seed {seed+1}/{n_seeds} ...", end="\r", flush=True)
        for name in NAMES:
            env = make_env(seed)
            if name == "SPSC-Alg1":
                m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY,
                                    probe_cost=PROBE_COST, window=WINDOW,
                                    lam=0.01, delta=0.05, seed=seed,
                                    normalize_gamma_by_d=True).run()
            elif name == "Oracle-LinUCB":
                m = OracleLinUCB(env, window=10000, lam=0.01, delta=0.05,
                                 seed=seed + 1000).run()
            elif name == "D-LinUCB":
                m = DLinUCB(env, gamma=0.995, lam=0.01, delta=0.05,
                            seed=seed + 2000).run()
            elif name == "SW-LinUCB":
                m = SWLinUCB(env, window=200, lam=0.01, delta=0.05,
                             seed=seed + 3000).run()
            elif name == "LinUCB":
                m = LinUCB(env, lam=0.01, delta=0.05,
                           seed=seed + 4000).run()
            results[name].append(m)
    print(flush=True)
    return results


def agg(runs, attr):
    data = np.stack([getattr(r, attr) for r in runs])
    return data.mean(axis=0), data.std(axis=0) / np.sqrt(len(runs))


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(results, env_ref, out_path, labels):
    T = env_ref.T
    t_axis = np.arange(1, T + 1)

    fig, axes = plt.subplots(1, 3, figsize=(17, 4.5))

    # Panel (a): Cumulative control regret
    ax = axes[0]
    for name in NAMES:
        mean, se = agg(results[name], "cumulative_control_regret")
        ax.plot(t_axis, mean, color=COLORS[name], ls=STYLES[name],
                lw=2.0, label=labels[name])
        ax.fill_between(t_axis, mean - se, mean + se,
                        color=COLORS[name], alpha=0.12)
    for cp in env_ref.tau[1::4]:
        ax.axvline(cp, color="gray", ls=":", lw=0.6, alpha=0.4)
    ax.set_xlabel("Round $t$")
    ax.set_ylabel("Cumulative Control Regret")
    ax.set_title("(a) Cumulative regret")
    ax.legend(fontsize=7, loc="upper left")
    ax.set_xlim(1, T); ax.set_ylim(bottom=0)

    # Panel (b): SVD spectrum
    ax = axes[1]
    spec = env_ref.svd_spectrum()
    cumvar = np.cumsum(spec)
    n_show = min(10, len(spec))
    x = np.arange(1, n_show + 1)
    ax.bar(x, spec[:n_show], color="#1f77b4", alpha=0.7, label="SV share")
    ax.plot(x, cumvar[:n_show], "o-", color="#d62728", lw=2, label="Cumulative")
    ax.axhline(0.90, ls="--", color="gray", lw=1, alpha=0.7)
    ax.text(n_show - 1, 0.91, "90%", color="gray", fontsize=9)
    ax.set_xlabel("Singular value index")
    ax.set_ylabel("Fraction of variance")
    ax.set_title("(b) Theta SVD spectrum (low-rank evidence)")
    ax.legend(fontsize=8); ax.set_ylim(0, 1.05)

    # Panel (c): Bar chart
    ax = axes[2]
    final_means, final_ses = [], []
    for name in NAMES:
        finals = np.array([r.cumulative_control_regret[-1] for r in results[name]])
        final_means.append(finals.mean())
        final_ses.append(finals.std() / np.sqrt(len(finals)))
    xp = np.arange(len(NAMES))
    ax.bar(xp, final_means, yerr=final_ses,
           color=[COLORS[n] for n in NAMES], capsize=4)
    ax.set_xticks(xp)
    ax.set_xticklabels([labels[n].split("(")[0].strip() for n in NAMES],
                       rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("Final Control Regret")
    ax.set_title("(c) Final regret comparison")
    for i, (m, s) in enumerate(zip(final_means, final_ses)):
        ax.text(i, m + s + max(final_means) * 0.02, f"{m:.0f}",
                ha="center", va="bottom", fontsize=8)

    fig.suptitle(
        f"Covertype Real-Data Bandit  |  "
        f"$d={env_ref.d}$, $r={R}$, {env_ref.K} segments, "
        f"$T={T}$  ({N_SEEDS} seeds, $\\pm 1$ SE)",
        fontsize=10, y=1.01)
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

def print_table(results, env_ref, labels):
    print()
    print("=" * 90)
    print("Covertype Real-Data Bandit")
    print(f"  d={env_ref.d}, r={R}, K={env_ref.K} segments, T={env_ref.T}")
    print(f"  sigma_eps={env_ref.sigma_eps:.3f}, S={env_ref.S:.4f}")
    spec = env_ref.svd_spectrum()
    print(f"  Theta SVD: SV1={spec[0]:.1%}, SV1-3={sum(spec[:3]):.1%}, "
          f"SV1-5={sum(spec[:5]):.1%}")
    print("-" * 90)
    print(f"  {'Algorithm':<36}  {'Control regret (mean+-SE)':>25}  "
          f"{'vs LinUCB':>12}  {'Probes':>7}")
    print("-" * 90)

    linucb_final = np.mean([r.cumulative_control_regret[-1]
                            for r in results["LinUCB"]])

    for name in NAMES:
        ctrl = np.array([r.cumulative_control_regret[-1] for r in results[name]])
        probes = np.array([r.total_probes for r in results[name]])
        n = len(ctrl)
        pct = (1 - ctrl.mean() / linucb_final) * 100 if name != "LinUCB" else 0
        vs_str = f"-{pct:.1f}%" if pct > 0 else (f"+{-pct:.1f}%" if pct < 0 else "---")
        print(f"  {labels[name]:<36}  {ctrl.mean():>10.1f} +- {ctrl.std()/np.sqrt(n):>7.1f}  "
              f"  {vs_str:>10}  {probes.mean():>7.0f}")
    print("=" * 90)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Covertype -- Real-Data-Calibrated Bandit")
    print("  Using SPSC Algorithm 1 (sphere probes + K-inverse)")
    print("=" * 60)

    env_ref = make_env(0)
    d = env_ref.d
    print(f"  d={d}, r={R}, K={env_ref.K} segments, T={env_ref.T}")
    print(f"  sigma_eps={env_ref.sigma_eps:.3f}, S={env_ref.S:.4f}")

    spec = env_ref.svd_spectrum()
    print(f"  Theta SVD: SV1={spec[0]:.1%}, SV1-3={sum(spec[:3]):.1%}, "
          f"SV1-5={sum(spec[:5]):.1%}")

    labels = _labels(R, d)

    print(f"\nRunning {N_SEEDS} seeds ...")
    results = run_all(N_SEEDS)

    print_table(results, env_ref, labels)
    make_figure(results, env_ref,
                os.path.join(OUT_DIR, "experiment_real_covtype.png"), labels)
    print("Done.\n")
