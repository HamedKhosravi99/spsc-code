# SPSC Experiment Code

Code for reproducing all experiments in:

> **Single-Play Subspace-Calibrated Optimism for Piecewise-Stationary Low-Rank Bandits**
> NeurIPS 2026 submission

## Setup

```bash
pip install -r requirements.txt
```

Python 3.9+ required. Dependencies: NumPy, SciPy, Matplotlib, scikit-learn.

## Paper-to-Code Mapping

Every figure and table with experimental data in the paper is listed below with the script that generates it.

### Main Paper (Section 6)

| # | Paper Reference | Script | Output |
|---|-----------------|--------|--------|
| 1 | Fig 1: Synthetic phase transition | `experiment1_main_benchmark.py` (data) | `experiment1_main_benchmark.png` |
| 1 | Fig 1: Phase-transition contour | `experiment1_final_figure.py` (plot) | `experiment1_synthetic_phase.png` |
| 2 | Table 1: Covertype multi-baseline | `experiment_covertype.py` | `experiment_covertype.png` + printed tables |
| 3 | Table 6 + Fig 11: Warfarin dosing | `experiment_real_bandit.py` (data) + `plot_warfarin.py` (plot) | `experiment_warfarin.png` |
| 4 | Fig 7: Robustness A/B/C | `experiment_robustness_abc.py` | `experiment_robustness_abc.png` |

### Appendix: Regime Characterization

| # | Paper Reference | Script | Output |
|---|-----------------|--------|--------|
| 3 | Fig 5: Pendigits regime | `experiment_pendigits_operating_regime.py` | `experiment_pendigits_operating_regime.png` |
| 4 | Fig 6: Satimage 7-method | `experiment_real_satimage_regime.py` | `experiment_real_satimage_double_rings.png` |
| - | Fig 10: Satimage aggregate | `satimage_final_plots.py` | `satimage_wincount.png` |

### Appendix: Mechanism Validation

| # | Paper Reference | Script | Output |
|---|-----------------|--------|--------|
| 5 | Fig 4: Probe-rate ablation | `experiment3_probe_ablation.py` | `experiment3_probe_ablation.png` |
| 6 | Fig 8: Subspace recovery rate | `experiment2_subspace_recovery.py` | `experiment2_subspace_recovery.png` |
| 7 | Fig 9: Change-point adaptation | `experiment4_changepoint_recovery.py` | `experiment4_changepoint_recovery.png` |
| 8 | Fig 10: Dimension scaling | `experiment5_dimension_scaling.py` | `experiment5_dimension_scaling.png` |

### Appendix: Robustness and Sensitivity

| # | Paper Reference | Script | Output |
|---|-----------------|--------|--------|
| 9-11 | Fig 7: Variance / cross-corr / coverage | `experiment_robustness_abc.py` | `experiment_robustness_abc.png` |
| - | Fig 7b + Table 3: Rank misspecification | `experiment_rank_misspec.py` | `experiment_rank_misspec.png` |
| 12 | Fig + Table: Noise robustness | `experiment6_noise_robustness.py` | `experiment6_noise_robustness.png` |
| 13 | Fig + Table: Changepoint frequency | `experiment7_changepoint_frequency.py` | `experiment7_changepoint_frequency.png` |
| 14 | Fig + Table: Drift speed | `experiment8_drift_speed.py` | `experiment8_drift_speed.png` |

### Appendix: SOTA and Full Tables

| # | Paper Reference | Script | Output |
|---|-----------------|--------|--------|
| 15 | Fig + Table: SOTA benchmark | `experiment9_sota_benchmark.py` | `experiment9_sota_benchmark.png` |
| 16 | Tables 4-7: Covertype full | `experiment_covertype.py` | Printed tables |

## File Inventory

### Core (2 files)

| File | Description |
|------|-------------|
| `algorithm.py` | SPSC Algorithm 1, LinUCB, Oracle-LinUCB, `K_inverse` operator |
| `environment.py` | Synthetic `LowRankLDSEnvironment` |

### Dataset Environments (5 files)

| File | Used By | Dataset |
|------|---------|---------|
| `covertype_environment.py` | `experiment_covertype.py` | UCI Covertype (semi-synthetic) |
| `real_covtype_environment_v2.py` | `experiment_rank_misspec.py` | Covertype (variable d) |
| `real_pendigits_environment.py` | `experiment_pendigits_operating_regime.py` | UCI Pendigits |
| `real_satimage_environment.py` | `experiment_real_satimage_regime.py` | UCI Satimage |
| `warfarin_environment.py` | `experiment_real_bandit.py` | Warfarin clinical dosing (d=93) |

All UCI datasets auto-download via `sklearn.datasets`. No manual download needed.

### Experiment Scripts (18 files)

See Paper-to-Code Mapping above.

### Utilities (3 files)

| File | Description |
|------|-------------|
| `run_all_experiments.py` | Batch runner (`--main`, `--synthetic`, `--real` flags) |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |

## Running Experiments

```bash
# Run everything
python run_all_experiments.py

# Main paper only (Exp 1-4)
python run_all_experiments.py --main

# Synthetic experiments only
python run_all_experiments.py --synthetic

# Real-data experiments only
python run_all_experiments.py --real

# Individual experiment
python experiment6_noise_robustness.py
```

## Algorithm

`algorithm.py` implements:

- **SPSC_Algorithm1**: Algorithm 1 from the paper. Single-play probing with K-inverse lifted estimation, windowed ridge regression in the learned r-dimensional subspace.
- **LinUCB**: Ambient-space ridge UCB (Abbasi-Yadkori et al., 2011).
- **OracleLinUCB**: UCB with oracle subspace knowledge (performance ceiling).

Nonstationary baselines (D-LinUCB, SW-LinUCB, Restart-LinUCB, LowRank-Reward) are implemented within individual experiment scripts.

## Reproducibility

- All experiments use explicit random seeds (default: 10 seeds; SOTA benchmark: 30 seeds).
- NumPy 1.x was used for the paper. NumPy 2.x produces different RNG streams.
- Qualitative conclusions are stable across platforms.
