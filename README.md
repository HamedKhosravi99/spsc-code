# Low-Rank Bandits

Research repository for

> **Optimism on a Moving Subspace: Priced-Probe Identification for Piecewise Low-Rank Bandits**

The project studies bandit problems in which the reward vector lies in a
low-rank subspace that can jump at unknown change points, and introduces
**SPSC** (Single-Play Subspace-Calibrated Optimism) and its detector-based
variant **SPSC-Adaptive**.

The repository is split into three self-contained versions of the work —
a short conference submission, a long journal draft, and the original
long-form source paper — each with its own paper, code, and figures.

## Repository layout

```
lowrank-bandits/
├── conference/   # NeurIPS 2026 short paper
│   ├── conf.tex, appendix_tables.tex, references.bib, cells.json, ...
│   ├── code/     # experiment scripts for the conference paper
│   ├── figures/  # all figures referenced by conf.tex
│   └── requirements.txt
│
├── journal/      # Journal-length paper (JMLR / Bernoulli target)
│   ├── journal.tex, references.bib
│   ├── code/     # core.py + exp*.py scripts (self-contained)
│   ├── figures/  # figures referenced by journal.tex
│   └── requirements.txt
│
├── source/         # Long-form source paper (all theory + full experiment set)
│   ├── paper/      # main.tex, references.bib, neurips_2026.sty
│   ├── code/       # algorithm, environments, every experiment script
│   ├── figures/    # figures referenced by main.tex
│   └── requirements.txt
│
├── anonymous-supp/ # Anonymized code + figures snapshot for review
│   ├── code/       # algorithm + experiments (Python)
│   ├── figures/    # PNG figures used in the paper
│   └── requirements.txt
│
└── README.md       # this file
```

## Main paper files

| Version    | Main `.tex`                    | Appendix                        | Bibliography     |
|------------|--------------------------------|---------------------------------|------------------|
| Conference | `conference/conf.tex`          | in-file + `appendix_tables.tex` | `references.bib` |
| Journal    | `journal/journal.tex`          | in-file                         | `references.bib` |
| Source     | `source/paper/main.tex`        | in-file                         | `references.bib` |

Build any of them with the standard LaTeX pipeline from inside the
version directory (for `source/`, from inside `source/paper/`):

```bash
pdflatex <name>.tex
bibtex   <name>
pdflatex <name>.tex
pdflatex <name>.tex
```

## What is in each version

- **Conference (`conf.tex`)** — SPSC + SPSC-Adaptive, four headline
  results (main regret bound, rank-adaptive corollary, adaptive-SPSC
  regret, class-conditional lower bound), plus a compact proofs
  appendix. Experiments cover the synthetic phase-transition benchmark,
  six real-data grids (Covertype, Pendigits, Satimage, MNIST,
  Fashion-MNIST, MovieLens), Warfarin clinical dosing, a BOSS/Jedra
  comparison, and rank / probe-rate sensitivity studies.
- **Journal (`journal.tex`)** — same algorithm, full theory: finite-sample
  subspace recovery, variance-adaptive concentration, instance-dependent
  bounds, ambient-space reference bound, expected / anytime / doubling
  refinements, minimax subspace-recovery lower bound, KL-based ETC
  lower bounds, matching `Ω(c^(1/3) T^(2/3))` in `Π_HP`, optimal probe
  allocation, and model-class separation. Experiments are a small,
  self-contained theory-validating set under `journal/code/`.
- **Source (`main.tex`)** — the long-form draft that both derivative
  versions were extracted from; kept for provenance and for the full
  experimental library.

## Reproducing experiments

From inside the chosen version:

```bash
cd <conference|journal|source>
pip install -r requirements.txt
cd code
python run_all_experiments.py     # source
python run_all.py                 # journal
# or individual experiment scripts — see the per-version sections below
```

Datasets download automatically (`sklearn.datasets` / script caches).

---

## Conference (`conference/`)

Self-contained source for the SPSC NeurIPS 2026 submission: paper,
figures, experiment scripts, and cached JSON results.

