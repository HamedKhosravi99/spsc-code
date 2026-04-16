"""
Pendigits Quick Test: 3 seeds, all 10 methods, verbose output after each cell.
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")

from environments import RealPendigitsEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, OracleLinUCB,
    SWLinUCB, RestartLinUCB, LowRankRewardUCB, LowOFUL, VOFUL,
    RunMetrics,
)

# ---------------------------------------------------------------------------
# Parameters — same as pendigits original, 3 seeds for quick test
# ---------------------------------------------------------------------------
N_SEEDS     = 3
SEG_SIZE    = 500
N_SEGMENTS  = 10
PROBE_EVERY = 10
WINDOW      = 400
LAM         = 0.01
DELTA       = 0.05
PROBE_COST  = 0.02

D_VALUES = [5, 55, 105, 155]
R_VALUES = [1, 10, 20, 30]

METHOD_NAMES = [
    "Oracle-LinUCB",
    "SPSC-Alg1",
    "SPSC-Adaptive",
    "LowOFUL",
    "VOFUL",
    "LowRank-Reward",
    "SW-LinUCB",
    "D-LinUCB",
    "Restart-LinUCB",
    "LinUCB",
]

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

COMPETITORS = ["LinUCB", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB",
               "LowRank-Reward", "LowOFUL", "VOFUL"]


def make_env(seed, d, r):
    return RealPendigitsEnvironment(
        d=d, r=r, n_actions=40, segment_size=SEG_SIZE,
        n_segments=N_SEGMENTS, seed=seed * 13 + 7,
    )


def run_cell(d, r):
    results = {m: [] for m in METHOD_NAMES}

    for seed in range(N_SEEDS):
        env = make_env(seed, d, r)
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
        results["SPSC-Alg1"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                          window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                          m_relearn=30, det_window=50, cusum_threshold=3.0,
                          warmup=100).run()
        results["SPSC-Adaptive"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000).run()
        results["LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 2000,
                   forgetting_factor=0.998).run()
        results["D-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                     seed=seed + 3000).run()
        results["SW-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = OracleLinUCB(env, window=10000, lam=LAM, delta=DELTA,
                         seed=seed + 4000).run()
        results["Oracle-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        T_env = env.T
        m = RestartLinUCB(env, restart_period=T_env // N_SEGMENTS,
                          lam=LAM, delta=DELTA, seed=seed + 5000).run()
        results["Restart-LinUCB"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = LowRankRewardUCB(env, window=WINDOW, pca_warmup=50,
                              lam=LAM, delta=DELTA, seed=seed + 6000).run()
        results["LowRank-Reward"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 7000,
                     pca_warmup=30, subspace_update_freq=20).run()
        results["LowOFUL"].append(m.cumulative_control_regret[-1])

        env = make_env(seed, d, r)
        m = VOFUL(env, lam=LAM, delta=DELTA, seed=seed + 8000,
                  pca_warmup=30, subspace_update_freq=20).run()
        results["VOFUL"].append(m.cumulative_control_regret[-1])

    return {m: np.array(results[m]) for m in METHOD_NAMES}


def print_cell_results(res, d, r):
    """Print full table for one cell immediately after it completes."""
    n = N_SEEDS
    lin_mean = res["LinUCB"].mean()
    best_comp_mean = min(res[m].mean() for m in COMPETITORS)
    best_method = min(COMPETITORS, key=lambda m: res[m].mean())

    print()
    print("=" * 110)
    print(f"  Pendigits d={d}, r={r}   ({n} seeds)")
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


if __name__ == "__main__":
    print("=" * 80)
    print("Pendigits QUICK TEST (10 methods, 3 seeds)")
    print(f"  d = {D_VALUES}")
    print(f"  r = {R_VALUES}")
    print(f"  lam={LAM}, probe_every={PROBE_EVERY}, window={WINDOW}")
    print("=" * 80)

    total_cells = len(D_VALUES) * len(R_VALUES)
    cell_idx = 0

    for d in D_VALUES:
        for r in R_VALUES:
            cell_idx += 1
            if r >= d:
                print(f"\n[{cell_idx}/{total_cells}] d={d}, r={r} -- SKIPPED (r >= d)")
                continue

            t0 = time.time()
            print(f"\n[{cell_idx}/{total_cells}] Running d={d}, r={r} "
                  f"(10 methods x {N_SEEDS} seeds) ...", flush=True)

            res = run_cell(d, r)
            elapsed = time.time() - t0
            print(f"  Completed in {elapsed:.1f}s")

            # Print FULL table for this cell right away
            print_cell_results(res, d, r)

    print("\nAll cells done.")
