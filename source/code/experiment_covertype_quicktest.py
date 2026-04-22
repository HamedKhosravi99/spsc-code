"""
Covertype quick test: d=75, r=2, 3 seeds, all 10 methods.
Uses Satimage winning params. Should show clear SPSC win at high d.
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")

from environments import CovtypeEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, OracleLinUCB,
    SWLinUCB, RestartLinUCB, LowRankRewardUCB, LowOFUL, VOFUL,
)

N_SEEDS     = 3
R           = 2
K           = 10
T           = 5000
PROBE_EVERY = 10
PROBE_COST  = 0.02
WINDOW      = 400
LAM         = 0.01
DELTA       = 0.05

METHOD_NAMES = [
    "Oracle-LinUCB", "SPSC-Alg1", "SPSC-Adaptive",
    "LowOFUL", "VOFUL", "LowRank-Reward",
    "SW-LinUCB", "D-LinUCB", "Restart-LinUCB", "LinUCB",
]

COMPETITORS = ["LinUCB", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB",
               "LowRank-Reward", "LowOFUL", "VOFUL"]


def make_env(seed, d):
    return CovtypeEnvironment(
        d=d, r=R, K=K, T=T, sigma_eps=0.3, spectral_radius=0.99,
        n_actions=40, seed=seed * 13 + 7, sigma_eta=0.04,
    )


def run_cell(d):
    results = {m: [] for m in METHOD_NAMES}
    for seed in range(N_SEEDS):
        print(f"    seed {seed+1}/{N_SEEDS}", flush=True)

        env = make_env(seed, d)
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
        results["SPSC-Alg1"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d)
        m = SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                          window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                          m_relearn=30, det_window=50, cusum_threshold=3.0,
                          warmup=100).run()
        results["SPSC-Adaptive"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000).run()
        results["LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d)
        m = OracleLinUCB(env, window=10000, lam=LAM, delta=DELTA,
                         seed=seed + 2000).run()
        results["Oracle-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 3000,
                   forgetting_factor=0.998).run()
        results["D-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d)
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                     seed=seed + 4000).run()
        results["SW-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d)
        m = RestartLinUCB(env, restart_period=T // K,
                          lam=LAM, delta=DELTA, seed=seed + 5000).run()
        results["Restart-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d)
        m = LowRankRewardUCB(env, window=WINDOW, pca_warmup=50,
                              lam=LAM, delta=DELTA, seed=seed + 6000).run()
        results["LowRank-Reward"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d)
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 7000,
                     pca_warmup=30, subspace_update_freq=20).run()
        results["LowOFUL"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d)
        m = VOFUL(env, lam=LAM, delta=DELTA, seed=seed + 8000,
                  pca_warmup=30, subspace_update_freq=20).run()
        results["VOFUL"].append(m.cumulative_control_regret[-1])

    return {m: np.array(results[m]) for m in METHOD_NAMES}


def print_table(res, d):
    n = N_SEEDS
    lin_mean = res["LinUCB"].mean()
    best_comp_mean = min(res[m].mean() for m in COMPETITORS)
    best_method = min(COMPETITORS, key=lambda m: res[m].mean())

    print()
    print("=" * 110)
    print(f"  Covertype QUICK TEST  d={d}, r={R}, K={K}, T={T}  ({n} seeds)")
    print(f"  lam={LAM}, probe_every={PROBE_EVERY}, window={WINDOW}, c={PROBE_COST}")
    print("-" * 110)
    print(f"  {'Method':<30}  {'Mean':>8}  {'SE':>8}  {'vs LinUCB':>10}  {'vs Best':>10}  {'Note':>12}")
    print("-" * 110)

    for method in METHOD_NAMES:
        arr = res[method]
        mean = arr.mean()
        se = arr.std() / np.sqrt(n)
        vs_lin = (mean / max(lin_mean, 1e-8) - 1) * 100
        vs_best = (mean / max(best_comp_mean, 1e-8) - 1) * 100

        if method in ("SPSC-Alg1", "SPSC-Adaptive"):
            tag = "<<< WINS" if mean < best_comp_mean else ""
        elif method == "Oracle-LinUCB":
            tag = "(oracle)"
        else:
            tag = "* best" if method == best_method else ""

        print(f"  {METHOD_LABELS[method]:<30}  {mean:>8.0f}  {se:>8.0f}  "
              f"{vs_lin:>+10.1f}%  {vs_best:>+10.1f}%  {tag:>12}")
    print("=" * 110)
    sys.stdout.flush()


METHOD_LABELS = {
    "Oracle-LinUCB":    "Oracle LinUCB",
    "SPSC-Alg1":        "SPSC Alg.1 (ours)",
    "SPSC-Adaptive":    "SPSC Adaptive (ours)",
    "LowOFUL":          "LowOFUL (Jun+ '19)",
    "VOFUL":            "VOFUL (Kim+ '22)",
    "LowRank-Reward":   "LowRank-Reward",
    "SW-LinUCB":        "SW-LinUCB (Cheung+ '19)",
    "D-LinUCB":         "D-LinUCB (Russac+ '19)",
    "Restart-LinUCB":   "Restart-LinUCB",
    "LinUCB":           "LinUCB (Abbasi+ '11)",
}


if __name__ == "__main__":
    d = 75
    print(f"Covertype QUICK TEST: d={d}, r={R}, K={K}, T={T}, 3 seeds")
    print(f"  lam={LAM}, probe_every={PROBE_EVERY}, window={WINDOW}, c={PROBE_COST}")
    print()

    t0 = time.time()
    res = run_cell(d)
    elapsed = time.time() - t0

    print_table(res, d)
    print(f"\nTotal time: {elapsed:.1f}s")
