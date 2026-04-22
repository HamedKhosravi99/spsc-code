"""
Ablation: Why does SPSC win on Warfarin despite high subspace error?

Three controls isolate the source of the benefit:
  1. SPSC (learned subspace via probing)
  2. RandomSubspace-UCB: fixed random r-dim subspace, NO probing, same windowed ridge UCB
  3. LinUCB (ambient d=93)
  4. Oracle (true subspace, performance ceiling)

If RandomSubspace-UCB also beats LinUCB → benefit is mainly dimensionality reduction.
If RandomSubspace-UCB loses → learned subspace captures meaningful structure.

Also reports:
  - Signal variance retained: tr(P_hat M_tilde P_hat) / tr(M_tilde)
    for both learned and random subspaces.

Setup matches paper: d=93, K=8, T=5000, 10 seeds, r in {1,2,3,5,10}.
"""

import os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import WarfarinEnvironment
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB, RunMetrics, RandomSubspaceUCB

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Signal variance retained: tr(P_hat @ M_tilde @ P_hat) / tr(M_tilde)
# ---------------------------------------------------------------------------

def signal_variance_retained(env, P_hat, k):
    """
    Fraction of signal energy captured by projector P_hat in segment k.
    M_tilde = E[theta_t theta_t^T] ≈ theta_k theta_k^T (constant within segment).
    Returns tr(P M P) / tr(M).
    """
    s = env.tau[k]
    theta_k = env.theta[s]
    M = np.outer(theta_k, theta_k)
    tr_M = np.trace(M)
    if tr_M < 1e-12:
        return 0.0
    PMP = P_hat @ M @ P_hat
    return float(np.trace(PMP) / tr_M)


# ---------------------------------------------------------------------------
# Run one (r) cell
# ---------------------------------------------------------------------------

ALGO_NAMES = ["SPSC", "RandomSub", "Oracle", "LinUCB"]

def run_cell(r, n_seeds):
    env_kwargs = dict(d=93, K=8, T=5000, n_actions=40, sigma_eps=0.3)
    results = {n: [] for n in ALGO_NAMES}
    svr_spsc = []    # signal variance retained per seed (averaged over segments)
    svr_random = []

    for seed in range(n_seeds):
        print(f"  r={r}, seed {seed+1}/{n_seeds}", end="\r", flush=True)

        for name in ALGO_NAMES:
            kw = {**env_kwargs, "r": r, "seed": seed * 13 + 7}
            env = WarfarinEnvironment(**kw)

            if name == "SPSC":
                alg = SPSC_Algorithm1(env, probe_every=10, probe_cost=0.1,
                                      window=200, lam=1.0, delta=0.05,
                                      seed=seed, normalize_gamma_by_d=True)
                m = alg.run()

                # Compute signal variance retained for learned subspace
                seg_svr = []
                for k in range(env.K):
                    # Get the subspace at end of segment
                    # Use the last probe-round subspace error to find P_hat
                    seg_start = env.tau[k]
                    seg_end = seg_start + env.segment_lengths[k]
                    probe_idx = np.where(m.probe_flags[seg_start:seg_end])[0]
                    if len(probe_idx) > 0:
                        last_probe = seg_start + probe_idx[-1]
                        # Reconstruct P_hat from the subspace error
                        # We need to re-derive U_hat... Instead, run a second
                        # pass just for the metric.
                        pass
                    seg_svr.append(np.nan)
                # We'll compute SVR differently below

            elif name == "RandomSub":
                m = RandomSubspaceUCB(env, window=200, lam=1.0, delta=0.05,
                                       seed=seed).run()

            elif name == "Oracle":
                m = OracleLinUCB(env, window=10000, lam=1.0, delta=0.05,
                                  seed=seed + 1000).run()

            elif name == "LinUCB":
                m = LinUCB(env, lam=1.0, delta=0.05, seed=seed + 5000).run()

            results[name].append(m)

        # --- Signal variance retained (separate pass for clean measurement) ---
        kw = {**env_kwargs, "r": r, "seed": seed * 13 + 7}

        # SPSC learned subspace SVR
        env_spsc = WarfarinEnvironment(**kw)
        alg = SPSC_Algorithm1(env_spsc, probe_every=10, probe_cost=0.1,
                               window=200, lam=1.0, delta=0.05,
                               seed=seed, normalize_gamma_by_d=True)
        # Re-run to track the subspace
        d = env_spsc.d
        from algorithm import K_inverse
        M_sum = np.zeros((d, d))
        m_probe = 0
        rng_p = np.random.default_rng(seed)
        seg_svr_spsc = []
        current_k = -1
        for t in range(env_spsc.T):
            k = env_spsc.seg_of[t]
            if k != current_k:
                if current_k >= 0 and m_probe > 0:
                    M_hat = M_sum / m_probe
                    eig_vals, eig_vecs = np.linalg.eigh(M_hat)
                    U_hat = eig_vecs[:, -r:]
                    P_hat = U_hat @ U_hat.T
                    seg_svr_spsc.append(signal_variance_retained(env_spsc, P_hat, current_k))
                M_sum = np.zeros((d, d))
                m_probe = 0
                current_k = k
            seg_start = env_spsc.tau[k]
            if t == seg_start or ((t - seg_start) % 10 == 0):
                z = rng_p.standard_normal(d)
                u_t = np.sqrt(d) * z / (np.linalg.norm(z) + 1e-12)
                y_t = env_spsc.step(u_t, t)
                s_t = y_t**2 - env_spsc.sigma_eps**2
                G_t = K_inverse(s_t * np.outer(u_t, u_t), d)
                M_sum += G_t
                m_probe += 1
        # Last segment
        if m_probe > 0:
            M_hat = M_sum / m_probe
            eig_vals, eig_vecs = np.linalg.eigh(M_hat)
            U_hat = eig_vecs[:, -r:]
            P_hat = U_hat @ U_hat.T
            seg_svr_spsc.append(signal_variance_retained(env_spsc, P_hat, current_k))
        svr_spsc.append(np.nanmean(seg_svr_spsc) if seg_svr_spsc else np.nan)

        # Random subspace SVR
        env_rand = WarfarinEnvironment(**kw)
        rng_r = np.random.default_rng(seed)
        seg_svr_rand = []
        for k in range(env_rand.K):
            Z = rng_r.standard_normal((env_rand.d, r))
            U_rand, _ = np.linalg.qr(Z)
            U_rand = U_rand[:, :r]
            P_rand = U_rand @ U_rand.T
            seg_svr_rand.append(signal_variance_retained(env_rand, P_rand, k))
        svr_random.append(np.mean(seg_svr_rand))

    print(flush=True)
    return results, np.array(svr_spsc), np.array(svr_random)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

