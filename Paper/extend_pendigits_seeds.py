"""
Extend Pendigits phase diagram from 5 seeds to 15 seeds.
Loads cached 5-seed averages, runs 10 more seeds (5-14),
combines via weighted average, saves updated cache, regenerates plots.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from experiment_phase_diagram import (
    PendigitsEnvironment, run_single,
    D_GRID, R_GRID, T_SWEEP, K, PROBE_EVERY, PROBE_COST, WINDOW,
    make_phase_diagram,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(OUT_DIR, "phase_diagram_data.npz")

OLD_SEEDS = 5
NEW_SEEDS_START = 5
NEW_SEEDS_END = 15  # seeds 5..14
TOTAL_SEEDS = 15


def main():
    # Load old 5-seed cache
    print("Loading cached 5-seed data ...")
    cached = np.load(CACHE_PATH)
    old_spsc = cached["spsc_regret"]
    old_lin = cached["lin_regret"]
    old_oracle = cached["oracle_regret"]

    n_r, n_d = len(R_GRID), len(D_GRID)

    # Accumulators for new seeds (sum, not mean)
    new_spsc = np.zeros((n_r, n_d))
    new_lin = np.zeros((n_r, n_d))
    new_oracle = np.zeros((n_r, n_d))
    new_count = np.zeros((n_r, n_d), dtype=int)

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
                s, l, o = run_single(d, r, seed)
                new_spsc[i, j] += s
                new_lin[i, j] += l
                new_oracle[i, j] += o
                new_count[i, j] += 1

            n_new = new_count[i, j]
            # Combined mean: (old_mean * 5 + new_sum) / 15
            combined_spsc = (old_spsc[i, j] * OLD_SEEDS + new_spsc[i, j]) / TOTAL_SEEDS
            combined_lin = (old_lin[i, j] * OLD_SEEDS + new_lin[i, j]) / TOTAL_SEEDS
            ratio = combined_spsc / max(combined_lin, 1e-8)
            pct = (1 - ratio) * 100
            tag = "SPSC wins" if pct > 0 else "LinUCB wins"
            print(f"  combined ratio={ratio:.3f}  ({tag}, {abs(pct):.0f}%)")

    # Combine all
    spsc_regret = (old_spsc * OLD_SEEDS + new_spsc) / TOTAL_SEEDS
    lin_regret = (old_lin * OLD_SEEDS + new_lin) / TOTAL_SEEDS
    oracle_regret = (old_oracle * OLD_SEEDS + new_oracle) / TOTAL_SEEDS

    # Handle r >= d cells (keep zeros)
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r >= d:
                spsc_regret[i, j] = 0
                lin_regret[i, j] = 0
                oracle_regret[i, j] = 0

    ratio_spsc_lin = np.ones((n_r, n_d))
    ratio_spsc_oracle = np.ones((n_r, n_d))
    for i, r in enumerate(R_GRID):
        for j, d in enumerate(D_GRID):
            if r < d:
                ratio_spsc_lin[i, j] = spsc_regret[i, j] / max(lin_regret[i, j], 1e-8)
                ratio_spsc_oracle[i, j] = spsc_regret[i, j] / max(oracle_regret[i, j], 1e-8)

    # Print summary
    print("\n" + "=" * 65)
    print(f"SPSC / LinUCB regret ratio ({TOTAL_SEEDS} seeds)")
    print("-" * 65)
    header = f"{'r \\\\ d':>6}" + "".join(f"{d:>8}" for d in D_GRID)
    print(header)
    print("-" * 65)
    wins = 0
    valid = 0
    for i, r in enumerate(R_GRID):
        row = f"{r:>6}"
        for j, d in enumerate(D_GRID):
            if r >= d:
                row += f"{'---':>8}"
            else:
                row += f"{ratio_spsc_lin[i,j]:>8.3f}"
                valid += 1
                if ratio_spsc_lin[i, j] < 1.0:
                    wins += 1
        print(row)
    print(f"\nSPSC wins {wins}/{valid} cells")
    print("=" * 65)

    # Save updated cache
    np.savez_compressed(
        CACHE_PATH,
        d_grid=np.array(D_GRID), r_grid=np.array(R_GRID),
        ratio_spsc_lin=ratio_spsc_lin, ratio_spsc_oracle=ratio_spsc_oracle,
        spsc_regret=spsc_regret, lin_regret=lin_regret, oracle_regret=oracle_regret,
    )
    print(f"Saved updated cache: {CACHE_PATH}")

    # Patch N_SEEDS so plot title shows 15
    import experiment_phase_diagram
    experiment_phase_diagram.N_SEEDS = TOTAL_SEEDS

    # Regenerate plot
    make_phase_diagram(ratio_spsc_lin, ratio_spsc_oracle,
                       spsc_regret, lin_regret, oracle_regret)
    print("Done.")


if __name__ == "__main__":
    main()
