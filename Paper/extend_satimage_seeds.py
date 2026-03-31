"""
Extend Satimage benchmark from 5 seeds to 15 seeds.
Loads cached 5-seed averages, runs 10 more seeds (5-14),
combines via weighted average, saves updated cache, regenerates plots.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from experiment_satimage import (
    SatimageEnvironment, run_single, print_summary,
    fig_concentric_rings, fig_bubble_multi_method,
    D_GRID, R_GRID, T_SWEEP, K, METHOD_NAMES,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(OUT_DIR, "satimage_phase_data.npz")

OLD_SEEDS = 5
NEW_SEEDS_START = 5
NEW_SEEDS_END = 15  # seeds 5..14
TOTAL_SEEDS = 15


def main():
    # Load old 5-seed cache
    print("Loading cached 5-seed data ...")
    cached = np.load(CACHE_PATH)
    old_grids = {}
    for m in METHOD_NAMES:
        old_grids[m] = cached[f"{m}_regret"]

    n_r, n_d = len(R_GRID), len(D_GRID)

    # Accumulators for new seeds (sum, not mean)
    new_sums = {m: np.zeros((n_r, n_d)) for m in METHOD_NAMES}

    total = n_d * n_r
    done = 0
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            done += 1
            if r >= d:
                continue
            print(f"  [{done}/{total}] d={d}, r={r} (seeds {NEW_SEEDS_START}-{NEW_SEEDS_END-1}) ...",
                  end="", flush=True)

            for seed in range(NEW_SEEDS_START, NEW_SEEDS_END):
                res = run_single(d, r, seed)
                for m in METHOD_NAMES:
                    new_sums[m][i, j] += res[m]

            # Combined mean
            combined_spsc = (old_grids["SPSC-Alg1"][i, j] * OLD_SEEDS + new_sums["SPSC-Alg1"][i, j]) / TOTAL_SEEDS
            combined_lin = (old_grids["LinUCB"][i, j] * OLD_SEEDS + new_sums["LinUCB"][i, j]) / TOTAL_SEEDS
            ratio = combined_spsc / max(combined_lin, 1e-8)
            pct = (1 - ratio) * 100
            tag = "SPSC wins" if pct > 0 else "LinUCB wins"
            print(f"  SPSC/Lin={ratio:.3f}  ({tag}, {abs(pct):.0f}%)")

    # Combine all
    regret_grids = {}
    for m in METHOD_NAMES:
        regret_grids[m] = (old_grids[m] * OLD_SEEDS + new_sums[m]) / TOTAL_SEEDS
        # Handle r >= d cells
        for i, r in enumerate(R_GRID):
            for j, d in enumerate(D_GRID):
                if r >= d:
                    regret_grids[m][i, j] = 0

    print_summary(regret_grids)

    # Save updated cache
    save_dict = {f"{m}_regret": regret_grids[m] for m in METHOD_NAMES}
    save_dict["d_grid"] = np.array(D_GRID)
    save_dict["r_grid"] = np.array(R_GRID)
    np.savez_compressed(CACHE_PATH, **save_dict)
    print(f"Saved updated cache: {CACHE_PATH}")

    # Patch N_SEEDS so plot titles show 15
    import experiment_satimage
    experiment_satimage.N_SEEDS = TOTAL_SEEDS

    # Regenerate plots
    fig_concentric_rings(regret_grids)
    fig_bubble_multi_method(regret_grids)

    # Also regenerate final plots — reload to pick up new cache
    print("\nRegenerating final plots ...")
    import importlib
    import satimage_final_plots
    importlib.reload(satimage_final_plots)
    satimage_final_plots.fig_double_rings()
    satimage_final_plots.fig_dot_strip()
    satimage_final_plots.fig_wincount()

    print("\nDone.")


if __name__ == "__main__":
    main()
