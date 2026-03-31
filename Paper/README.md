# Single-Play Subspace-Aware Control with Windowed Low-Dimensional Exploitation

**NeurIPS 2026 Submission**

Paper and simulation code for
*"Single-Play Subspace-Aware Control with Windowed Low-Dimensional Exploitation"*

---

## Paper

| File | Description |
|---|---|
| `neuripslowrank.tex` | Main paper (LaTeX source) |
| `neurips_2026.sty` | NeurIPS 2026 official style file |
| `references.bib` | Bibliography (37 entries) |

**Compile:**
```bash
pdflatex neuripslowrank
bibtex neuripslowrank
pdflatex neuripslowrank
pdflatex neuripslowrank
```

---

## Code Structure

```
├── algorithm.py                    # SPSC Algorithm 1, LinUCB, OracleLinUCB
├── environment.py                  # Synthetic piecewise-stationary low-rank LDS bandit
├── covertype_environment.py        # Covertype dataset environment
├── criteo_environment.py           # Criteo dataset environment
├── movielens_environment.py        # MovieLens dataset environment
│
├── experiment1_main_benchmark.py   # Exp 1: SPSC vs LinUCB vs Oracle (synthetic)
├── experiment2_subspace_recovery.py# Exp 2: Subspace estimation rate
├── experiment3_probe_ablation.py   # Exp 3: Probe-rate sweep
├── experiment4_changepoint_recovery.py # Exp 4: Change-point adaptation
├── experiment5_dimension_scaling.py# Exp 5: Dimension scaling
├── experiment6_noise_robustness.py # Exp 6: Noise robustness sweep
├── experiment7_changepoint_frequency.py # Exp 7: Changepoint frequency sweep
├── experiment8_drift_speed.py      # Exp 8: Drift speed (spectral radius) sweep
├── experiment9_sota_benchmark.py   # Exp 9: SOTA comparison (Russac et al.)
│
├── experiment_covertype.py         # Covertype benchmark
├── experiment_shuttle.py           # Shuttle benchmark (5 methods)
├── experiment_phase_diagram.py     # Pendigits phase diagram (SPSC operating regime)
├── experiment_satimage.py          # Satimage benchmark (7 methods)
├── satimage_final_plots.py         # Double rings, dot-strip, win-count plots
├── visualize_phase_extras.py       # 3D surface, rings, bubble from cached data
├── extend_pendigits_seeds.py       # Extend Pendigits from 5 to 15 seeds
├── extend_satimage_seeds.py        # Extend Satimage from 5 to 15 seeds
│
├── run_all_experiments.py          # Runs experiments 1-5 in sequence
└── requirements.txt                # Python dependencies
```

---

## Requirements

Python 3.9+ and:

```bash
pip install -r requirements.txt
```

---

## Quick Start

**Run Experiment 1 (simplest, ~5 min):**
```bash
python experiment1_main_benchmark.py
```

**All synthetic experiments (1-9):**
```bash
python run_all_experiments.py           # Experiments 1-5
python experiment6_noise_robustness.py  # ~10 min
python experiment7_changepoint_frequency.py  # ~10 min
python experiment8_drift_speed.py       # ~10 min
python experiment9_sota_benchmark.py    # ~15 min
```

Each experiment prints a results table and saves a `.png` figure.

---

## Experiments

### Synthetic Experiments

| # | File | What it tests | Setup | Runtime |
|---|---|---|---|---|
| 1 | `experiment1_main_benchmark.py` | SPSC vs LinUCB vs Oracle | d=4, r=1, K=4, T=6000, 10 seeds | ~5 min |
| 2 | `experiment2_subspace_recovery.py` | Subspace error decays as 1/sqrt(m) | d=4, r=1, 20 seeds | ~3 min |
| 3 | `experiment3_probe_ablation.py` | Probe-rate tradeoff sweep | probe_every in {5..300}, 10 seeds | ~10 min |
| 4 | `experiment4_changepoint_recovery.py` | Re-learning after segment boundaries | d=4, r=1, K=4 | ~5 min |
| 5 | `experiment5_dimension_scaling.py` | Low-rank benefit grows with d | d in {4,8,12}, r=2, 10 seeds | ~10 min |
| 6 | `experiment6_noise_robustness.py` | Noise-monotone SPSC advantage | sigma in {0.05..0.80}, 10 seeds | ~10 min |
| 7 | `experiment7_changepoint_frequency.py` | Margin vs segment count | K in {1..12}, 10 seeds | ~10 min |
| 8 | `experiment8_drift_speed.py` | Correlation-time phase transition | rho in {0.30..0.99}, 10 seeds | ~10 min |
| 9 | `experiment9_sota_benchmark.py` | SOTA comparison (6 methods) | d=2, r=1, sigma=1, 30 seeds | ~15 min |

### Semi-Synthetic Benchmarks (Real Datasets)

| File | Dataset | Methods | Grid | Seeds | Runtime |
|---|---|---|---|---|---|
| `experiment_covertype.py` | UCI Covertype | 3 | fixed | 10 | ~10 min |
| `experiment_shuttle.py` | UCI Shuttle | 5 | fixed | 10 | ~5 min |
| `experiment_phase_diagram.py` | UCI Pendigits | 3 | d x r = 6x4 | 15 | ~30 min |
| `experiment_satimage.py` | UCI Satimage | 7 | d x r = 4x4 | 15 | ~60 min |

---

## Key Results

| Benchmark | SPSC wins | Avg regret reduction |
|---|---|---|
| Synthetic (Exp 1) | SPSC/LinUCB = 0.59 | 41% |
| Noise sweep (Exp 6) | All 6 noise levels | 40-43% |
| SOTA benchmark (Exp 9) | Beats D-LinUCB, SW-LinUCB | 46.5% vs D-LinUCB |
| Shuttle (5 methods) | Beats all baselines | 8-12% |
| Pendigits (phase diagram) | 23/24 cells | 2-38% |
| Satimage (7 methods) | 13-16/16 cells vs each baseline | 6-24% |

---

## Algorithm Notes

### Buffer Reprojection
The exploitation buffer stores raw actions `x_s`. At each round, all buffered actions are reprojected with the current subspace estimate `U_hat`:
```python
z_s = U_hat.T @ x_s   # consistent basis for all window entries
```

### K-inverse Operator
For sphere probes `u = sqrt(d) * z/||z||`, `z ~ N(0, I_d)`:
```
K_inv(N) = (d+2)/(2d) * N - tr(N)/(2d) * I_d
```

---

## Environment Parameters (Synthetic)

| Parameter | Value | Role |
|---|---|---|
| `sigma_eta` | 0.04 | LDS innovation std |
| `spectral_radius` | 0.99 | AR(1) coefficient; correlation time ~100 |
| `sigma_eps` | 0.3 | Observation noise std |
| `n_actions` | 80 | Fresh unit-sphere arms per round |
