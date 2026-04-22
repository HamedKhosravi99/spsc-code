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
│   ├── paper/    # conf.tex, appendix_tables.tex, references.bib, cells.json, ...
│   ├── code/     # experiment scripts for the conference paper
│   ├── figures/  # all figures referenced by conf.tex
│   └── requirements.txt
│
├── journal/      # Journal-length paper (JMLR / Bernoulli target)
│   ├── paper/    # journal.tex, references.bib
│   ├── code/     # core.py + exp*.py scripts (self-contained)
│   ├── figures/  # figures referenced by journal.tex
│   └── requirements.txt
│
├── source/       # Long-form source paper (all theory + full experiment set)
│   ├── paper/    # main.tex, references.bib, neurips_2026.sty
│   ├── code/     # algorithm, environments, every experiment script
│   ├── figures/  # figures referenced by main.tex
│   └── requirements.txt
│
└── README.md     # this file
```

Each subfolder has its own `README.md` with build instructions and a
figure-to-script mapping.

## Main paper files

| Version    | Main `.tex`            | Appendix                        | Bibliography          |
|------------|------------------------|---------------------------------|-----------------------|
| Conference | `conference/paper/conf.tex`    | in-file + `appendix_tables.tex` | `references.bib`      |
| Journal    | `journal/paper/journal.tex`    | in-file                         | `references.bib`      |
| Source     | `source/paper/main.tex`        | in-file                         | `references.bib`      |

Build any of them with the standard LaTeX pipeline from inside the
corresponding `paper/` directory:

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
  allocation, and model-class separation. Experiments are a small
  theory-validating set.
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
# or individual experiment scripts — see the per-folder README
```

Datasets download automatically (`sklearn.datasets` / script caches).

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
