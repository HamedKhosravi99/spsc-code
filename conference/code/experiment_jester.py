"""
Jester bandit experiment.

Uses the Jester Dataset 1 (Goldberg et al., UC Berkeley): 73K users,
100 jokes, ratings in [-10, +10].  This is the closest dataset in our
evaluation to true bandit feedback — at each round the reward returned
by env.step() is the user's *actual* rating for the chosen joke, not
a simulated x^T theta + noise.

Setup mirrors experiment_pendigits_extended.py:
  - K=10 segments (user clusters by latent preference)
  - T=5,000
  - d in {55, 105}, r in {5, 10}
  - 10 seeds per cell
  - 10 methods (Oracle, SPSC, SPSC-Adaptive, LowOFUL, VOFUL,
                LowRank-Reward, SW-LinUCB, D-LinUCB, Restart-LinUCB,
                LinUCB)

First run downloads ~4MB of Jester data into
conference/code/environments/.jester_cache/.

Output:
  results/experiment_jester.json
  experiment_jester.png
"""

import os, sys, time, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import RealJesterEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, OracleLinUCB,
    SWLinUCB, RestartLinUCB, LowRankRewardUCB, LowOFUL, VOFUL,
)

OUT_DIR     = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(OUT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
RESULTS_PATH = os.path.join(RESULTS_DIR, "experiment_jester.json")
FIGURE_PATH  = os.path.join(OUT_DIR, "experiment_jester.png")

# --- configuration --------------------------------------------------------
N_SEEDS     = 10
SEG_SIZE    = 500
N_SEGMENTS  = 10
PROBE_EVERY = 10
WINDOW      = 400
LAM         = 0.01
DELTA       = 0.05
PROBE_COST  = 0.02

D_VALUES = [55, 105]
R_VALUES = [5, 10]

METHOD_NAMES = [
    "Oracle-LinUCB", "SPSC-Alg1", "SPSC-Adaptive",
    "LowOFUL", "VOFUL", "LowRank-Reward",
    "SW-LinUCB", "D-LinUCB", "Restart-LinUCB", "LinUCB",
]

METHOD_LABELS = {
    "Oracle-LinUCB":  "Oracle LinUCB",
    "SPSC-Alg1":      "SPSC (ours)",
    "SPSC-Adaptive":  "SPSC-Adaptive (ours)",
    "LowOFUL":        "LowOFUL",
    "VOFUL":          "VOFUL",
    "LowRank-Reward": "LowRank-Reward",
    "SW-LinUCB":      "SW-LinUCB",
    "D-LinUCB":       "D-LinUCB",
    "Restart-LinUCB": "Restart-LinUCB",
    "LinUCB":         "LinUCB",
}

METHOD_COLORS = {
    "Oracle-LinUCB":  "#2ca02c",
    "SPSC-Alg1":      "#1f77b4",
    "SPSC-Adaptive":  "#17becf",
    "LowOFUL":        "#e377c2",
    "VOFUL":          "#9467bd",
    "LowRank-Reward": "#7f7f7f",
    "SW-LinUCB":      "#bcbd22",
    "D-LinUCB":       "#ff7f0e",
    "Restart-LinUCB": "#8c564b",
    "LinUCB":         "#d62728",
}

COMPETITORS = ["LinUCB", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB",
               "LowRank-Reward", "LowOFUL", "VOFUL"]


def make_env(seed, d, r):
    return RealJesterEnvironment(
        d=d, r=r, n_actions=40, segment_size=SEG_SIZE,
        n_segments=N_SEGMENTS, seed=seed * 13 + 7,
    )


def run_method(name, seed, d, r):
    env = make_env(seed, d, r)
    if name == "SPSC-Alg1":
        m = SPSC_Algorithm1(
            env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
            normalize_gamma_by_d=True,
        ).run()
    elif name == "SPSC-Adaptive":
        m = SPSC_Adaptive(
            env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
            m_relearn=30, det_window=50, cusum_threshold=3.0,
            warmup=100,
        ).run()
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
        T_env = env.T
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
    return float(m.cumulative_control_regret[-1])


def run_cell(d, r):
    print(f"\n[Cell d={d}, r={r}]  {len(METHOD_NAMES)} methods x {N_SEEDS} seeds")
    print("-" * 80)
    results = {m: [] for m in METHOD_NAMES}
    cell_t0 = time.time()
    for seed in range(N_SEEDS):
        print(f"  seed {seed+1}/{N_SEEDS}")
        for name in METHOD_NAMES:
            t0 = time.time()
            val = run_method(name, seed, d, r)
            results[name].append(val)
            print(f"    {METHOD_LABELS[name]:<25}  regret = {val:>8.0f}   "
                  f"[{time.time()-t0:.1f}s]", flush=True)
    print(f"  Cell done in {time.time()-cell_t0:.1f}s")
    return {m: np.array(results[m]) for m in METHOD_NAMES}


def print_cell_summary(res, d, r):
    n = N_SEEDS
    lin_mean = res["LinUCB"].mean()
    best_comp_mean = min(res[m].mean() for m in COMPETITORS)
    best_method = min(COMPETITORS, key=lambda m: res[m].mean())
    print()
    print("=" * 110)
    print(f"  Jester  d={d}, r={r}   ({n} seeds)")
    print("-" * 110)
    print(f"  {'Method':<28}  {'Mean':>8}  {'SE':>8}  {'vs LinUCB':>10}  "
          f"{'vs Best':>10}  {'Note':>12}")
    print("-" * 110)
    for method in METHOD_NAMES:
        arr = res[method]
        mean = arr.mean()
        se   = arr.std() / np.sqrt(n)
        vs_lin  = (mean / max(lin_mean, 1e-8) - 1) * 100
        vs_best = (mean / max(best_comp_mean, 1e-8) - 1) * 100
        if method in ("SPSC-Alg1", "SPSC-Adaptive"):
            tag = "<<< WINS" if mean < best_comp_mean else ""
        elif method == "Oracle-LinUCB":
            tag = "(oracle)"
        else:
            tag = "* best" if method == best_method else ""
        print(f"  {METHOD_LABELS[method]:<28}  {mean:>8.0f}  {se:>8.0f}  "
              f"{vs_lin:>+9.1f}%  {vs_best:>+9.1f}%  {tag:>12}")
    print("=" * 110)


def make_figure(all_results, out_path):
    cells = list(all_results.keys())
    n = len(cells)
    if n == 0:
        return
    fig, axes = plt.subplots(1, n, figsize=(6.0 * n, 7.0), sharey=False)
    if n == 1:
        axes = [axes]
    LABEL_COLOR = "#000000"

    for ax, (d, r) in zip(axes, cells):
        res = all_results[(d, r)]
        means = np.array([res[m].mean() for m in METHOD_NAMES])
        ses   = np.array([res[m].std() / np.sqrt(N_SEEDS) for m in METHOD_NAMES])
        order = np.argsort(means)

        y = np.arange(len(METHOD_NAMES))
        ax.barh(
            y, means[order], xerr=ses[order],
            color=[METHOD_COLORS[METHOD_NAMES[i]] for i in order],
            capsize=3.5, height=0.7, edgecolor="black", linewidth=0.6,
        )
        ax.set_yticks(y)
        ax.set_yticklabels(
            [METHOD_LABELS[METHOD_NAMES[i]] for i in order],
            fontsize=12.5, color=LABEL_COLOR, fontweight="bold",
        )
        ax.set_xlabel("Control regret", fontsize=14,
                      color=LABEL_COLOR, fontweight="bold")
        ax.set_title(f"$d{{=}}{d}$, $r{{=}}{r}$",
                     fontsize=15, fontweight="bold", color=LABEL_COLOR)
        ax.tick_params(axis="x", labelsize=12, colors=LABEL_COLOR)
        ax.tick_params(axis="y", labelsize=12.5, colors=LABEL_COLOR)
        for spine in ax.spines.values():
            spine.set_color(LABEL_COLOR); spine.set_linewidth(1.0)
        ax.xaxis.grid(True, alpha=0.35)

    fig.suptitle(
        "Jester real-rating bandit (joke recommendation, ratings $\\in[-10,+10]$)",
        fontsize=16, fontweight="bold", y=1.02, color=LABEL_COLOR,
    )
    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight")
    print(f"Saved: {out_path}")


def main():
    print("=" * 80)
    print("Jester real-rating bandit experiment")
    print(f"  d in {D_VALUES}, r in {R_VALUES}")
    print(f"  N_SEEDS={N_SEEDS}, SEG_SIZE={SEG_SIZE}, N_SEGMENTS={N_SEGMENTS}")
    print(f"  T = {SEG_SIZE * N_SEGMENTS}, K = {N_SEGMENTS}")
    print("=" * 80)

    all_results = {}
    grand_t0 = time.time()
    for d in D_VALUES:
        for r in R_VALUES:
            res = run_cell(d, r)
            all_results[(d, r)] = res
            print_cell_summary(res, d, r)

    serial = {}
    for (d, r), res in all_results.items():
        serial[f"d={d},r={r}"] = {m: res[m].tolist() for m in METHOD_NAMES}
    with open(RESULTS_PATH, "w") as f:
        json.dump(serial, f, indent=2)
    print(f"\nSaved JSON: {RESULTS_PATH}")

    make_figure(all_results, FIGURE_PATH)
    print(f"\nTotal wall time: {time.time()-grand_t0:.1f}s")


if __name__ == "__main__":
    main()
