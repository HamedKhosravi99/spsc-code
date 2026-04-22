"""
Focused: SPSC Alg.1 vs SPSC Adaptive — when does each win?

Sweep 1: d sweep — both beat LinUCB when d-r is large
Sweep 2: Oracle quality — false alarm boundaries degrade Alg.1
         (exactly as in sweep2.py). K_real=5 actual subspace changes;
         Alg.1 is given K_oracle evenly-spaced boundaries. When
         K_oracle > K_real, extras are false alarms → Alg.1 resets
         and starves; Adaptive (CUSUM) is unaffected.
"""

import os, sys, time, numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from environments import LowRankLDSEnvironment
from algorithm import SPSC_Algorithm1, SPSC_Adaptive, LinUCB

T = 5000
K = 10
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
N_SEEDS = 5


def make_env(d, r, K_val, seed):
    return LowRankLDSEnvironment(
        d=d, r=r, K=K_val, T=T,
        sigma_eps=SIGMA_EPS, spectral_radius=SPEC_RAD,
        n_actions=N_ACTIONS, sigma_eta=SIGMA_ETA, seed=seed * 100,
        piecewise_constant=True, feature_decay=FEATURE_DECAY)


def run_three(env_fn, seed):
    env1 = env_fn(seed)
    a1 = SPSC_Algorithm1(env1, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                         window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                         normalize_gamma_by_d=True).run()
    env2 = env_fn(seed)
    ad = SPSC_Adaptive(env2, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                       window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                       m_relearn=30, det_window=50, cusum_threshold=3.0,
                       warmup=100).run()
    env3 = env_fn(seed)
    li = LinUCB(env3, lam=LAM, delta=DELTA, seed=seed + 1000).run()

    return (a1.cumulative_costed_regret[-1],
            ad.cumulative_costed_regret[-1],
            li.cumulative_costed_regret[-1])


def print_header():
    print(f"  {'param':>8}  {'Alg.1':>10}  {'Adaptive':>10}  {'LinUCB':>10}  "
          f"{'A1/Lin':>8}  {'Ad/Lin':>8}  {'Ad/A1':>8}  {'Better':>12}")
    print("-" * 90)


def print_row(label, a1s, ads, lis):
    a1m, adm, lim = np.mean(a1s), np.mean(ads), np.mean(lis)
    better = "Alg.1" if a1m <= adm else "Adaptive"
    gap = abs(a1m - adm) / max(min(a1m, adm), 1) * 100
    print(f"  {label:>8}  {a1m:>10.0f}  {adm:>10.0f}  {lim:>10.0f}  "
          f"{a1m/max(lim,1):>8.3f}  {adm/max(lim,1):>8.3f}  "
          f"{adm/max(a1m,1):>8.3f}  {better:>8} ({gap:.1f}%)")


