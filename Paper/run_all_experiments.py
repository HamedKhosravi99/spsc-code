"""
Run all five experiments in sequence and print a summary.

Usage
-----
    python run_all_experiments.py

Each experiment saves its figure as experiment{N}_*.png in the same directory.
"""

import subprocess
import sys
import os
import time

# Reproducibility check — warn if numpy major version differs from what was used
# to generate the reference numbers (1.x with default_rng / PCG64).
try:
    import numpy as np
    major = int(np.__version__.split(".")[0])
    if major >= 2:
        print(f"WARNING: numpy {np.__version__} detected. Reference results were "
              f"generated with numpy 1.x. RNG streams differ across major versions — "
              f"numerical results will NOT match the paper's tables exactly.")
    else:
        print(f"numpy {np.__version__} — RNG reproducibility: OK")
except Exception:
    pass

SCRIPTS = [
    ("Experiment 1", "experiment1_main_benchmark.py",   "experiment1_main_benchmark.png"),
    ("Experiment 2", "experiment2_subspace_recovery.py","experiment2_subspace_recovery.png"),
    ("Experiment 3", "experiment3_probe_ablation.py",   "experiment3_probe_ablation.png"),
    ("Experiment 4", "experiment4_changepoint_recovery.py", "experiment4_changepoint_recovery.png"),
    ("Experiment 5", "experiment5_dimension_scaling.py","experiment5_dimension_scaling.png"),
]

ROOT = os.path.dirname(os.path.abspath(__file__))

def run(name, script):
    path = os.path.join(ROOT, script)
    print(f"\n{'='*60}")
    print(f"  {name}: {script}")
    print(f"{'='*60}")
    t0 = time.time()
    result = subprocess.run([sys.executable, path], cwd=ROOT)
    elapsed = time.time() - t0
    status = "OK" if result.returncode == 0 else f"FAILED (code {result.returncode})"
    print(f"  → {status}  ({elapsed:.0f}s)")
    return result.returncode == 0

if __name__ == "__main__":
    ok = []
    for name, script, _ in SCRIPTS:
        ok.append(run(name, script))

    print(f"\n{'='*60}")
    print("  Summary")
    print(f"{'='*60}")
    for (name, _, fig), passed in zip(SCRIPTS, ok):
        mark = "✓" if passed else "✗"
        fig_exists = os.path.exists(os.path.join(ROOT, fig))
        print(f"  {mark} {name:15s}  figure: {fig}  {'[saved]' if fig_exists else '[MISSING]'}")
    print(f"{'='*60}")
    if not all(ok):
        sys.exit(1)
