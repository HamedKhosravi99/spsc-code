# Anonymous supplementary code and figures

This archive contains the implementation, experiment scripts, cached
results, and rendered figures supporting the submission. It is
provided anonymously for review.

## Contents

```
anonymous-supp/
├── README.md
├── requirements.txt
├── code/                    # algorithm + experiments (Python)
│   ├── algorithm.py             # SPSC and SPSC-Adaptive
│   ├── environments/            # one module per benchmark
│   ├── results/                 # cached JSON outputs (re-runs reproducible)
│   ├── experiment[1-9]_*.py     # synthetic-figure experiments
│   ├── experiment_<dataset>_*.py # real-data experiments per benchmark
│   ├── plot_*.py                # plotting helpers
│   ├── results_io.py            # JSON persistence helper
│   └── __init__.py
└── figures/                 # the 14 PNG figures used in the paper
```

## Setup

```bash
pip install -r requirements.txt
```

Tested with NumPy 1.x, SciPy 1.10+, matplotlib 3.7+, scikit-learn 1.2+,
on a single 16-core CPU machine. No GPU is required.

## Figures: one script per figure

| Figure (`figures/`)                              | Generator (`code/`)                             |
|--------------------------------------------------|-------------------------------------------------|
| `experiment1_synthetic_phase.png`                | `experiment1_phase_grid.py`                     |
| `experiment2_subspace_recovery.png`              | `experiment2_subspace_recovery.py`              |
| `experiment3_probe_ablation.png`                 | `experiment3_probe_ablation.py`                 |
| `experiment4_changepoint_recovery.png`           | `experiment4_changepoint_recovery.py`           |
| `experiment6_noise_robustness.png`               | `experiment6_noise_robustness.py`               |
| `experiment7_changepoint_frequency.png`          | `experiment7_changepoint_frequency.py`          |
| `experiment8_drift_speed.png`                    | `experiment8_drift_speed.py`                    |
| `experiment9_sota_benchmark.png`                 | `experiment9_sota_benchmark.py`                 |
| `experiment_pendigits_extended.png`              | `experiment_pendigits_extended.py` + `plot_pendigits_extended.py` |
| `experiment_rank_misspec.png`                    | `experiment_rank_misspec.py`                    |
| `experiment_real_satimage_double_rings.png`      | `experiment_real_satimage_regime.py`            |
| `experiment_robustness_abc.png`                  | `experiment_robustness_abc.py`                  |
| `experiment_synthetic_extended.png`              | `experiment_synthetic_extended.py`              |
| `ablation_warfarin_random_subspace.png`          | `ablation_warfarin_random_subspace.py`          |

## Tables: one source per table

| Table in the paper                       | Source script                                      |
|------------------------------------------|----------------------------------------------------|
| Warfarin representative cell             | `experiment_warfarin_extended.py`                  |
| Vancomycin per-rank sweep                | `experiment_vancomycin_extended.py`                |
| BOSS/Jedra adapted-stationary grid       | `experiment_boss_jedra_grid.py` (and `experiment_boss_jedra.py`) |
| Real-data summary (Covertype, Pendigits, Satimage, MNIST, Fashion-MNIST, MovieLens) | `experiment_<dataset>_grid.py` per dataset |
| Sensitivity / assumption-violation master| `experiment_assumption_violation.py` + `experiment_segmentation_sensitivity.py` |
| Russac benchmark / Open Bandit           | `experiment_openbandit.py`                         |
| Per-cell appendix tables                 | populated from `code/results/*.json`               |

## Reproducing a single experiment

```bash
cd code

# Synthetic phase-transition figure
python experiment1_phase_grid.py

# A real-data benchmark (writes JSON to code/results/)
python experiment_pendigits_extended.py

# A clinical benchmark
python experiment_warfarin_extended.py
```

Cached JSON outputs in `code/results/` are sufficient to rebuild the
paper's tables without re-running the experiments.

## Reproducibility notes

* Random seeds are fixed inside each script. NumPy 2.x changes the RNG
  stream relative to NumPy 1.x; reference results were generated under
  NumPy 1.x, so we recommend NumPy < 2 for byte-identical replication.
* All baselines (LinUCB, D-LinUCB, SW-LinUCB, Restart-LinUCB, LowOFUL,
  VOFUL, LowRank-Reward, LinTS, SW-LinTS, BOSS-adapted, Jedra-adapted,
  Oracle-LinUCB) are implemented in `code/algorithm.py`.
* Subspace-aware baselines (LowOFUL, VOFUL) consume the same refreshed
  projector $\widehat U$ as the proposed method (recomputed every 20
  rounds after a 30-round warm-up); see `algorithm.py` for details.

## License

Code and figures in this archive are released for review purposes
under an open-source license to be specified in the camera-ready
version.
