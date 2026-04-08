"""
Experiment: Real-Domain Bandit Benchmarks (Warfarin + Yahoo-style).

Two genuine decision-making domains with naturally high d and low-rank structure:

1. Warfarin Clinical Dosing (d=93, natural r≈3)
   - Patient features: demographics, genotypes, clinical indicators
   - Action: dose recommendation
   - Low-rank: pharmacogenomic factors
   - Segments: patient subpopulation shifts

2. Yahoo-style News Recommendation (d=136, natural r≈5)
   - User × article interaction features
   - Action: article recommendation
   - Low-rank: topic clustering
   - Segments: news cycle shifts

Grid per dataset: r ∈ {1, 2, 3, 5, 10}, 10 seeds
Reports: regret table, subspace recovery, probe overhead.
"""

import os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import WarfarinEnvironment
try:
    from yahoo_environment import YahooR6Environment
except ImportError:
    YahooR6Environment = None  # Yahoo benchmark not used in paper
from algorithm import SPSC_Algorithm1, LinUCB, OracleLinUCB, RunMetrics, SWLinUCB, DLinUCB, OracleResetLinUCB

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALGO_NAMES = ["SPSC", "Oracle", "D-LinUCB", "SW-LinUCB", "Restart-LinUCB", "LinUCB"]

def final_regret(runs):
    finals = np.array([r.cumulative_control_regret[-1] for r in runs])
    return finals.mean(), finals.std() / np.sqrt(len(finals))

def final_costed(runs):
    finals = np.array([r.costed_regret.sum() for r in runs])
    return finals.mean(), finals.std() / np.sqrt(len(finals))

def avg_subspace_error(runs):
    errors = []
    for r in runs:
        valid = r.subspace_error[~np.isnan(r.subspace_error)]
        if len(valid) > 0: errors.append(valid.mean())
    if errors: return np.mean(errors), np.std(errors) / np.sqrt(len(errors))
    return np.nan, np.nan


def run_cell(env_class, env_kwargs, r, n_seeds, probe_every=10, probe_cost=0.1, window=200):
    """Run all algorithms for one (env, r) configuration."""
    results = {n: [] for n in ALGO_NAMES}

    for seed in range(n_seeds):
        print(f"    seed {seed+1}/{n_seeds}", end="\r", flush=True)
        kw = {**env_kwargs, "r": r, "seed": seed * 13 + 7}

        for name in ALGO_NAMES:
            env = env_class(**kw)
            if name == "SPSC":
                m = SPSC_Algorithm1(env, probe_every=probe_every,
                                    probe_cost=probe_cost, window=window,
                                    lam=1.0, delta=0.05, seed=seed,
                                    normalize_gamma_by_d=True).run()
            elif name == "Oracle":
                m = OracleLinUCB(env, window=10000, lam=1.0, delta=0.05,
                                 seed=seed + 1000).run()
            elif name == "D-LinUCB":
                m = DLinUCB(env, gamma=0.995, lam=1.0, delta=0.05,
                            seed=seed + 2000).run()
            elif name == "SW-LinUCB":
                m = SWLinUCB(env, window=200, lam=1.0, delta=0.05,
                             seed=seed + 3000).run()
            elif name == "Restart-LinUCB":
                m = OracleResetLinUCB(env, lam=1.0, delta=0.05,
                                      seed=seed + 4000).run()
            elif name == "LinUCB":
                m = LinUCB(env, lam=1.0, delta=0.05, seed=seed + 5000).run()
            results[name].append(m)
    print(flush=True)
    return results


def print_cell(results, label, r, d):
    """Print summary table for one cell."""
    linucb_m, _ = final_regret(results["LinUCB"])
    best_name, best_val = None, np.inf
    for name in ALGO_NAMES:
        if name == "Oracle": continue
        m, _ = final_regret(results[name])
        if m < best_val: best_val, best_name = m, name

    print(f"\n{'='*100}")
    print(f"  {label}, r={r}, d={d}")
    print(f"  {'Method':<22} {'Mean':>10} {'Std':>10} {'SE':>10} {'vs LinUCB':>10} {'vs Best':>10} {'':>10}")
    print(f"  {'-'*90}")

    for name in ALGO_NAMES:
        finals = np.array([r.cumulative_control_regret[-1] for r in results[name]])
        m, s, se = finals.mean(), finals.std(), finals.std()/np.sqrt(len(finals))
        vs_lin = m / linucb_m if linucb_m > 0 else np.nan
        vs_best = m / best_val if best_val > 0 else np.nan
        tag = "(oracle)" if name == "Oracle" else ("* best" if name == best_name else ("<<<" if name == "SPSC" and vs_lin < 1.0 else ""))
        print(f"  {name:<22} {m:>10.1f} {s:>10.1f} {se:>10.1f} {vs_lin:>10.3f} {vs_best:>10.3f}  {tag}")

    sub_m, sub_se = avg_subspace_error(results["SPSC"])
    if not np.isnan(sub_m):
        print(f"  SPSC avg subspace error: {sub_m:.4f} ± {sub_se:.4f}")
    ctrl_m, _ = final_regret(results["SPSC"])
    cost_m, _ = final_costed(results["SPSC"])
    overhead = (cost_m - ctrl_m) / max(cost_m, 1e-8) * 100
    print(f"  SPSC probe overhead: {overhead:.1f}%")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

N_SEEDS = 10
R_VALUES = [1, 2, 3, 5, 10]

