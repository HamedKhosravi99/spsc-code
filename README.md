# Catching a Moving Subspace: Low-Rank Bandits Beyond Stationarity

Conference submission of the SPSC paper. Studies linear contextual
bandits in which the reward parameter lies in a piecewise-constant
rank-$r$ subspace that shifts at unknown change points, and introduces
**SPSC** (Single-Play Subspace-Calibrated Optimism) and its
detector-based variant **SPSC-Adaptive**.

A separate journal-length version of the paper, with the full theory
and an extended experimental library, lives in a sibling repository.

## Repository layout

```
.
├── conf.tex                 # main paper
├── appendix_tables.tex      # per-cell tables included by conf.tex
├── checklist.tex            # NeurIPS responsibility checklist
├── neurips_2026.sty         # NeurIPS 2026 style file
├── references.bib           # bibliography
├── code/                    # experiment scripts (Python)
│   ├── algorithm.py         #   SPSC and SPSC-Adaptive implementations
│   ├── environments/        #   benchmark environments
│   └── experiment_*.py      #   one script per benchmark / sensitivity study
├── figures/                 # all figures referenced by conf.tex
└── requirements.txt         # Python dependencies for the code/
```

## Building the paper

From the repository root:

```bash
pdflatex conf.tex
bibtex   conf
pdflatex conf.tex
pdflatex conf.tex
```

(or simply `latexmk -pdf conf.tex`).

## Reproducing experiments

```bash
pip install -r requirements.txt
python code/experiment1_phase_grid.py        # synthetic phase-transition grid
python code/experiment_pendigits_extended.py # Pendigits operating-regime grid
python code/experiment_real_satimage_regime.py
python code/experiment_movielens_real_grid.py
python code/experiment_openbandit.py         # ZOZOTOWN / Open Bandit logs
python code/ablation_warfarin_random_subspace.py
python code/experiment_assumption_violation.py
python code/experiment_boss_jedra_grid.py
python code/experiment_rank_misspec.py
# (and so on for the remaining experiment_*.py scripts)
```

Each script writes per-seed JSON results into `code/results/`.

## Highlights

- **Identification boundary (Theorem 2.2).** Three probe-side
  conditions, known noise variance, bounded state-noise coupling, and
  full-dimensional probe support, are individually necessary (in the
  unrestricted-second-moment scope) and jointly sufficient for
  recovering the rank-$r$ subspace from quadratic functionals of
  scalar rewards.
- **Algorithm (SPSC, SPSC-Adaptive).** Interleaves isotropic probes
  with windowed projected ridge-UCB exploitation in the learned
  $r$-dimensional subspace; SPSC-Adaptive detects segment boundaries
  online via a CUSUM-style two-window comparison.
- **Costed dynamic regret (Theorem 4.1).**
  $\widetilde O(r\sqrt{T}) + \widetilde O(T^{2/3}) + O(W V_{\mathrm{in}})$,
  replacing the ambient $\widetilde O(d\sqrt{T})$ rate with the
  intrinsic rank.
- **Experiments (eleven benchmarks).** Synthetic phase-transition
  grid; UCI/MovieLens (Covertype, Pendigits, Satimage, MNIST,
  Fashion-MNIST, MovieLens); clinical (Warfarin, Vancomycin); the
  Russac small-$d$ stress test; Open Bandit production logs.
