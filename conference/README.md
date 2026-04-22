# Conference paper — `conf.tex` (NeurIPS 2026)

Short-form NeurIPS submission derived from `main.tex`. Self-contained proofs
in the appendix; per-dataset per-cell tables are built from `cells.json` via
`build_appendix_tables.py`.

```
conference/
├── paper/       # conf.tex + .pdf + bibliography + style + cells.json + appendix tables
├── figures/     # all figures referenced by conf.tex
├── code/        # every experiment script (same tree as source/code)
└── requirements.txt
```

## Build the paper

```bash
cd paper
pdflatex conf.tex
bibtex conf
pdflatex conf.tex
pdflatex conf.tex
```

The paper references figures via `\graphicspath{{../figs/}{../exps/}}` in the
original layout. After this reorganisation the simplest fix is to replace that
line with `\graphicspath{{../figures/}}` — all referenced figures now live in
one place.

### Regenerating the per-cell appendix tables

```bash
cd paper
python build_appendix_tables.py  # reads cells.json, writes appendix_tables.tex
```

## Reproduce experiments

```bash
cd code
pip install -r ../requirements.txt
python experiment_covertype_grid.py     # one cell-grid (UCB-family)
python experiment_covertype_lints.py    # LinTS + SW-LinTS on the same grid
```

Raw results are written to `code/results/*.json`. To refresh `cells.json`
after rerunning, see `paper/build_appendix_tables.py` for the data shape it
expects (one cell per (d,r) with method → [mean, se] arrays).

## Key paper artefacts

| File                        | Purpose                                              |
|-----------------------------|------------------------------------------------------|
| `paper/conf.tex`            | NeurIPS submission source                            |
| `paper/cells.json`          | Aggregated per-cell mean/SE for every dataset        |
| `paper/appendix_tables.tex` | Generated per-dataset tables (do not edit by hand)   |
| `paper/results_raw.txt`     | Raw stdout dumps used to populate `cells.json`       |
| `paper/build_appendix_tables.py` | Generator: `cells.json` → `appendix_tables.tex` |
