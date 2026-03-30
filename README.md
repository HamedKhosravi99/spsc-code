# Single-Play Subspace-Aware Control — Simulation Code

Simulation code for the paper
**"Single-Play Subspace-Aware Control with Windowed r-Dimensional Exploitation"**

---

## Structure

```
Code/
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
├── experiment1_notebook.ipynb      # Google Colab notebook for Experiment 1
├── run_all_experiments.py          # Runs experiments 1-5 in sequence
├── requirements.txt                # Python dependencies
└── .gitignore
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

**Google Colab:** Open `experiment1_notebook.ipynb` in Colab, upload `algorithm.py` + `environment.py`, and run cells top to bottom.

**All synthetic experiments (1-5):**
```bash
python run_all_experiments.py
```

Each experiment prints a results table and saves a `.png` figure in the same directory.

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

### Semi-Synthetic Benchmarks (Real Datasets)

| File | Dataset | Methods | Grid | Seeds | Runtime |
|---|---|---|---|---|---|
| `experiment_covertype.py` | UCI Covertype | 3 | fixed | 10 | ~10 min |
| `experiment_shuttle.py` | UCI Shuttle | 5 | fixed | 10 | ~5 min |
| `experiment_phase_diagram.py` | UCI Pendigits | 3 | d x r = 6x4 | 15 | ~30 min |
| `experiment_satimage.py` | UCI Satimage | 7 | d x r = 4x4 | 15 | ~60 min |

**Satimage baselines (7 methods):**
1. SPSC Algorithm 1 (ours)
2. LinUCB (Abbasi-Yadkori+ 2011)
3. D-LinUCB — discounted ridge (Russac+ 2019)
4. SW-LinUCB — sliding window (Cheung+ 2019)
5. Restart-LinUCB — periodic restart (Auer+ 2019)
6. LowRank-Reward-UCB — subspace from rewards (LowESTR spirit)
7. Oracle-LinUCB — known subspace (unattainable ceiling)

### Extending Seeds

To extend from 5 to 15 seeds (loads cached 5-seed results, runs 10 more, combines):
```bash
python extend_pendigits_seeds.py
python extend_satimage_seeds.py
```

### Regenerating Plots from Cache

```bash
python experiment_phase_diagram.py --replot
python satimage_final_plots.py
python visualize_phase_extras.py
```

---

## Key Results

| Benchmark | SPSC wins | Avg regret reduction |
|---|---|---|
| Synthetic (Exp 1) | SPSC/LinUCB = 0.59 | 41% |
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
This gives the unbiased lifted estimator `E[K_inv(s_t u_t u_t^T)] = theta_t theta_t^T`.

---

## Environment Parameters (Synthetic)

| Parameter | Value | Role |
|---|---|---|
| `sigma_eta` | 0.04 | LDS innovation std |
| `spectral_radius` | 0.99 | AR(1) coefficient; correlation time ~100 |
| `sigma_eps` | 0.3 | Observation noise std |
| `n_actions` | 80 | Fresh unit-sphere arms per round |
