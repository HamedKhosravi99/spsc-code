"""LinTS baselines on Warfarin. Same settings as experiment_warfarin_extended.py."""
import os, sys, time, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from environments import WarfarinEnvironment
from algorithm import LinTS, SWLinTS

D = 93; K = 8; T = 5000; N_ACTIONS = 40; SIGMA_EPS = 0.3
N_SEEDS = 10; WINDOW = 200; LAM = 1.0; DELTA = 0.05
R_VALUES = [1, 2, 3, 5, 10]

def make_env(seed, r):
    return WarfarinEnvironment(d=D, r=r, K=K, T=T, n_actions=N_ACTIONS,
                               sigma_eps=SIGMA_EPS, seed=seed * 13 + 7)

if __name__ == "__main__":
    from results_io import save_results
    print(f"Warfarin LinTS (d={D}, K={K}, T={T}, {N_SEEDS} seeds)")
    all_results = {}
    for r in R_VALUES:
        print(f"\n  r={r}  (d-r={D-r})", flush=True)
        lints_vals, swlints_vals = [], []
        for seed in range(N_SEEDS):
            t0 = time.time()
            env = make_env(seed, r)
            val = LinTS(env, lam=LAM, delta=DELTA, seed=seed + 9000).run().cumulative_control_regret[-1]
            lints_vals.append(val)
            env = make_env(seed, r)
            val2 = SWLinTS(env, window=WINDOW, lam=LAM, delta=DELTA, seed=seed + 10000).run().cumulative_control_regret[-1]
            swlints_vals.append(val2)
            print(f"    seed {seed+1}/{N_SEEDS}  LinTS={val:.0f}  SW-LinTS={val2:.0f}  [{time.time()-t0:.1f}s]", flush=True)
        lints = np.array(lints_vals); swlints = np.array(swlints_vals)
        all_results[f"r={r}"] = {"LinTS": lints.tolist(), "SW-LinTS": swlints.tolist()}
        print(f"    {'LinTS':<12}  mean={lints.mean():.0f}  se={lints.std()/np.sqrt(N_SEEDS):.0f}")
        print(f"    {'SW-LinTS':<12}  mean={swlints.mean():.0f}  se={swlints.std()/np.sqrt(N_SEEDS):.0f}")
    save_results(__file__,
                 config={"D": D, "K": K, "T": T, "N_ACTIONS": N_ACTIONS, "SIGMA_EPS": SIGMA_EPS,
                         "N_SEEDS": N_SEEDS, "WINDOW": WINDOW, "LAM": LAM, "DELTA": DELTA,
                         "R_VALUES": R_VALUES},
                 results=all_results)
    print("\nDone.")
