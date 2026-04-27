# SPSC — NeurIPS 2026 conference submission

Self-contained source for the SPSC (Single-Play Subspace-Calibrated
Optimism) NeurIPS submission: paper, figures, experiment scripts, and
cached JSON results.

## Layout

```
conference/
├── paper/         # conf.tex + .bbl, bibliography, style, appendix tables
├── figures/       # the 14 .png files referenced by conf.tex
├── code/          # experiment scripts and helpers
│   ├── algorithm.py            # SPSC and SPSC-Adaptive implementations
│   ├── environments/           # per-dataset bandit environments
│   ├── results/                # cached JSON outputs (pre-computed for tables)
│   ├── experiment[1-9]_*.py    # synthetic-figure experiments
│   ├── experiment_<dataset>_*.py # real-data experiments per benchmark
│   ├── plot_*.py               # plotting helpers
│   └── run_all_experiments.py  # orchestrator
├── requirements.txt
└── README.md      # this file
```

## Build the paper

```bash
cd paper
pdflatex conf.tex
bibtex conf
pdflatex conf.tex
pdflatex conf.tex
```

`conf.tex` reads figures from `../figures/` via
`\graphicspath{{../figures/}}`. The bibliography lives in
`references.bib`; the NeurIPS 2026 style file is `neurips_2026.sty`.

### Regenerating the per-cell appendix tables

`appendix_tables.tex` is auto-generated from `cells.json` (the
aggregated per-cell mean/SE for every dataset; the `*_lints.json`
files in `code/results/` cover the LinTS rows):

```bash
cd paper
python build_appendix_tables.py   # reads cells.json, writes appendix_tables.tex
```

## Reproduce experiments

```bash
cd code
pip install -r ../requirements.txt
```

### Figures used in the paper (one script per figure)

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

### Body tables (one script per data source)

| Table in `conf.tex`              | Source script                       |
|----------------------------------|-------------------------------------|
| `tab:warfarin_body`              | `experiment_warfarin_extended.py`   |
| `tab:vancomycin_body`            | `experiment_vancomycin_extended.py` |
| `tab:boss_jedra_grid`            | `experiment_boss_jedra_grid.py` (and `experiment_boss_jedra.py`) |
| `tab:realdata`                   | per-dataset `experiment_*_grid.py` (Covertype, Pendigits, Satimage, MNIST, Fashion-MNIST, MovieLens) |

### Appendix tables

| Table                            | Source                              |
|----------------------------------|-------------------------------------|
| `tab:assumption_master`          | `experiment_assumption_violation.py` + `experiment_segmentation_sensitivity.py` |
| `tab:vancomycin_full`            | `experiment_vancomycin_extended.py` |
| Russac benchmark / Open Bandit   | `experiment_openbandit.py`          |
| Per-cell `tab:app-*`             | `cells.json` → `build_appendix_tables.py` (in `paper/`) |

### Common workflow

```bash
# Run a single experiment (writes JSON to code/results/ or PNG to figures/)
python experiment_pendigits_extended.py

# Refresh appendix tables after re-running grid experiments
cd ../paper && python build_appendix_tables.py
```

## Key paper artefacts

| File                              | Purpose                                              |
|-----------------------------------|------------------------------------------------------|
| `paper/conf.tex`                  | NeurIPS submission source                            |
| `paper/references.bib`            | Bibliography                                         |
| `paper/neurips_2026.sty`          | NeurIPS 2026 style                                   |
| `paper/cells.json`                | Aggregated per-cell mean/SE for every dataset        |
| `paper/appendix_tables.tex`       | Generated per-dataset tables (do not edit by hand)   |
| `paper/build_appendix_tables.py`  | Generator: `cells.json` → `appendix_tables.tex`      |
| `paper/conf.bbl`                  | Pre-built bibliography (handy for arXiv-style submissions) |
