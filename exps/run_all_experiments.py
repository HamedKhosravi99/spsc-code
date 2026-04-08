"""
Run all paper experiments and print a summary.

Usage
-----
    python run_all_experiments.py              # all experiments
    python run_all_experiments.py --synthetic  # synthetic only (faster)
    python run_all_experiments.py --real       # real-data only
    python run_all_experiments.py --main       # main paper only (4 experiments)

Each experiment saves its figure as *.png in the same directory.
"""

import subprocess
import sys
import os
import time
import argparse

# Reproducibility check
try:
    import numpy as np
    major = int(np.__version__.split(".")[0])
    if major >= 2:
        print(f"WARNING: numpy {np.__version__} detected. Reference results were "
              f"generated with numpy 1.x. RNG streams differ across major versions.")
    else:
        print(f"numpy {np.__version__} — RNG reproducibility: OK")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Experiment registry — matches paper experiment roadmap (Table 9)
# (name, script, output_figure, category)
# ---------------------------------------------------------------------------

EXPERIMENTS = [
    # --- Main paper (Section 6) ---
    ("Exp 1: Phase transition (data)",
     "experiment1_main_benchmark.py",
     "experiment1_main_benchmark.png", "main"),

    ("Exp 1: Phase transition (figure)",
     "experiment1_final_figure.py",
     "experiment1_synthetic_phase.png", "main"),

    ("Exp 2: Covertype multi-baseline",
     "experiment_covertype.py",
     "experiment_covertype.png", "main"),

    ("Exp 3: Warfarin (data)",
     "experiment_real_bandit.py",
     "experiment_real_bandit.png", "main"),

    ("Exp 3: Warfarin (figure)",
     "plot_warfarin.py",
     "experiment_warfarin.png", "main"),

    ("Exp 4: Robustness ABC",
     "experiment_robustness_abc.py",
     "experiment_robustness_abc.png", "main"),

    # --- Appendix: mechanism validation ---
    ("Probe-rate ablation",
     "experiment3_probe_ablation.py",
     "experiment3_probe_ablation.png", "synthetic"),

    ("Subspace recovery rate",
     "experiment2_subspace_recovery.py",
     "experiment2_subspace_recovery.png", "synthetic"),

    ("Change-point adaptation",
     "experiment4_changepoint_recovery.py",
     "experiment4_changepoint_recovery.png", "synthetic"),

    ("Dimension scaling",
     "experiment5_dimension_scaling.py",
     "experiment5_dimension_scaling.png", "synthetic"),

    # --- Appendix: sensitivity studies ---
    ("Noise robustness",
     "experiment6_noise_robustness.py",
     "experiment6_noise_robustness.png", "synthetic"),

    ("Changepoint frequency",
     "experiment7_changepoint_frequency.py",
     "experiment7_changepoint_frequency.png", "synthetic"),

    ("Drift speed",
     "experiment8_drift_speed.py",
     "experiment8_drift_speed.png", "synthetic"),

    # --- Appendix: SOTA and real-data ---
    ("SOTA comparison",
     "experiment9_sota_benchmark.py",
     "experiment9_sota_benchmark.png", "synthetic"),

    ("Pendigits regime",
     "experiment_pendigits_operating_regime.py",
     "experiment_pendigits_operating_regime.png", "real"),

    ("Satimage regime",
     "experiment_real_satimage_regime.py",
     "experiment_real_satimage_double_rings.png", "real"),

    ("Rank misspecification",
     "experiment_rank_misspec.py",
     "experiment_rank_misspec.png", "real"),

    ("Satimage aggregate",
     "satimage_final_plots.py",
     "satimage_wincount.png", "real"),
]

ROOT = os.path.dirname(os.path.abspath(__file__))


def run(name, script):
    path = os.path.join(ROOT, script)
    if not os.path.exists(path):
        print(f"  SKIP — {script} not found")
        return None
    print(f"\n{'='*60}")
    print(f"  {name}: {script}")
    print(f"{'='*60}")
    t0 = time.time()
    result = subprocess.run([sys.executable, path], cwd=ROOT)
    elapsed = time.time() - t0
    status = "OK" if result.returncode == 0 else f"FAILED (code {result.returncode})"
    print(f"  -> {status}  ({elapsed:.0f}s)")
    return result.returncode == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--synthetic", action="store_true",
                       help="Run synthetic experiments only")
    group.add_argument("--real", action="store_true",
                       help="Run real-data experiments only")
    group.add_argument("--main", action="store_true",
                       help="Run main paper experiments only (Exp 1-4)")
    args = parser.parse_args()

    if args.synthetic:
        selected = [e for e in EXPERIMENTS if e[3] == "synthetic"]
    elif args.real:
        selected = [e for e in EXPERIMENTS if e[3] == "real"]
    elif args.main:
        selected = [e for e in EXPERIMENTS if e[3] == "main"]
    else:
        selected = EXPERIMENTS

    results = []
    for name, script, fig, cat in selected:
        results.append((name, script, fig, run(name, script)))

    print(f"\n{'='*60}")
    print("  Summary")
    print(f"{'='*60}")
    for name, script, fig, passed in results:
        if passed is None:
            mark = "-"
        elif passed:
            mark = "v"
        else:
            mark = "X"
        fig_path = os.path.join(ROOT, fig)
        fig_status = "[saved]" if os.path.exists(fig_path) else "[MISSING]"
        print(f"  {mark} {name:35s}  {fig}  {fig_status}")
    print(f"{'='*60}")

    failures = [r for r in results if r[3] is False]
    if failures:
        print(f"\n{len(failures)} experiment(s) failed.")
        sys.exit(1)
    else:
        print(f"\nAll {len(results)} experiment(s) completed.")
