"""
Sweep 2: Oracle quality — false alarm boundaries degrade Alg.1.

K_real=5 actual subspace changes. Alg.1 is given K_oracle evenly-spaced
boundaries. When K_oracle > K_real, the extra boundaries are false alarms:
  - Alg.1 resets at every boundary → discards data, restarts with few probes
    → gamma_t huge → near-random action selection
  - Adaptive ignores oracle, uses CUSUM → unaffected by false alarms
"""

import os, sys, numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from environments import LowRankLDSEnvironment
from algorithm import SPSC_Algorithm1, SPSC_Adaptive, LinUCB

T = 5000
K_REAL = 5
D = 60
R = 5
SIGMA_EPS = 0.3
SPEC_RAD = 0.99
SIGMA_ETA = 0.04
N_ACTIONS = 40
PROBE_EVERY = 50
PROBE_COST = 0.1
WINDOW = 400
LAM = 0.01
DELTA = 0.05
FEATURE_DECAY = 1.5
N_SEEDS = 10

K_ORACLE_SWEEP = [5, 10, 15, 20, 30, 50]


def make_env(seed):
    return LowRankLDSEnvironment(
        d=D, r=R, K=K_REAL, T=T,
        sigma_eps=SIGMA_EPS, spectral_radius=SPEC_RAD,
        n_actions=N_ACTIONS, sigma_eta=SIGMA_ETA, seed=seed * 100,
        piecewise_constant=True, feature_decay=FEATURE_DECAY)


def add_false_boundaries(env, K_oracle):
    """Replace seg_of/tau with K_oracle evenly-spaced boundaries."""
    if K_oracle == K_REAL:
        return

    real_seg_len = T // K_REAL
    oracle_seg_len = T // K_oracle
    new_seg_of = np.minimum(np.arange(T) // oracle_seg_len, K_oracle - 1).astype(int)
    new_tau = np.array([i * oracle_seg_len for i in range(K_oracle)])

    new_B_list = []
    for k in range(K_oracle):
        t_mid = new_tau[k] + oracle_seg_len // 2
        real_k = min(t_mid // real_seg_len, K_REAL - 1)
        new_B_list.append(env.B_list[real_k])

    env.seg_of = new_seg_of
    env.tau = new_tau
    env.K = K_oracle
    env.B_list = new_B_list


def run_three(K_oracle, seed):
    env1 = make_env(seed)
    add_false_boundaries(env1, K_oracle)
    a1 = SPSC_Algorithm1(env1, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                         window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                         normalize_gamma_by_d=True).run()

    env2 = make_env(seed)
    ad = SPSC_Adaptive(env2, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                       window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                       m_relearn=30, det_window=50, cusum_threshold=3.0,
                       warmup=100).run()

    env3 = make_env(seed)
    li = LinUCB(env3, lam=LAM, delta=DELTA, seed=seed + 1000).run()

    return (a1.cumulative_costed_regret[-1],
            ad.cumulative_costed_regret[-1],
            li.cumulative_costed_regret[-1])


if __name__ == "__main__":
    print("=" * 90)
    print(f"Sweep 2: Oracle quality (d={D}, r={R}, K_real={K_REAL}, T={T})")
    print(f"  K_oracle = boundaries Alg.1 sees ({K_REAL} real + false alarms)")
    print(f"  K_oracle={K_REAL}: correct oracle → Alg.1 advantage")
    print(f"  K_oracle>>{K_REAL}: too many resets → Alg.1 data-starved → Adaptive wins")
    print(f"  Seeds: {N_SEEDS}")
    print("=" * 90)
    print(f"  {'K_oracle':>8}  {'seg_len':>8}  {'Alg.1':>10}  {'Adaptive':>10}  "
          f"{'LinUCB':>10}  {'A1/Lin':>8}  {'Ad/Lin':>8}  {'Ad/A1':>8}  {'Better':>12}")
    print("-" * 90)

    all_results = {}
    for K_oracle in K_ORACLE_SWEEP:
        a1s, ads, lis = [], [], []
        for seed in range(N_SEEDS):
            a1, ad, li = run_three(K_oracle, seed)
            a1s.append(a1); ads.append(ad); lis.append(li)

        all_results[f"K_oracle={K_oracle}"] = {
            "SPSC-Alg1": a1s, "SPSC-Adaptive": ads, "LinUCB": lis}

        a1m, adm, lim = np.mean(a1s), np.mean(ads), np.mean(lis)
        seg_len = T // K_oracle
        better = "Alg.1" if a1m <= adm else "Adaptive"
        gap = abs(a1m - adm) / max(min(a1m, adm), 1) * 100
        print(f"  {K_oracle:>8}  {seg_len:>8}  {a1m:>10.0f}  {adm:>10.0f}  "
              f"{lim:>10.0f}  {a1m/max(lim,1):>8.3f}  {adm/max(lim,1):>8.3f}  "
              f"{adm/max(a1m,1):>8.3f}  {better:>8} ({gap:.1f}%)")

    print("=" * 90)

    from results_io import save_results
    save_results(__file__,
                 config={"T": T, "K_REAL": K_REAL, "D": D, "R": R,
                         "SIGMA_EPS": SIGMA_EPS, "SPEC_RAD": SPEC_RAD, "SIGMA_ETA": SIGMA_ETA,
                         "N_ACTIONS": N_ACTIONS, "PROBE_EVERY": PROBE_EVERY, "PROBE_COST": PROBE_COST,
                         "WINDOW": WINDOW, "LAM": LAM, "DELTA": DELTA,
                         "FEATURE_DECAY": FEATURE_DECAY, "N_SEEDS": N_SEEDS,
                         "K_ORACLE_SWEEP": K_ORACLE_SWEEP},
                 results=all_results)
    print("\nDone.")
