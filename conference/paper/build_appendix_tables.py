import json
data = json.load(open('cells.json'))

LABEL = {
    "Oracle LinUCB":            (r"Oracle",    "oracle"),
    "SPSC Alg.1 (ours)":        (r"\textbf{SPSC}",    "ours"),
    "SPSC Adaptive (ours)":     (r"\textbf{SPSC-Adp}",    "ours"),
    "LowOFUL (Jun+ '19)":       (r"LowOFUL",   "comp"),
    "VOFUL (Kim+ '22)":         (r"VOFUL",     "comp"),
    "LowRank-Reward":           (r"LR-Rew",  "comp"),
    "SW-LinUCB (Cheung+ '19)":  (r"SW-Lin",  "comp"),
    "D-LinUCB (Russac+ '19)":   (r"D-Lin",   "comp"),
    "Restart-LinUCB":           (r"Rst-Lin",   "comp"),
    "LinUCB (Abbasi+ '11)":     (r"LinUCB",     "comp"),
    "LinTS (Agrawal+ 13)":      (r"LinTS",     "comp"),
    "SW-LinTS":                 (r"SW-LinTS",  "comp"),
}

ORDER = list(LABEL.keys())

def fmt(val, se):
    if val is None: return "--"
    if val >= 100: return f"${int(round(val))}{{\\pm}}{int(round(se))}$"
    return f"${val:.1f}{{\\pm}}{se:.1f}$"

data['MovieLens'] = data['MovieLens'][3:]

def make_table(dataset, label, caption):
    cells = data[dataset]
    cells_sorted = sorted(cells, key=lambda c: (c['d'], c['r']))
    ncols = len(ORDER)
    lines = []
    lines.append(r"\begin{table}[!htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{" + caption + "}")
    lines.append(r"\label{" + label + "}")
    lines.append(r"\scriptsize")
    lines.append(r"\setlength{\tabcolsep}{3pt}")
    lines.append(r"\resizebox{\textwidth}{!}{%")
    lines.append(r"\begin{tabular}{ll" + "r"*ncols + "}")
    lines.append(r"\toprule")
    hdr = r"$d$ & $r$"
    for m in ORDER:
        hdr += " & " + LABEL[m][0]
    lines.append(hdr + r" \\")
    lines.append(r"\midrule")
    prev_d = None
    for c in cells_sorted:
        d, r = c['d'], c['r']
        meths = c['methods']
        comp_means = {m: meths[m][0] for m in ORDER if LABEL[m][1]=='comp' and m in meths}
        best_comp = min(comp_means.values()) if comp_means else None
        best_comp_method = min(comp_means, key=comp_means.get) if comp_means else None
        row_cells = []
        for m in ORDER:
            if m in meths:
                val, se = meths[m]
                s = fmt(val, se)
                if m in ("SPSC Alg.1 (ours)","SPSC Adaptive (ours)") and best_comp is not None and val < best_comp:
                    s = r"\cellcolor{green!12}" + s
                elif m == best_comp_method:
                    s = r"\underline{" + s + "}"
                row_cells.append(s)
            else:
                row_cells.append("--")
        d_str = str(d) if d != prev_d else ""
        prev_d = d
        lines.append(f"{d_str} & {r} & " + " & ".join(row_cells) + r" \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}%")
    lines.append(r"}")
    lines.append(r"\end{table}")
    return "\n".join(lines)

out = []
out.append(make_table('Covertype',  'tab:app-covertype',
    r"\textbf{Covertype} per-cell results. Mean $\pm$ SE costed regret over 10 seeds. Green = SPSC variant beats every non-oracle baseline; underline = best non-oracle. $T{=}10{,}000$, $K{=}4$."))
out.append(make_table('Pendigits', 'tab:app-pendigits',
    r"\textbf{Pendigits} per-cell results. $T{=}5{,}000$, $K{=}10$, 10 seeds."))
out.append(make_table('Satimage', 'tab:app-satimage',
    r"\textbf{Satimage} per-cell results. $T{=}5{,}000$, $K{=}10$, 10 seeds."))
out.append(make_table('Fashion-MNIST', 'tab:app-fmnist',
    r"\textbf{Fashion-MNIST} per-cell results. $T{=}5{,}000$, $K{=}10$, 10 seeds."))
out.append(make_table('MNIST', 'tab:app-mnist',
    r"\textbf{MNIST} per-cell results. $T{=}5{,}000$, $K{=}10$, 10 seeds."))
out.append(make_table('MovieLens', 'tab:app-movielens',
    r"\textbf{MovieLens} (fully real ratings) per-cell results. $T{=}5{,}000$, $K{=}10$, 10 seeds."))
out.append(make_table('Warfarin', 'tab:app-warfarin',
    r"\textbf{Warfarin} ($d{=}93$, $K{=}8$, $T{=}5{,}000$) per-rank results across $r\in\{1,2,3,5,10\}$. 10 seeds."))

with open('appendix_tables.tex','w') as f:
    f.write("\n\n".join(out))

print("Wrote appendix_tables.tex,", sum(len(x) for x in out), "chars")
