"""
MNIST Grid: d in {55, 105, 200}, r in {5, 10, 20}, 3 seeds.
Pixel features via random projection. Per-seed per-method timing.
"""

import os, sys, time, numpy as np
import matplotlib
matplotlib.use("Agg")

from environments import MNISTEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, OracleLinUCB,
    SWLinUCB, RestartLinUCB, LowRankRewardUCB, LowOFUL, VOFUL,
    LinTS, SWLinTS,
)

N_SEEDS     = 10
SEG_SIZE    = 500
N_SEGMENTS  = 10
PROBE_EVERY = 10
PROBE_COST  = 0.02
WINDOW      = 400
LAM         = 0.01
DELTA       = 0.05

D_VALUES = [55, 105, 200]
R_VALUES = [5, 10, 20]

METHOD_NAMES = [
    "Oracle-LinUCB", "SPSC-Alg1", "SPSC-Adaptive",
    "LowOFUL", "VOFUL", "LowRank-Reward",
    "SW-LinUCB", "D-LinUCB", "Restart-LinUCB", "LinUCB",
    "LinTS", "SW-LinTS",
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
    "LinTS":            "LinTS (Agrawal+ '13)",
    "SW-LinTS":         "SW-LinTS",
}

COMPETITORS = ["LinUCB", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB",
               "LowRank-Reward", "LowOFUL", "VOFUL", "LinTS", "SW-LinTS"]


def make_env(seed, d, r):
    return MNISTEnvironment(
        d=d, r=r, n_actions=40, segment_size=SEG_SIZE,
        n_segments=N_SEGMENTS, seed=seed * 13 + 7,
    )


def run_method(name, seed, d, r):
    env = make_env(seed, d, r)
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
    elif name == "LinTS":
        m = LinTS(env, lam=LAM, delta=DELTA, seed=seed + 9000).run()
    elif name == "SW-LinTS":
        m = SWLinTS(env, window=WINDOW, lam=LAM, delta=DELTA,
                    seed=seed + 10000).run()
    return m.cumulative_control_regret[-1]


def run_cell(d, r):
    results = {m: [] for m in METHOD_NAMES}
    for seed in range(N_SEEDS):
        print(f"\n  -- seed {seed+1}/{N_SEEDS} --", flush=True)
        for name in METHOD_NAMES:
            t0 = time.time()
            val = run_method(name, seed, d, r)
            results[name].append(val)
            elapsed = time.time() - t0
            print(f"    {METHOD_LABELS[name]:<30}  regret = {val:>8.0f}   [{elapsed:.1f}s]",
                  flush=True)
    return {m: np.array(results[m]) for m in METHOD_NAMES}


def print_cell_summary(res, d, r):
    n = N_SEEDS
    lin_mean = res["LinUCB"].mean()
    best_comp_mean = min(res[m].mean() for m in COMPETITORS)
    best_method = min(COMPETITORS, key=lambda m: res[m].mean())

    print()
    print("=" * 110)
    print(f"  MNIST  d={d}, r={r}   ({n} seeds)   d-r={d-r}")
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
    print(f"MNIST Grid ({len(METHOD_NAMES)} methods, {N_SEEDS} seeds)")
    print(f"  d = {D_VALUES}")
    print(f"  r = {R_VALUES}")
    print(f"  SEG_SIZE={SEG_SIZE}, N_SEGMENTS={N_SEGMENTS}, "
          f"lam={LAM}, pe={PROBE_EVERY}, W={WINDOW}, c={PROBE_COST}")
    print(f"  Features = pixel values via random projection")
    print("=" * 80)

    all_results = {}
    total_cells = len(D_VALUES) * len(R_VALUES)
    cell_idx = 0

    for d in D_VALUES:
        for r in R_VALUES:
            cell_idx += 1
            if r >= d:
                print(f"\n[{cell_idx}/{total_cells}] d={d}, r={r} -- SKIPPED (r >= d)")
                all_results[(d, r)] = None
                continue

            t_cell = time.time()
            print(f"\n\n[{cell_idx}/{total_cells}] ========== d={d}, r={r}  (d-r={d-r}) ==========",
                  flush=True)

            res = run_cell(d, r)
            all_results[(d, r)] = res
            print(f"\n  Cell completed in {time.time()-t_cell:.1f}s")
            print_cell_summary(res, d, r)

    # Final ratio summaries
    print("\n" + "=" * 100)
    print("FINAL SUMMARY: SPSC-Alg1 / LinUCB ratio (* = SPSC wins)")
    header = f"{'d\\\\r':>6}"
    for r in R_VALUES:
        header += f"  {'r='+str(r):>10}"
    print(header)
    print("-" * (6 + 12 * len(R_VALUES)))
    for d in D_VALUES:
        row = f"{d:>6}"
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>10}"
            else:
                ratio = res["SPSC-Alg1"].mean() / max(res["LinUCB"].mean(), 1e-8)
                marker = "*" if ratio < 1.0 else " "
                row += f"  {ratio:>9.3f}{marker}"
        print(row)

    print(f"\nSPSC-Adaptive / LinUCB ratio:")
    print(header)
    print("-" * (6 + 12 * len(R_VALUES)))
    for d in D_VALUES:
        row = f"{d:>6}"
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>10}"
            else:
                ratio = res["SPSC-Adaptive"].mean() / max(res["LinUCB"].mean(), 1e-8)
                marker = "*" if ratio < 1.0 else " "
                row += f"  {ratio:>9.3f}{marker}"
        print(row)

    print(f"\nSPSC-Alg1 / Best Competitor ratio:")
    print(header)
    print("-" * (6 + 12 * len(R_VALUES)))
    for d in D_VALUES:
        row = f"{d:>6}"
        for r in R_VALUES:
            res = all_results.get((d, r))
            if res is None:
                row += f"  {'--':>10}"
            else:
                best_comp = min(res[m].mean() for m in COMPETITORS)
                ratio = res["SPSC-Alg1"].mean() / max(best_comp, 1e-8)
                marker = "*" if ratio < 1.0 else " "
                row += f"  {ratio:>9.3f}{marker}"
        print(row)
    print("=" * 100)

    from results_io import save_results
    save_results(__file__,
                 config={"N_SEEDS": N_SEEDS, "SEG_SIZE": SEG_SIZE, "N_SEGMENTS": N_SEGMENTS,
                         "PROBE_EVERY": PROBE_EVERY, "PROBE_COST": PROBE_COST,
                         "WINDOW": WINDOW, "LAM": LAM, "DELTA": DELTA,
                         "D_VALUES": D_VALUES, "R_VALUES": R_VALUES,
                         "METHOD_NAMES": METHOD_NAMES},
                 results=all_results)
    print("\nDone.")
