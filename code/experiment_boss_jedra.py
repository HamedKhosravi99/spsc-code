"""
BOSS vs Jedra vs SPSC on non-stationary synthetic environment.

Shows that recent low-rank methods (BOSS, Jedra) assume stationary subspace
and fail when subspaces change. SPSC detects/uses change points to adapt.

d=60, r=5, K=10 segments, T=5000, 10 seeds.
"""

import os, sys, time, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from environments import LowRankLDSEnvironment
from algorithm import SPSC_Algorithm1, SPSC_Adaptive, BOSSAdapted, JedraAdapted

N_SEEDS = 10
T = 5000; K = 10; D = 60; R = 5
SIGMA_EPS = 0.3; SPEC_RAD = 0.99; SIGMA_ETA = 0.04
N_ACTIONS = 40; PROBE_EVERY = 50; PROBE_COST = 0.1
WINDOW = 400; LAM = 0.01; DELTA = 0.05; FEATURE_DECAY = 1.5

METHOD_NAMES = ["SPSC-Alg1", "SPSC-Adaptive", "BOSS-adapted", "Jedra-adapted"]

def make_env(seed):
    return LowRankLDSEnvironment(
        d=D, r=R, K=K, T=T, sigma_eps=SIGMA_EPS, spectral_radius=SPEC_RAD,
        n_actions=N_ACTIONS, sigma_eta=SIGMA_ETA, seed=seed * 100,
        piecewise_constant=True, feature_decay=FEATURE_DECAY)

def run_all(seed):
    results = {}
    env = make_env(seed)
    m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                        window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                        normalize_gamma_by_d=True).run()
    results["SPSC-Alg1"] = m.cumulative_costed_regret[-1]

    env = make_env(seed)
    m = SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                      window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                      m_relearn=30, det_window=50, cusum_threshold=3.0,
                      warmup=100).run()
    results["SPSC-Adaptive"] = m.cumulative_costed_regret[-1]

    env = make_env(seed)
    m = BOSSAdapted(env, m_explore=200, lam=LAM, delta=DELTA, seed=seed + 11000).run()
    results["BOSS-adapted"] = m.cumulative_control_regret[-1]

    env = make_env(seed)
    m = JedraAdapted(env, m_explore=200, lam=LAM, delta=DELTA, seed=seed + 12000).run()
    results["Jedra-adapted"] = m.cumulative_control_regret[-1]

    return results

if __name__ == "__main__":
    print("=" * 80)
    print(f"BOSS & Jedra (adapted) vs SPSC — Non-stationary subspaces")
    print(f"d={D}, r={R}, K={K}, T={T}, {N_SEEDS} seeds")
    print(f"BOSS/Jedra learn subspace ONCE in first 200 steps, then fix it.")
    print(f"SPSC re-learns subspace at change points → adapts to new subspaces.")
    print("=" * 80)

    all_res = {m: [] for m in METHOD_NAMES}
    for seed in range(N_SEEDS):
        t0 = time.time()
        res = run_all(seed)
        for m in METHOD_NAMES:
            all_res[m].append(res[m])
        print(f"  seed {seed+1}/{N_SEEDS}:  " +
              "  ".join(f"{m}={res[m]:.0f}" for m in METHOD_NAMES) +
              f"  [{time.time()-t0:.1f}s]", flush=True)

    print("\n" + "=" * 80)
    print(f"  {'Method':<20}  {'Mean':>8}  {'SE':>8}  {'vs SPSC-Alg1':>14}")
    print("-" * 60)
    a1_mean = np.mean(all_res["SPSC-Alg1"])
    for m in METHOD_NAMES:
        arr = np.array(all_res[m])
        ratio = arr.mean() / max(a1_mean, 1e-8)
        print(f"  {m:<20}  {arr.mean():>8.0f}  {arr.std()/np.sqrt(N_SEEDS):>8.0f}  {ratio:>14.3f}")
    print("=" * 80)

    from results_io import save_results
    save_results(__file__,
                 config={"N_SEEDS": N_SEEDS, "T": T, "K": K, "D": D, "R": R,
                         "SIGMA_EPS": SIGMA_EPS, "SPEC_RAD": SPEC_RAD, "SIGMA_ETA": SIGMA_ETA,
                         "N_ACTIONS": N_ACTIONS, "PROBE_EVERY": PROBE_EVERY, "PROBE_COST": PROBE_COST,
                         "WINDOW": WINDOW, "LAM": LAM, "DELTA": DELTA,
                         "FEATURE_DECAY": FEATURE_DECAY, "METHOD_NAMES": METHOD_NAMES},
                 results=all_res)
    print("\nDone.")
