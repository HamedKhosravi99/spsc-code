# Journal paper — `journal.tex`

Journal-version draft (targeting JMLR / Bernoulli). Theory + a small set of
theory-validating experiments. The code here is self-contained and does **not**
depend on the big `exps/` tree used by the source/conference papers.

```
journal/
├── paper/       # journal.tex + .pdf + references.bib
├── figures/     # journal_exp*.png referenced by journal.tex
├── code/        # core.py + 4 exp*.py scripts + run_all.py
└── requirements.txt
```

## Build the paper

```bash
cd paper
pdflatex journal.tex
bibtex journal
pdflatex journal.tex
pdflatex journal.tex
```

Figures are loaded via `\graphicspath{{../figs/}}` in the original layout;
change to `\graphicspath{{../figures/}}` in `journal.tex` to match this
reorganised tree.

## Reproduce experiments

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

## Figure → script map

| Figure                              | Producing script            |
|-------------------------------------|-----------------------------|
| journal_exp1_minimax_recovery.png   | exp1_minimax_recovery.py    |
| journal_exp2_probe_cost.png         | exp2_probe_cost.py          |
| journal_exp4_identification.png     | exp4_identification.py      |
| journal_exp5_allocation.png         | exp5_allocation.py          |
| journal_exp5_drift_regime.png       | *(missing — not yet generated; referenced by `journal.tex`)* |
