# Source (theory) paper — `main.tex`

Long-form source paper with full theory, algorithms, and all supporting experiments.

```
source/
├── paper/       # main.tex, references.bib, neurips_2026.sty
├── figures/     # all figures referenced by main.tex
├── code/        # algorithm, environments, and every experiment script
└── requirements.txt
```

## Build the paper

```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Figures are loaded from `../figures/` via `\graphicspath{{../figures/}}`;
update `\graphicspath` in `main.tex` if you move files around.

## Reproduce experiments

```bash
cd code
pip install -r ../requirements.txt
python run_all_experiments.py            # all experiments
python experiment1_synthetic_final.py    # one experiment
```

Figures are written to `exps/`/`figs/` locations (relative to the original
repo). Re-point the output paths inside each script or run from the root
repo if you prefer the previous layout.

## Figure → script map

| Figure (in `figures/`)                         | Producing script                             |
|------------------------------------------------|----------------------------------------------|
| experiment1_synthetic_phase.png                | experiment1_phase_grid.py, experiment1_synthetic_final.py |
| experiment2_subspace_recovery.png              | experiment2_subspace_recovery.py             |
| experiment3_probe_ablation.png                 | experiment3_probe_ablation.py                |
| experiment4_changepoint_recovery.png           | experiment4_changepoint_recovery.py          |
| experiment5_dimension_scaling.png              | experiment5_dimension_scaling.py             |
| experiment6_noise_robustness.png               | experiment6_noise_robustness.py              |
| experiment7_changepoint_frequency.png          | experiment7_changepoint_frequency.py         |
| experiment8_drift_speed.png                    | experiment8_drift_speed.py                   |
| experiment9_sota_benchmark.png                 | experiment9_sota_benchmark.py                |
| experiment_pendigits_operating_regime.png      | experiment_pendigits_operating_regime.py     |
| experiment_rank_misspec.png                    | experiment_rank_misspec.py                   |
| experiment_real_satimage_double_rings.png      | experiment_real_satimage_regime.py           |
| experiment_robustness_abc.png                  | experiment_robustness_abc.py                 |
| experiment_warfarin.png                        | plot_warfarin.py                             |
| ablation_warfarin_random_subspace.png          | ablation_warfarin_random_subspace.py         |
| satimage_wincount.png                          | satimage_final_plots.py                      |
