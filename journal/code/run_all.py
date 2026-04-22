"""
Driver: run all five journal-paper theory-validating experiments.

Usage
-----
    python run_all.py                # default seeds per experiment
    python run_all.py --seeds 5      # override all
    python run_all.py --only 1 3     # only experiments 1 and 3
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


EXPERIMENTS = [
    (1, 'exp1_minimax_recovery', 20),
    (2, 'exp2_probe_cost',       20),
    (4, 'exp4_identification',   20),
    (5, 'exp5_allocation',       20),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=None,
                    help='Override default seed count for every experiment')
    ap.add_argument('--only', type=int, nargs='+', default=None,
                    help='Run only the specified experiment numbers')
    args = ap.parse_args()

    to_run = args.only or [e[0] for e in EXPERIMENTS]
    t_total = time.time()
    for num, mod_name, default_seeds in EXPERIMENTS:
        if num not in to_run:
            continue
        print(f"\n{'='*70}\nExperiment {num}: {mod_name}\n{'='*70}",
              flush=True)
        seeds = args.seeds if args.seeds is not None else default_seeds
        # Run by exec'ing with overridden argv so each script's argparse picks up --seeds
        old_argv = sys.argv
        sys.argv = [mod_name + '.py', '--seeds', str(seeds)]
        try:
            mod = importlib.import_module(mod_name)
            importlib.reload(mod)   # ensure fresh module state
            mod.main()
        finally:
            sys.argv = old_argv
    print(f"\nAll experiments complete in {time.time() - t_total:.1f}s")


if __name__ == '__main__':
    main()