```
conference/
├── conf.tex                   # NeurIPS submission source
├── appendix_tables.tex        # generated per-dataset appendix tables
├── build_appendix_tables.py   # generator: cells.json → appendix_tables.tex
├── cells.json                 # aggregated per-cell mean/SE for every dataset
├── checklist.tex              # NeurIPS submission checklist
├── neurips_2026.sty           # NeurIPS 2026 style
├── references.bib             # bibliography
├── figures/                   # the 14 .png files referenced by conf.tex
├── code/                      # experiment scripts and helpers
│   ├── algorithm.py            # SPSC and SPSC-Adaptive implementations
│   ├── environments/           # per-dataset bandit environments
│   ├── results/                # cached JSON outputs (pre-computed for tables)
│   ├── experiment[1-9]_*.py    # synthetic-figure experiments
│   ├── experiment_<dataset>_*.py # real-data experiments per benchmark
│   ├── plot_*.py               # plotting helpers
│   └── run_all_experiments.py  # orchestrator
└── requirements.txt
```

`conf.tex` reads figures from `figures/` via `\graphicspath{{figures/}}`.

### Regenerating the per-cell appendix tables

`appendix_tables.tex` is auto-generated from `cells.json` (the
aggregated per-cell mean/SE for every dataset; the `*_lints.json`
files in `code/results/` cover the LinTS rows):

```bash
python build_appendix_tables.py   # reads cells.json, writes appendix_tables.tex
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
| Per-cell `tab:app-*`             | `cells.json` → `build_appendix_tables.py` |

### Common workflow

```bash
# Run a single experiment (writes JSON to code/results/ or PNG to figures/)
cd code
python experiment_pendigits_extended.py

# Refresh appendix tables after re-running grid experiments
cd .. && python build_appendix_tables.py
```

### Key paper artefacts

| File                        | Purpose                                              |
|-----------------------------|------------------------------------------------------|
| `conf.tex`                  | NeurIPS submission source                            |
| `references.bib`            | Bibliography                                         |
| `neurips_2026.sty`          | NeurIPS 2026 style                                   |
| `cells.json`                | Aggregated per-cell mean/SE for every dataset        |
| `appendix_tables.tex`       | Generated per-dataset tables (do not edit by hand)   |
| `build_appendix_tables.py`  | Generator: `cells.json` → `appendix_tables.tex`      |

---

## Journal (`journal/`)

Journal-version draft (targeting JMLR / Bernoulli). Theory + a small
set of theory-validating experiments. The code here is self-contained
and does **not** depend on the big `exps/` tree used by the
source/conference papers.

```
journal/
├── journal.tex      # main paper source
├── references.bib   # bibliography
├── figures/         # journal_exp*.png referenced by journal.tex
├── code/            # core.py + 4 exp*.py scripts + run_all.py
└── requirements.txt
```

Figures are loaded from `figures/` via `\graphicspath{{figures/}}` in
`journal.tex`.

### Reproduce experiments

```bash
cd code
pip install -r ../requirements.txt
python run_all.py            # runs all four experiments
# or individually:
python exp1_minimax_recovery.py
python exp2_probe_cost.py
python exp4_identification.py
python exp5_allocation.py
```

### Figure → script map

| Figure                              | Producing script            |
|-------------------------------------|-----------------------------|
| journal_exp1_minimax_recovery.png   | exp1_minimax_recovery.py    |
| journal_exp2_probe_cost.png         | exp2_probe_cost.py          |
| journal_exp4_identification.png     | exp4_identification.py      |
| journal_exp5_allocation.png         | exp5_allocation.py          |
| journal_exp5_drift_regime.png       | *(missing — not yet generated; referenced by `journal.tex`)* |

---

## Status

- **Conference** — submitted draft for NeurIPS 2026. Main body fits in
  10 pages; full appendix (proofs + per-cell tables + sensitivity
  studies) compiles cleanly.
- **Journal** — draft in progress. Theory is essentially complete;
  `journal_exp5_drift_regime.png` is the one remaining figure to
  generate.
- **Source** — frozen long-form version used as the reference point
  for both the conference and journal splits.

## License

MIT
