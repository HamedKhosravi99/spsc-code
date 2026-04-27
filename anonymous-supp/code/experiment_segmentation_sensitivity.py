"""
Segmentation-sensitivity study (revision W11) on Pendigits.

The base experiment (experiment_pendigits_lints.py and friends) segments the
data by sorting by digit label, so each segment contains one class. Reviewers
may worry the SPSC advantage is an artifact of this rule. We run three
alternative segmentation rules and report SPSC's cost-regret ratio vs. the
best non-oracle baseline. If ratios stay well below 1 across rules, the
advantage is not a segmentation artifact.

Rules:
  A. sorted-by-label   (original: each segment = one digit class)
  B. paired-classes    (segment k = one of {0,1}, {2,3}, ..., {8,9})
  C. random-class-mix  (each segment draws a random 40% subset of classes)

Output: exps/results/experiment_segmentation_sensitivity.json

Cell: (d=105, r=10), T=5000, K=10, 10 seeds. This is SPSC's best-cell regime
per Table 1 of the paper.

Run time: ~30-60 min on 16 cores (3 rules x 10 seeds x 5 methods).
"""

import os, sys, time
import numpy as np
from copy import deepcopy
sys.path.insert(0, os.path.dirname(__file__))
from environments import RealPendigitsEnvironment
from algorithm import SPSC_Algorithm1, SPSC_Adaptive, LinUCB, SWLinUCB, LowOFUL
from results_io import save_results

N_SEEDS = 10
D, R = 105, 10
N_ACTIONS = 40
SEGMENT_SIZE, N_SEGMENTS = 500, 10
WINDOW, LAM, DELTA = 400, 0.01, 0.05
PROBE_EVERY, PROBE_COST = 50, 0.1

METHODS = ["SPSC-Alg1", "SPSC-Adaptive", "LinUCB", "SW-LinUCB", "LowOFUL"]


# ---- segmentation rules --------------------------------------------------