N_SEEDS = 10
R_VALUES = [1, 2, 3, 5, 10]

if __name__ == "__main__":
    all_results = {}
    all_svr_spsc = {}
    all_svr_random = {}

    print("=" * 80)
    print("  Ablation: Random Subspace vs Learned Subspace on Warfarin (d=93)")
    print("=" * 80)

    for r in R_VALUES:
        results, svr_s, svr_r = run_cell(r, N_SEEDS)
        all_results[r] = results
        all_svr_spsc[r] = svr_s
        all_svr_random[r] = svr_r

    # -----------------------------------------------------------------------
    # Print results table
    # -----------------------------------------------------------------------
    print("\n" + "=" * 100)
    print(f"  {'r':>3}  {'SPSC':>12}  {'RandomSub':>12}  {'LinUCB':>12}  "
          f"{'Oracle':>12}  {'SPSC/Lin':>9}  {'Rand/Lin':>9}  "
          f"{'SVR(SPSC)':>10}  {'SVR(Rand)':>10}")
    print("  " + "-" * 96)

    for r in R_VALUES:
        res = all_results[r]
        vals = {}
        for name in ALGO_NAMES:
            finals = np.array([m.cumulative_control_regret[-1] for m in res[name]])
            vals[name] = (finals.mean(), finals.std() / np.sqrt(len(finals)))

        spsc_m, spsc_se = vals["SPSC"]
        rand_m, rand_se = vals["RandomSub"]
        lin_m, lin_se = vals["LinUCB"]
        orc_m, orc_se = vals["Oracle"]
        svr_s = all_svr_spsc[r]
        svr_r = all_svr_random[r]

        print(f"  {r:>3}  "
              f"{spsc_m:>8.0f}±{spsc_se:>3.0f}  "
              f"{rand_m:>8.0f}±{rand_se:>3.0f}  "
              f"{lin_m:>8.0f}±{lin_se:>3.0f}  "
              f"{orc_m:>8.0f}±{orc_se:>3.0f}  "
              f"{spsc_m/lin_m:>9.3f}  "
              f"{rand_m/lin_m:>9.3f}  "
              f"{np.nanmean(svr_s):>10.3f}  "
              f"{np.mean(svr_r):>10.3f}")

    print("=" * 100)

    # -----------------------------------------------------------------------
    # Figure: 3-panel
    # -----------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Panel (a): Regret comparison
    ax = axes[0]
    for name, color, marker, ls in [
        ("SPSC", "#1f77b4", "o", "-"),
        ("RandomSub", "#ff7f0e", "s", "--"),
        ("LinUCB", "#d62728", "^", ":"),
        ("Oracle", "#2ca02c", "D", "-.")
    ]:
        means, ses = [], []
        for r in R_VALUES:
            finals = np.array([m.cumulative_control_regret[-1]
                               for m in all_results[r][name]])
            means.append(finals.mean())
            ses.append(finals.std() / np.sqrt(len(finals)))
        ax.errorbar(R_VALUES, means, yerr=ses, fmt=f"{marker}{ls}",
                     lw=2, markersize=7, capsize=3, label=name, color=color)
    ax.set_xlabel("Rank $r$", fontsize=11)
    ax.set_ylabel("Cumulative Control Regret", fontsize=11)
    ax.set_title("(a) Absolute regret", fontsize=11)
    ax.legend(fontsize=9)
    ax.set_xticks(R_VALUES)

    # Panel (b): Ratio to LinUCB
    ax = axes[1]
    for name, color, marker, ls, label in [
        ("SPSC", "#1f77b4", "o", "-", "SPSC / LinUCB"),
        ("RandomSub", "#ff7f0e", "s", "--", "RandomSub / LinUCB"),
    ]:
        ratios = []
        for r in R_VALUES:
            s_finals = np.array([m.cumulative_control_regret[-1]
                                  for m in all_results[r][name]])
            l_finals = np.array([m.cumulative_control_regret[-1]
                                  for m in all_results[r]["LinUCB"]])
            ratios.append(s_finals.mean() / l_finals.mean())
        ax.plot(R_VALUES, ratios, f"{marker}{ls}", lw=2.5, markersize=8,
                color=color, label=label)
    ax.axhline(1.0, color="gray", ls=":", lw=1)
    ax.fill_between(R_VALUES, [0]*len(R_VALUES), [1]*len(R_VALUES),
                     alpha=0.06, color="blue")
    ax.set_xlabel("Rank $r$", fontsize=11)
    ax.set_ylabel("Regret ratio vs LinUCB", fontsize=11)
    ax.set_title("(b) Ratio to LinUCB", fontsize=11)
    ax.legend(fontsize=9)
    ax.set_xticks(R_VALUES)
    ax.set_ylim(0.4, 1.6)

    # Panel (c): Signal variance retained
    ax = axes[2]
    svr_spsc_means = [np.nanmean(all_svr_spsc[r]) for r in R_VALUES]
    svr_spsc_ses = [np.nanstd(all_svr_spsc[r]) / np.sqrt(N_SEEDS) for r in R_VALUES]
    svr_rand_means = [np.mean(all_svr_random[r]) for r in R_VALUES]
    svr_rand_ses = [np.std(all_svr_random[r]) / np.sqrt(N_SEEDS) for r in R_VALUES]

    ax.errorbar(R_VALUES, svr_spsc_means, yerr=svr_spsc_ses,
                fmt="o-", lw=2, markersize=7, capsize=3,
                color="#1f77b4", label="Learned (SPSC)")
    ax.errorbar(R_VALUES, svr_rand_means, yerr=svr_rand_ses,
                fmt="s--", lw=2, markersize=7, capsize=3,
                color="#ff7f0e", label="Random subspace")
    ax.set_xlabel("Rank $r$", fontsize=11)
    ax.set_ylabel("$\\mathrm{tr}(\\hat{P} M \\hat{P}) \\,/\\, \\mathrm{tr}(M)$",
                   fontsize=11)
    ax.set_title("(c) Signal variance retained", fontsize=11)
    ax.legend(fontsize=9)
    ax.set_xticks(R_VALUES)
    ax.set_ylim(0, 1.05)

    fig.suptitle("Warfarin Ablation: Learned vs Random Subspace  |  "
                 "$d{=}93$, $K{=}8$, $T{=}5{,}000$, 10 seeds",
                 fontsize=12, y=1.02)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, "ablation_warfarin_random_subspace.png")
    plt.savefig(out, bbox_inches="tight", dpi=150)
    print(f"\nSaved: {out}")
    print("Done!")