if __name__ == "__main__":

    all_results = {}

    # ===================================================================
    # 1. WARFARIN (d=93, clinical dosing)
    # ===================================================================
    print("\n" + "=" * 100)
    print("BENCHMARK 1: Warfarin Clinical Dosing (d=93)")
    print("=" * 100)

    warfarin_kwargs = dict(d=93, K=8, T=5000, n_actions=40, sigma_eps=0.3)

    for r in R_VALUES:
        if r > 10: continue
        print(f"\n--- Warfarin, r={r} ---")
        results = run_cell(WarfarinEnvironment, warfarin_kwargs, r, N_SEEDS,
                           probe_every=10, probe_cost=0.1, window=200)
        all_results[("warfarin", r)] = results
        print_cell(results, "Warfarin", r, 93)

    # Ratio summary
    print(f"\n\nWarfarin SPSC/LinUCB ratio:")
    for r in R_VALUES:
        if ("warfarin", r) not in all_results: continue
        res = all_results[("warfarin", r)]
        spsc_m, _ = final_regret(res["SPSC"])
        lin_m, _ = final_regret(res["LinUCB"])
        ratio = spsc_m / lin_m if lin_m > 0 else np.nan
        marker = "*" if ratio < 1.0 else ""
        print(f"  r={r:>2}: {ratio:.3f}{marker}")

    # ===================================================================
    # 2. YAHOO-STYLE NEWS (d=136, recommendation)
    # ===================================================================
    print("\n" + "=" * 100)
    print("BENCHMARK 2: Yahoo-style News Recommendation (d=136)")
    print("=" * 100)

    yahoo_kwargs = dict(d=136, K=10, T=10000, n_actions=20, sigma_eps=0.2)

    for r in R_VALUES:
        print(f"\n--- Yahoo News, r={r} ---")
        results = run_cell(YahooR6Environment, yahoo_kwargs, r, N_SEEDS,
                           probe_every=15, probe_cost=0.05, window=300)
        all_results[("yahoo", r)] = results
        print_cell(results, "Yahoo News", r, 136)

    # Ratio summary
    print(f"\n\nYahoo SPSC/LinUCB ratio:")
    for r in R_VALUES:
        res = all_results[("yahoo", r)]
        spsc_m, _ = final_regret(res["SPSC"])
        lin_m, _ = final_regret(res["LinUCB"])
        ratio = spsc_m / lin_m if lin_m > 0 else np.nan
        marker = "*" if ratio < 1.0 else ""
        print(f"  r={r:>2}: {ratio:.3f}{marker}")

    # ===================================================================
    # Figure: 2×3 panel
    # ===================================================================
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    for row, (domain, domain_kwargs, domain_label) in enumerate([
        ("warfarin", warfarin_kwargs, "Warfarin (d=93)"),
        ("yahoo", yahoo_kwargs, "Yahoo News (d=136)")
    ]):
        # Panel 1: SPSC/LinUCB ratio vs r
        ax = axes[row, 0]
        ratios, ratio_ses = [], []
        for r in R_VALUES:
            if (domain, r) not in all_results: continue
            res = all_results[(domain, r)]
            spsc_finals = np.array([rr.cumulative_control_regret[-1] for rr in res["SPSC"]])
            lin_finals = np.array([rr.cumulative_control_regret[-1] for rr in res["LinUCB"]])
            ratio = spsc_finals.mean() / lin_finals.mean()
            ratios.append(ratio)
        ax.plot(R_VALUES[:len(ratios)], ratios, "o-", lw=2, markersize=8, color="#1f77b4")
        ax.axhline(1.0, color="gray", ls="--", lw=1)
        ax.set_xlabel("Rank r"); ax.set_ylabel("SPSC / LinUCB")
        ax.set_title(f"{domain_label}: SPSC/LinUCB"); ax.set_xticks(R_VALUES[:len(ratios)])

        # Panel 2: SPSC/Best ratio vs r
        ax = axes[row, 1]
        best_ratios = []
        for r in R_VALUES:
            if (domain, r) not in all_results: continue
            res = all_results[(domain, r)]
            spsc_m, _ = final_regret(res["SPSC"])
            best_val = np.inf
            for name in ALGO_NAMES:
                if name in ("Oracle", "SPSC"): continue
                m, _ = final_regret(res[name])
                if m < best_val: best_val = m
            best_ratios.append(spsc_m / best_val if best_val > 0 else np.nan)
        ax.plot(R_VALUES[:len(best_ratios)], best_ratios, "s-", lw=2, markersize=8, color="#d62728")
        ax.axhline(1.0, color="gray", ls="--", lw=1)
        ax.set_xlabel("Rank r"); ax.set_ylabel("SPSC / Best Competitor")
        ax.set_title(f"{domain_label}: vs Best"); ax.set_xticks(R_VALUES[:len(best_ratios)])

        # Panel 3: Subspace recovery
        ax = axes[row, 2]
        sub_errors, sub_ses_list = [], []
        for r in R_VALUES:
            if (domain, r) not in all_results: continue
            res = all_results[(domain, r)]
            m, se = avg_subspace_error(res["SPSC"])
            sub_errors.append(m); sub_ses_list.append(se)
        ax.errorbar(R_VALUES[:len(sub_errors)], sub_errors, yerr=sub_ses_list,
                     fmt="o-", lw=2, capsize=4, color="#2ca02c")
        ax.set_xlabel("Rank r"); ax.set_ylabel("Avg subspace error")
        ax.set_title(f"{domain_label}: Subspace recovery"); ax.set_xticks(R_VALUES[:len(sub_errors)])

    fig.suptitle(f"Real-Domain Bandit Benchmarks  |  {N_SEEDS} seeds, ±1 SE", fontsize=13, y=1.01)
    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "experiment_real_bandit.png")
    plt.savefig(out_path, bbox_inches="tight", dpi=150)
    print(f"\nSaved: {out_path}")
    print("\nDone!")