def _rebuild_trajectory_with_order(env: RealPendigitsEnvironment, new_order: np.ndarray):
    """Re-materialize env internals using `new_order` as the row permutation of
    the underlying dataset before segmenting into K blocks of SEGMENT_SIZE.

    This mutates env in place so downstream algorithm objects see the new
    trajectory when they read env.theta / env.seg_of / env.get_action_set(t).
    """
    features = env._features[new_order]
    labels = env._labels[new_order]
    T = env.K * env.segment_lengths[0]  # K x SEGMENT_SIZE
    if T > len(features):
        T = (len(features) // env.K) * env.K
    step = len(features) // T if T > 0 else 1
    idx = np.arange(0, len(features), step)[:T]
    env._seg_features = features[idx]
    env._seg_labels = labels[idx]
    env.T = T
    env.segment_lengths = [T // env.K] * env.K
    env.segment_lengths[-1] += T - sum(env.segment_lengths)
    env.tau = [0]
    for L in env.segment_lengths[:-1]:
        env.tau.append(env.tau[-1] + L)
    env.seg_of = np.zeros(T, dtype=int)
    for k, s in enumerate(env.tau):
        env.seg_of[s:s + env.segment_lengths[k]] = k
    env._build_theta_and_subspaces()


def rule_sorted_by_label(env, rng):
    # Base behaviour (already applied in RealPendigitsEnvironment.__init__).
    return env  # no-op


def rule_paired_classes(env, rng):
    """Build K=10 segments such that segment k draws from class pair
    p(k) = (k mod 5): pairs are {0,1},{2,3},{4,5},{6,7},{8,9} and each
    pair appears in two non-consecutive segments (indices k and k+5).
    Within a segment both classes are interleaved, so the subspace of
    segment k and segment k+5 is similar but their dynamics realise
    different draws, testing SPSC's ability to re-identify the same
    subspace when it reappears after visiting others.
    """
    labels = (env._labels + 4.5).astype(int)  # undo centering, yielding 0..9
    segments = []
    for k in range(env.K):
        pair = k % 5
        c1, c2 = 2 * pair, 2 * pair + 1
        mask = (labels == c1) | (labels == c2)
        pool = np.where(mask)[0]
        rng.shuffle(pool)
        segments.append(pool[:env.segment_lengths[0]])
    order = np.concatenate(segments)
    _rebuild_trajectory_with_order(env, order)
    return env


def rule_random_class_mix(env, rng):
    """Each segment is formed by sampling a random 40%-subset of the 10 classes
    and drawing SEGMENT_SIZE rows from that pool. Produces class-overlap across
    segments, so the subspace changes smoothly rather than by clean swaps.
    """
    labels = (env._labels + 4.5).astype(int)
    classes = np.arange(10)
    segments = []
    for k in range(env.K):
        chosen = rng.choice(classes, size=4, replace=False)
        mask = np.isin(labels, chosen)
        pool = np.where(mask)[0]
        rng.shuffle(pool)
        segments.append(pool[:env.segment_lengths[0]])
    order = np.concatenate(segments)
    _rebuild_trajectory_with_order(env, order)
    return env


RULES = {
    "sorted_by_label": rule_sorted_by_label,
    "paired_classes":  rule_paired_classes,
    "random_class_mix": rule_random_class_mix,
}


# ---- runner --------------------------------------------------------------

def make_env(seed, rule_name):
    env = RealPendigitsEnvironment(
        d=D, r=R, n_actions=N_ACTIONS,
        segment_size=SEGMENT_SIZE, n_segments=N_SEGMENTS,
        seed=seed * 13 + 7,
    )
    rng = np.random.default_rng(seed * 29 + 101)
    return RULES[rule_name](env, rng)


def run_method(name, env, seed):
    if name == "SPSC-Alg1":
        m = SPSC_Algorithm1(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                            window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                            normalize_gamma_by_d=True).run()
        return float(m.cumulative_costed_regret[-1])
    if name == "SPSC-Adaptive":
        m = SPSC_Adaptive(env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
                          window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
                          m_relearn=30, det_window=50, cusum_threshold=3.0,
                          warmup=100).run()
        return float(m.cumulative_costed_regret[-1])
    if name == "LinUCB":
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 2000).run()
    elif name == "SW-LinUCB":
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA, seed=seed + 3000).run()
    elif name == "LowOFUL":
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 5000).run()
    else:
        raise ValueError(name)
    return float(m.cumulative_control_regret[-1])


def run_rule(rule_name):
    print(f"\n[{rule_name}]")
    t0 = time.time()
    res = {m: [] for m in METHODS}
    for s in range(N_SEEDS):
        for m in METHODS:
            env = make_env(s, rule_name)
            res[m].append(run_method(m, env, s))
    for m in METHODS:
        arr = np.array(res[m])
        print(f"  {m:<15} {arr.mean():>7.0f} +/- {arr.std()/np.sqrt(N_SEEDS):>5.0f}")
    print(f"  [{time.time()-t0:.1f}s]")
    return {m: np.array(v) for m, v in res.items()}


if __name__ == "__main__":
    print("=" * 80)
    print(f"Segmentation-sensitivity study   (d={D}, r={R}, K={N_SEGMENTS}, seeds={N_SEEDS})")
    print("=" * 80)

    all_results = {}
    overall_t0 = time.time()
    for rule_name in RULES:
        all_results[rule_name] = run_rule(rule_name)
    print(f"\nTotal time: {(time.time()-overall_t0)/60:.1f} min")

    save_results(
        __file__,
        config={
            "N_SEEDS": N_SEEDS, "D": D, "R": R, "N_ACTIONS": N_ACTIONS,
            "SEGMENT_SIZE": SEGMENT_SIZE, "N_SEGMENTS": N_SEGMENTS,
            "WINDOW": WINDOW, "LAM": LAM, "DELTA": DELTA,
            "PROBE_EVERY": PROBE_EVERY, "PROBE_COST": PROBE_COST,
            "METHODS": METHODS, "RULES": list(RULES.keys()),
        },
        results=all_results,
    )
    print("Done.")
