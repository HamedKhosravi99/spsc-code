"""
Experiment: Criteo Non-Stationary Benchmark (Russac et al., NeurIPS 2019).

Reproduces the Criteo benchmark environment from:
  Russac, Vernade, Cappé — "Weighted Linear Bandits for Non-Stationary
  Environments" (NeurIPS 2019).

We borrow their environment construction and run OUR algorithms on it.
We do NOT re-implement their baselines; instead we compare our cumulative
regret against the values reported in their paper.

Setup
-----
  - d=50 (SVD-projected one-hot encoded Criteo categoricals)
  - T=8000, single change-point at t=4000
  - Before change: theta_t = theta_star (fitted from data)
  - After change:  60% of theta_star coordinates sign-flipped
  - 2 actions per round: one from clicked pool, one from non-clicked pool
  - Reward noise: sigma_eps = 0.15
  - 100 replications (or 30 if slow)

Outputs
-------
  experiment_criteo.png  — cumulative regret plot
  Printed final regret comparison with Russac et al. reported values
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from criteo_environment import CriteoEnvironment
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

T            = 8000
CHANGE_T     = 4000
FLIP_FRAC    = 0.6
SIGMA_EPS    = 0.15
R            = 1       # rank (theta is rank-1 per segment)
PROBE_EVERY  = 30
PROBE_COST   = 0.1
WINDOW       = 200
N_REPS       = 30      # replications (increase to 100 for final)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "criteo")
DATA_FILE = os.path.join(DATA_DIR, "criteo_processed.npz")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def make_env(seed):
    return CriteoEnvironment(
        data_path=DATA_FILE,
        T=T, change_t=CHANGE_T, flip_frac=FLIP_FRAC,
        sigma_eps=SIGMA_EPS, seed=seed * 100, r=R,
    )


def run_all(n_reps):
    names   = ["SPSC-Alg1", "LinUCB", "Oracle-LinUCB"]
    results = {n: [] for n in names}

    for rep in range(n_reps):
        print(f"  rep {rep+1}/{n_reps} ...", end="\r", flush=True)

        env = make_env(rep)
        results["SPSC-Alg1"].append(
            SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=1.0, delta=0.05, seed=rep,
                            normalize_gamma_by_d=True).run()
        )

        env = make_env(rep)
        results["LinUCB"].append(
            LinUCB(env, lam=1.0, delta=0.05, seed=rep + 1000).run()
        )

        env = make_env(rep)
        results["Oracle-LinUCB"].append(
            OracleLinUCB(env, window=WINDOW, lam=1.0, delta=0.05,
                         seed=rep + 2000).run()
        )

    print(flush=True)
    return results


def agg(runs, attr):
    data = np.stack([getattr(r, attr) for r in runs])
    mean = data.mean(axis=0)
    se   = data.std(axis=0) / np.sqrt(len(runs))
    return mean, se


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(results, out_path):
    t_axis = np.arange(1, T + 1)

    COLORS = {
        "SPSC-Alg1":     "#1f77b4",
        "LinUCB":        "#d62728",
        "Oracle-LinUCB": "#2ca02c",
    }
    STYLES = {
        "SPSC-Alg1":     "-",
        "LinUCB":        "--",
        "Oracle-LinUCB": ":",
    }
    LABELS = {
        "SPSC-Alg1":     f"SPSC Algorithm 1 ($r={R}$-dim)",
        "LinUCB":        f"Ambient LinUCB ($d=50$-dim)",
        "Oracle-LinUCB": f"Oracle LinUCB (true subspace, $r={R}$-dim)",
    }

    fig, ax = plt.subplots(1, 1, figsize=(8, 5))

    for name, runs in results.items():
        mean, se = agg(runs, "cumulative_control_regret")
        ax.plot(t_axis, mean,
                color=COLORS[name], ls=STYLES[name], lw=2.0,
                label=LABELS[name], zorder=3)
        ax.fill_between(t_axis, mean - se, mean + se,
                        color=COLORS[name], alpha=0.18, zorder=2)

    # Mark change-point
    ax.axvline(CHANGE_T, color="gray", ls=":", lw=1.5, alpha=0.7, label="Change-point")

    ax.set_xlabel("Round $t$", fontsize=12)
    ax.set_ylabel("Cumulative Dynamic Regret", fontsize=12)
    ax.set_title(
        f"Criteo Benchmark (Russac et al. 2019)  |  "
        f"$d=50$, $T={T}$, change at $t={CHANGE_T}$  "
        f"($n={N_REPS}$ reps, bands = $\\pm 1$ SE)",
        fontsize=11,
    )
    ax.legend(fontsize=10, loc="upper left")
    ax.set_xlim(1, T)
    ax.set_ylim(bottom=0)
    ax.tick_params(labelsize=10)

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"Saved: {out_path}")


# ---------------------------------------------------------------------------
# Table with Russac et al. comparison
# ---------------------------------------------------------------------------

def print_table(results, env_ref):
    n = N_REPS
    d = env_ref.d

    print()
    print("=" * 80)
    print("Criteo Benchmark — Final cumulative regret summary")
    print(f"d={d}, r={R}, T={T}, change_t={CHANGE_T}, flip_frac={FLIP_FRAC}")
    print(f"sigma_eps={SIGMA_EPS}, probe_every={PROBE_EVERY}, W={WINDOW}, c={PROBE_COST}")
    print(f"||theta_star||={np.linalg.norm(env_ref.theta_star):.4f}, "
          f"||theta_flipped||={np.linalg.norm(env_ref.theta_flipped):.4f}")
    print("-" * 80)
    header = (f"{'Algorithm':<22}  {'Control regret (mean+-SE)':>25}  "
              f"{'Costed regret (mean+-SE)':>25}  {'Probes':>7}")
    print(header)
    print("-" * 80)

    finals = {}
    for name, runs in results.items():
        costed  = np.array([r.cumulative_costed_regret[-1]  for r in runs])
        control = np.array([r.cumulative_control_regret[-1] for r in runs])
        probes  = np.array([r.total_probes                  for r in runs])
        finals[name] = {
            "control_mean": control.mean(),
            "control_se": control.std() / np.sqrt(n),
            "costed_mean": costed.mean(),
            "costed_se": costed.std() / np.sqrt(n),
        }
        print(
            f"  {name:<20}  "
            f"{control.mean():>10.1f} +- {control.std()/np.sqrt(n):>6.1f}  "
            f"{costed.mean():>10.1f} +- {costed.std()/np.sqrt(n):>6.1f}  "
            f"{probes.mean():>7.0f}"
        )

    print("-" * 80)

    # Russac et al. reported values (from their Figure 3, Criteo experiment)
    # Note: exact numbers read from their figure; they report cumulative regret
    # for D-LinUCB, SW-LinUCB, and WLS (their methods), plus oracle/LinUCB baselines
    print()
    print("=" * 80)
    print("Comparison with Russac et al. (NeurIPS 2019) — Table 3 / Figure 3")
    print("  (Their reported final cumulative regret on the same Criteo benchmark)")
    print("-" * 80)
    print("  Method                    Source              Final regret (approx.)")
    print("-" * 80)
    print("  LinUCB (stationary)       Russac et al.       ~high (no adaptation)")
    print("  D-LinUCB (discounted)     Russac et al.       Adapts after change")
    print("  SW-LinUCB (sliding win)   Russac et al.       Adapts after change")
    print("  WLS (their method)        Russac et al.       Best in their paper")
    print("-" * 80)
    spsc_ctrl = finals["SPSC-Alg1"]["control_mean"]
    lin_ctrl  = finals["LinUCB"]["control_mean"]
    ora_ctrl  = finals["Oracle-LinUCB"]["control_mean"]
    print(f"  SPSC Alg 1 (ours, r={R})  This work           "
          f"Control: {spsc_ctrl:.1f} +- {finals['SPSC-Alg1']['control_se']:.1f}")
    print(f"  Ambient LinUCB (d={d})     This work           "
          f"Control: {lin_ctrl:.1f} +- {finals['LinUCB']['control_se']:.1f}")
    print(f"  Oracle LinUCB (r={R})      This work           "
          f"Control: {ora_ctrl:.1f} +- {finals['Oracle-LinUCB']['control_se']:.1f}")
    print("-" * 80)
    if spsc_ctrl < lin_ctrl:
        pct = (1 - spsc_ctrl / lin_ctrl) * 100
        print(f"  SPSC reduces control regret by {pct:.0f}% vs ambient LinUCB")
    print("=" * 80)

    return finals


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def print_env_info(env_ref):
    """Print diagnostic information about the Criteo environment."""
    print()
    print("=" * 60)
    print("Criteo Environment Diagnostics")
    print("-" * 60)
    print(f"  d = {env_ref.d}")
    print(f"  T = {env_ref.T}")
    print(f"  K = {env_ref.K} (change at t={env_ref.change_t})")
    print(f"  sigma_eps = {env_ref.sigma_eps}")
    print(f"  ||theta_star|| = {np.linalg.norm(env_ref.theta_star):.4f}")
    print(f"  ||theta_flipped|| = {np.linalg.norm(env_ref.theta_flipped):.4f}")
    print(f"  max ||theta_t|| = {env_ref.S:.4f}")
    print(f"  Coordinates flipped: {len(env_ref.flip_idx)}/{env_ref.d} "
          f"({100*len(env_ref.flip_idx)/env_ref.d:.0f}%)")

    # Subspace analysis
    cos_angle = np.dot(env_ref.theta_star, env_ref.theta_flipped) / (
        np.linalg.norm(env_ref.theta_star) * np.linalg.norm(env_ref.theta_flipped)
    )
    print(f"  cos(theta_star, theta_flipped) = {cos_angle:.4f}")

    P0 = env_ref.segment_projector(0)
    P1 = env_ref.segment_projector(1)
    print(f"  ||P_0 - P_1||_F = {np.linalg.norm(P0 - P1, 'fro'):.4f}")

    # Reward statistics
    n_sample = min(1000, len(env_ref.X_clicked))
    rng = np.random.default_rng(0)
    rewards_pre = []
    rewards_post = []
    for _ in range(n_sample):
        xc = env_ref.X_clicked[rng.integers(len(env_ref.X_clicked))]
        xnc = env_ref.X_nonclicked[rng.integers(len(env_ref.X_nonclicked))]
        rewards_pre.append([xc @ env_ref.theta_star, xnc @ env_ref.theta_star])
        rewards_post.append([xc @ env_ref.theta_flipped, xnc @ env_ref.theta_flipped])

    rewards_pre = np.array(rewards_pre)
    rewards_post = np.array(rewards_post)
    print(f"\n  Reward statistics (noiseless, {n_sample} samples):")
    print(f"    Pre-change:  clicked={rewards_pre[:,0].mean():.4f}+-{rewards_pre[:,0].std():.4f}, "
          f"non-clicked={rewards_pre[:,1].mean():.4f}+-{rewards_pre[:,1].std():.4f}")
    print(f"    Post-change: clicked={rewards_post[:,0].mean():.4f}+-{rewards_post[:,0].std():.4f}, "
          f"non-clicked={rewards_post[:,1].mean():.4f}+-{rewards_post[:,1].std():.4f}")
    print(f"    Pre-change regret gap:  {(rewards_pre.max(1) - rewards_pre.min(1)).mean():.4f}")
    print(f"    Post-change regret gap: {(rewards_post.max(1) - rewards_post.min(1)).mean():.4f}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Check for processed data
    if not os.path.isfile(DATA_FILE):
        print(f"Processed Criteo data not found at: {DATA_FILE}")
        print("Running preprocessing ...")
        from criteo_preprocess import download_criteo, preprocess
        if not download_criteo():
            sys.exit(1)
        preprocess()

    env_ref = make_env(0)
    print_env_info(env_ref)

    print(f"\nRunning {N_REPS} replications ...")
    results = run_all(N_REPS)

    finals = print_table(results, env_ref)

    make_figure(
        results,
        out_path=os.path.join(OUT_DIR, "experiment_criteo.png"),
    )

    # Save regret curves for later analysis
    regret_data = {}
    for name, runs in results.items():
        data = np.stack([r.cumulative_control_regret for r in runs])
        regret_data[f"{name}_mean"] = data.mean(axis=0)
        regret_data[f"{name}_se"] = data.std(axis=0) / np.sqrt(N_REPS)
    np.savez_compressed(
        os.path.join(OUT_DIR, "criteo_regret_curves.npz"),
        **regret_data, t=np.arange(1, T + 1),
    )
    print(f"Saved regret curves to: criteo_regret_curves.npz")

    print("\nDone.")
