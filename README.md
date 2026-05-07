# SPSC: Single-Play Subspace-Calibrated Optimism

Reference implementation of **SPSC** and **SPSC-Adaptive** for
piecewise low-rank linear contextual bandits, together with scripts
that reproduce every experiment in the accompanying paper.

The setting is linear contextual bandits in which the reward
parameter lies in a piecewise-constant rank-$r$ subspace that shifts
at unknown change points: stationary low-rank bandits exploit the
rank but break under any subspace change, and non-stationary linear
bandits adapt to drift but pay the ambient $\widetilde O(d\sqrt T)$
rate. SPSC interleaves isotropic probes with windowed projected
ridge-UCB exploitation in the learned $r$-dimensional subspace;
SPSC-Adaptive detects segment boundaries online via a CUSUM-style
two-window comparison.

## Repository layout

```
.
├── code/
│   ├── algorithm.py                       # SPSC / SPSC-Adaptive / baselines
│   ├── environments/                      # benchmark environments
│   ├── experiment_*.py                    # one script per benchmark / sweep
│   └── ablation_warfarin_random_subspace.py
└── requirements.txt                       # Python dependencies
```

## Installation

```bash
pip install -r requirements.txt
```

NumPy / SciPy / Matplotlib only; no GPU or external ML libraries
required.

## Reproducing the experiments

```bash
# Synthetic phase-transition grid
python code/experiment_synthetic_extended.py

# UCI / MovieLens benchmarks
python code/experiment_pendigits_extended.py
python code/experiment_satimage_extended.py
python code/experiment_covertype_grid.py
python code/experiment_mnist_grid.py
python code/experiment_fashion_mnist_grid.py
python code/experiment_movielens_real_grid.py

# Clinical
python code/experiment_warfarin_extended.py
python code/experiment_vancomycin_extended.py
python code/ablation_warfarin_random_subspace.py

# Production logs
python code/experiment_openbandit.py

# Comparison with stationary low-rank methods
python code/experiment_boss_jedra_grid.py

# Sensitivity / robustness
python code/experiment_rank_misspec.py
python code/experiment_assumption_violation.py
python code/experiment_robustness_abc.py
python code/experiment_oracle_quality_extended.py
```

Each script writes per-seed JSON results into `code/results/`.

## Algorithm summary

- **Identification boundary.** Three probe-side conditions, known
  noise variance, bounded state-noise coupling, and full-dimensional
  probe support, are individually necessary (in the
  unrestricted-second-moment scope) and jointly sufficient for
  recovering the rank-$r$ subspace from quadratic functionals of
  scalar rewards.
- **SPSC / SPSC-Adaptive.** Interleaves isotropic probes with
  windowed projected ridge-UCB exploitation in the learned
  $r$-dimensional subspace; SPSC-Adaptive detects segment boundaries
  online via a CUSUM-style two-window comparison.
- **Costed dynamic regret.**
  $\widetilde O(r\sqrt{T}) + \widetilde O(T^{2/3}) + O(W V_{\mathrm{in}})$,
  replacing the ambient $\widetilde O(d\sqrt T)$ rate with the
  intrinsic rank.

## Benchmarks covered

Synthetic phase-transition grid; UCI/MovieLens (Covertype, Pendigits,
Satimage, MNIST, Fashion-MNIST, MovieLens); clinical (Warfarin,
Vancomycin); a small-$d$ piecewise-stationary stress test; Open
Bandit production logs.