if __name__ == "__main__":
    print("=" * 90)
    print("SPSC Alg.1 vs Adaptive — When does each win?")
    print(f"T={T}, K={K}, pe={PROBE_EVERY}, c={PROBE_COST}, W={WINDOW}, fd={FEATURE_DECAY}")
    print(f"Seeds: {N_SEEDS}")
    print("=" * 90)

    # =================================================================
    # Sweep 1: d sweep — where does SPSC win over LinUCB?
    # =================================================================
    D_SWEEP = [10, 20, 30, 50, 60, 80, 100]
    R_FIXED = 5

    print(f"\n{'=' * 90}")
    print(f"  SWEEP 1: d sweep (r={R_FIXED}, K={K}) — all boundaries are real changes")
    print(f"  Alg.1 has oracle change points → always slightly better")
    print(f"{'=' * 90}")
    print_header()

    sweep1_results = {}
    for d in D_SWEEP:
        a1s, ads, lis = [], [], []
        for seed in range(N_SEEDS):
            a1, ad, li = run_three(lambda s: make_env(d, R_FIXED, K, s), seed)
            a1s.append(a1); ads.append(ad); lis.append(li)
        sweep1_results[f"d={d}"] = {"SPSC-Alg1": a1s, "SPSC-Adaptive": ads, "LinUCB": lis}
        print_row(f"d={d}", a1s, ads, lis)
    print("=" * 90)
    sys.stdout.flush()

    # =================================================================
    # Sweep 2: Oracle quality — false alarm boundaries (exactly as in sweep2.py)
    # =================================================================
    # K_real=5 actual subspace changes. Alg.1 is given K_oracle evenly-spaced
    # boundaries. When K_oracle > K_real, extras are false alarms:
    #   - Alg.1 resets at every boundary → discards data, restarts with few
    #     probes → gamma_t huge → near-random action selection
    #   - Adaptive ignores oracle, uses CUSUM → unaffected by false alarms
    SWEEP2_K_REAL = 5
    SWEEP2_D = 60
    SWEEP2_R = 5
    SWEEP2_N_SEEDS = 10
    K_ORACLE_SWEEP = [5, 10, 15, 20, 30, 50]

    def make_sweep2_env(seed):
        return LowRankLDSEnvironment(
            d=SWEEP2_D, r=SWEEP2_R, K=SWEEP2_K_REAL, T=T,
            sigma_eps=SIGMA_EPS, spectral_radius=SPEC_RAD,
            n_actions=N_ACTIONS, sigma_eta=SIGMA_ETA, seed=seed * 100,
            piecewise_constant=True, feature_decay=FEATURE_DECAY)

    def add_false_boundaries(env, K_oracle):
        """Replace seg_of/tau with K_oracle evenly-spaced boundaries."""
        if K_oracle == SWEEP2_K_REAL:
            return
        real_seg_len = T // SWEEP2_K_REAL
        oracle_seg_len = T // K_oracle
        new_seg_of = np.minimum(np.arange(T) // oracle_seg_len, K_oracle - 1).astype(int)
        new_tau = np.array([i * oracle_seg_len for i in range(K_oracle)])
        new_B_list = []
        for k in range(K_oracle):
            t_mid = new_tau[k] + oracle_seg_len // 2
            real_k = min(t_mid // real_seg_len, SWEEP2_K_REAL - 1)
            new_B_list.append(env.B_list[real_k])
        env.seg_of = new_seg_of
        env.tau = new_tau
        env.K = K_oracle
        env.B_list = new_B_list

    def run_sweep2(K_oracle, seed):
        env1 = make_sweep2_env(seed)
        add_false_boundaries(env1, K_oracle)
        a1 = SPSC_Algorithm1(env1, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                             window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                             normalize_gamma_by_d=True).run()
        env2 = make_sweep2_env(seed)
        ad = SPSC_Adaptive(env2, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                           window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                           m_relearn=30, det_window=50, cusum_threshold=3.0,
                           warmup=100).run()
        env3 = make_sweep2_env(seed)
        li = LinUCB(env3, lam=LAM, delta=DELTA, seed=seed + 1000).run()
        return (a1.cumulative_costed_regret[-1],
                ad.cumulative_costed_regret[-1],
                li.cumulative_costed_regret[-1])

    print(f"\n{'=' * 90}")
    print(f"  SWEEP 2: Oracle quality (d={SWEEP2_D}, r={SWEEP2_R}, "
          f"K_real={SWEEP2_K_REAL}, T={T})")
    print(f"  K_oracle = boundaries Alg.1 sees ({SWEEP2_K_REAL} real + false alarms)")
    print(f"  K_oracle={SWEEP2_K_REAL}: correct oracle → Alg.1 advantage")
    print(f"  K_oracle>>{SWEEP2_K_REAL}: too many resets → Alg.1 data-starved → Adaptive wins")
    print(f"  Seeds: {SWEEP2_N_SEEDS}")
    print(f"{'=' * 90}")
    print(f"  {'K_oracle':>8}  {'seg_len':>8}  {'Alg.1':>10}  {'Adaptive':>10}  "
          f"{'LinUCB':>10}  {'A1/Lin':>8}  {'Ad/Lin':>8}  {'Ad/A1':>8}  {'Better':>12}")
    print("-" * 90)

    sweep2_results = {}
    for K_oracle in K_ORACLE_SWEEP:
        a1s, ads, lis = [], [], []
        for seed in range(SWEEP2_N_SEEDS):
            a1, ad, li = run_sweep2(K_oracle, seed)
            a1s.append(a1); ads.append(ad); lis.append(li)
        sweep2_results[f"K_oracle={K_oracle}"] = {
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
                 config={"T": T, "K": K, "SIGMA_EPS": SIGMA_EPS, "SPEC_RAD": SPEC_RAD,
                         "SIGMA_ETA": SIGMA_ETA, "N_ACTIONS": N_ACTIONS,
                         "PROBE_EVERY": PROBE_EVERY, "PROBE_COST": PROBE_COST,
                         "WINDOW": WINDOW, "LAM": LAM, "DELTA": DELTA,
                         "FEATURE_DECAY": FEATURE_DECAY,
                         "SWEEP1_N_SEEDS": N_SEEDS, "D_SWEEP": D_SWEEP, "R_FIXED": R_FIXED,
                         "SWEEP2_N_SEEDS": SWEEP2_N_SEEDS, "SWEEP2_K_REAL": SWEEP2_K_REAL,
                         "SWEEP2_D": SWEEP2_D, "SWEEP2_R": SWEEP2_R,
                         "K_ORACLE_SWEEP": K_ORACLE_SWEEP},
                 results={"sweep1_d": sweep1_results, "sweep2_oracle_quality": sweep2_results})
    print("\nDone.")
