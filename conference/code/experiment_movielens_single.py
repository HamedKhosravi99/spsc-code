"""
MovieLens single-seed test: d=105, r=20, all 10 methods.
Runs BOTH semi-synthetic and fully-real versions.
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")

from environments import MovieLensEnvironment, RealMovieLensEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, OracleLinUCB,
    SWLinUCB, RestartLinUCB, LowRankRewardUCB, LowOFUL, VOFUL,
)

D           = 105
R           = 20
SEG_SIZE    = 500
N_SEGMENTS  = 10
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


def run_method(name, env, seed):
    T_env = env.T
    if name == "SPSC-Alg1":
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
    elif name == "SPSC-Adaptive":
        m = SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                          window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                          m_relearn=30, det_window=50, cusum_threshold=3.0,
                          warmup=100).run()
    elif name == "LinUCB":
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000).run()
    elif name == "Oracle-LinUCB":
        m = OracleLinUCB(env, window=10000, lam=LAM, delta=DELTA,
                         seed=seed + 2000).run()
    elif name == "D-LinUCB":
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 3000,
                   forgetting_factor=0.998).run()
    elif name == "SW-LinUCB":
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA,
                     seed=seed + 4000).run()
    elif name == "Restart-LinUCB":
        m = RestartLinUCB(env, restart_period=T_env // N_SEGMENTS,
                          lam=LAM, delta=DELTA, seed=seed + 5000).run()
    elif name == "LowRank-Reward":
        m = LowRankRewardUCB(env, window=WINDOW, pca_warmup=50,
                              lam=LAM, delta=DELTA, seed=seed + 6000).run()
    elif name == "LowOFUL":
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 7000,
                     pca_warmup=30, subspace_update_freq=20).run()
    elif name == "VOFUL":
        m = VOFUL(env, lam=LAM, delta=DELTA, seed=seed + 8000,
                  pca_warmup=30, subspace_update_freq=20).run()
    return m.cumulative_control_regret[-1]


def run_all(env_name, make_env_fn):
    """Run all 10 methods on one environment, print per-method."""
    print(f"\n{'='*90}")
    print(f"  {env_name}: d={D}, r={R}, SEG_SIZE={SEG_SIZE}, N_SEGMENTS={N_SEGMENTS}")
    print(f"  lam={LAM}, probe_every={PROBE_EVERY}, window={WINDOW}, c={PROBE_COST}")
    print(f"{'='*90}")

    results = {}
    t_total = time.time()

    for name in METHOD_NAMES:
        env = make_env_fn()
        t0 = time.time()
        val = run_method(name, env, seed=0)
        results[name] = val
        elapsed = time.time() - t0
        print(f"  {METHOD_LABELS[name]:<30}  regret = {val:>8.0f}   [{elapsed:.1f}s]",
              flush=True)

    print(f"  {'':30}  {'':>8}   [total: {time.time()-t_total:.1f}s]")

    # Summary table
    lin_val = results["LinUCB"]
    best_comp_val = min(results[m] for m in COMPETITORS)
    best_comp_name = min(COMPETITORS, key=lambda m: results[m])

    print()
    print("-" * 90)
    print(f"  {'Method':<30}  {'Regret':>8}  {'vs LinUCB':>10}  {'vs Best':>10}  {'Note':>12}")
    print("-" * 90)
    for name in METHOD_NAMES:
        val = results[name]
        vs_lin = (val / max(lin_val, 1e-8) - 1) * 100
        vs_best = (val / max(best_comp_val, 1e-8) - 1) * 100
        if name in ("SPSC-Alg1", "SPSC-Adaptive"):
            tag = "<<< WINS" if val < best_comp_val else ""
        elif name == "Oracle-LinUCB":
            tag = "(oracle)"
        else:
            tag = "* best" if name == best_comp_name else ""
        print(f"  {METHOD_LABELS[name]:<30}  {val:>8.0f}  "
              f"{vs_lin:>+10.1f}%  {vs_best:>+10.1f}%  {tag:>12}")
    print("=" * 90)
    return results


if __name__ == "__main__":
    seed = 0

    # --- Semi-synthetic ---
    print("\n" + "#" * 90)
    print("#  MOVIELENS SEMI-SYNTHETIC (rewards = x^T theta + noise)")
    print("#" * 90)
    res_semi = run_all(
        "MovieLens Semi-Synthetic",
        lambda: MovieLensEnvironment(
            d=D, r=R, n_actions=40, segment_size=SEG_SIZE,
            n_segments=N_SEGMENTS, seed=seed * 13 + 7,
        ),
    )

    # --- Fully real ---
    print("\n" + "#" * 90)
    print("#  MOVIELENS FULLY REAL (rewards = actual user ratings)")
    print("#" * 90)
    res_real = run_all(
        "MovieLens Fully Real",
        lambda: RealMovieLensEnvironment(
            d=D, r=R, n_actions=40, segment_size=SEG_SIZE,
            n_segments=N_SEGMENTS, seed=seed * 13 + 7,
        ),
    )

    # --- Comparison ---
    print("\n" + "=" * 90)
    print("COMPARISON: Semi-Synthetic vs Fully Real")
    print("-" * 90)
    print(f"  {'Method':<30}  {'Semi':>10}  {'Real':>10}  {'Diff':>10}")
    print("-" * 90)
    for name in METHOD_NAMES:
        s, r_ = res_semi[name], res_real[name]
        print(f"  {METHOD_LABELS[name]:<30}  {s:>10.0f}  {r_:>10.0f}  {r_-s:>+10.0f}")
    print("=" * 90)

    from results_io import save_results
    save_results(__file__,
                 config={"D": D, "R": R, "SEG_SIZE": SEG_SIZE, "N_SEGMENTS": N_SEGMENTS,
                         "PROBE_EVERY": PROBE_EVERY, "PROBE_COST": PROBE_COST,
                         "WINDOW": WINDOW, "LAM": LAM, "DELTA": DELTA, "N_SEEDS": 1,
                         "METHOD_NAMES": METHOD_NAMES},
                 results={"semi_synthetic": res_semi, "fully_real": res_real})
