"""
Action-set-size ablation (revision W11) on Satimage.

The paper draws |A_t| = 40 actions per round from the active segment's class
pool. Reviewers may ask whether SPSC's win depends on this specific choice.
We sweep |A_t| in {20, 40, 80, 160} at the (d=105, r=10) cell.

Output: exps/results/experiment_action_set_size.json

Run time: ~20-40 min on 16 cores (4 sizes x 10 seeds x 5 methods).
"""

import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from environments import RealSatimageEnvironment
from algorithm import SPSC_Algorithm1, SPSC_Adaptive, LinUCB, SWLinUCB, LowOFUL
from results_io import save_results

N_SEEDS = 10
D, R = 105, 10
SEGMENT_SIZE, N_SEGMENTS = 500, 10
WINDOW, LAM, DELTA = 400, 0.01, 0.05
PROBE_EVERY, PROBE_COST = 50, 0.1
ACTION_SIZES = [20, 40, 80, 160]

METHODS = ["SPSC-Alg1", "SPSC-Adaptive", "LinUCB", "SW-LinUCB", "LowOFUL"]


def make_env(seed, n_actions):
    return RealSatimageEnvironment(
        d=D, r=R, n_actions=n_actions,
        segment_size=SEGMENT_SIZE, n_segments=N_SEGMENTS,
        seed=seed * 13 + 7,
    )


def run_method(name, env, seed):
    if name == "SPSC-Alg1":
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
        return float(m.cumulative_costed_regret[-1])
    if name == "SPSC-Adaptive":
        m = SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                          window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                          m_relearn=30, det_window=50, cusum_threshold=3.0,
                          warmup=100).run()
        return float(m.cumulative_costed_regret[-1])
    if name == "LinUCB":
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 2000).run()
    elif name == "SW-LinUCB":
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA, seed=seed + 3000).run()
    elif name == "LowOFUL":
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 5000).run()
    else:
        raise ValueError(name)
    return float(m.cumulative_control_regret[-1])


def run_cell(n_actions):
    print(f"\n[|A| = {n_actions}]")
    t0 = time.time()
    res = {m: [] for m in METHODS}
    for s in range(N_SEEDS):
        for m in METHODS:
            env = make_env(s, n_actions)
            res[m].append(run_method(m, env, s))
    for m in METHODS:
        arr = np.array(res[m])
        print(f"  {m:<15} {arr.mean():>7.0f} +/- {arr.std()/np.sqrt(N_SEEDS):>5.0f}")
    print(f"  [{time.time()-t0:.1f}s]")
    return {m: np.array(v) for m, v in res.items()}


if __name__ == "__main__":
    print("=" * 80)
    print(f"Action-set-size ablation on Satimage  (d={D}, r={R}, seeds={N_SEEDS})")
    print("=" * 80)

    all_results = {}
    overall_t0 = time.time()
    for n_act in ACTION_SIZES:
        all_results[n_act] = run_cell(n_act)
    print(f"\nTotal time: {(time.time()-overall_t0)/60:.1f} min")

    save_results(
        __file__,
        config={
            "N_SEEDS": N_SEEDS, "D": D, "R": R,
            "SEGMENT_SIZE": SEGMENT_SIZE, "N_SEGMENTS": N_SEGMENTS,
            "WINDOW": WINDOW, "LAM": LAM, "DELTA": DELTA,
            "PROBE_EVERY": PROBE_EVERY, "PROBE_COST": PROBE_COST,
            "ACTION_SIZES": ACTION_SIZES, "METHODS": METHODS,
        },
        results=all_results,
    )
    print("Done.")
