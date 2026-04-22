"""LinTS baselines on MovieLens Real. Same grid/settings as experiment_movielens_real_grid.py."""
import os, sys, time, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from environments import RealMovieLensEnvironment
from algorithm import LinTS, SWLinTS

N_SEEDS = 10; SEG_SIZE = 500; N_SEGMENTS = 10
WINDOW = 400; LAM = 0.01; DELTA = 0.05
D_VALUES = [55, 105, 200]; R_VALUES = [5, 10, 20]

def make_env(seed, d, r):
    return RealMovieLensEnvironment(d=d, r=r, n_actions=40, segment_size=SEG_SIZE,
                                    n_segments=N_SEGMENTS, seed=seed * 13 + 7)

def run_cell(d, r):
    res = {"LinTS": [], "SW-LinTS": []}
    for seed in range(N_SEEDS):
        t0 = time.time()
        env = make_env(seed, d, r)
        val = LinTS(env, lam=LAM, delta=DELTA, seed=seed + 9000).run().cumulative_control_regret[-1]
        res["LinTS"].append(val)
        env = make_env(seed, d, r)
        val2 = SWLinTS(env, window=WINDOW, lam=LAM, delta=DELTA, seed=seed + 10000).run().cumulative_control_regret[-1]
        res["SW-LinTS"].append(val2)
        print(f"    seed {seed+1}/{N_SEEDS}  LinTS={val:.0f}  SW-LinTS={val2:.0f}  [{time.time()-t0:.1f}s]", flush=True)
    return {m: np.array(v) for m, v in res.items()}

if __name__ == "__main__":
    from results_io import save_results
    print(f"MovieLens LinTS ({N_SEEDS} seeds)")
    all_results = {}
    for d in D_VALUES:
        for r in R_VALUES:
            if r >= d:
                print(f"\n  d={d}, r={r} -- SKIPPED")
                all_results[(d, r)] = None
                continue
            print(f"\n  d={d}, r={r}  (d-r={d-r})", flush=True)
            res = run_cell(d, r)
            all_results[(d, r)] = res
            for m in res:
                arr = res[m]
                print(f"    {m:<12}  mean={arr.mean():.0f}  se={arr.std()/np.sqrt(N_SEEDS):.0f}")
    save_results(__file__,
                 config={"N_SEEDS": N_SEEDS, "SEG_SIZE": SEG_SIZE, "N_SEGMENTS": N_SEGMENTS,
                         "WINDOW": WINDOW, "LAM": LAM, "DELTA": DELTA,
                         "D_VALUES": D_VALUES, "R_VALUES": R_VALUES},
                 results=all_results)
    print("\nDone.")
