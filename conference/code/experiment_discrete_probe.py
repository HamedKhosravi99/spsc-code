"""
Discrete-action probe ablation (Reviewer 2 Q3).

Setting: Pendigits, d=105, r=10, K=10, T=5,000, 10 seeds.

Compares three probe variants for SPSC's probe rounds:
  - sphere       : draw u ~ sphere(sqrt(d))           (paper default)
  - arm_uniform  : draw u along a random arm from A_t
  - arm_leverage : draw u along an arm a from A_t with prob ~ ||a||^2

Implementation: monkey-patches the SPSC instance's `rng.standard_normal(d)`
to return a vector pointing in a feasible-arm direction.  SPSC then computes
u_t = sqrt(d) * z / ||z|| as usual, so u_t lies on the d-sphere but along
the chosen arm direction.  This isolates "the recovery operator only sees
arm directions" without changing the SPSC code.

Honest caveat: this restricts probe DIRECTIONS to feasible arm directions
but still rescales to sphere norm. A fully unscaled discrete-action probe
would also need a recalibrated K^{-1} operator (the closed-form sphere-K^{-1}
becomes biased), which is outside the scope of this ablation.
"""

import os, sys, json, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environments import RealPendigitsEnvironment
from algorithm import SPSC_Algorithm1, LinUCB

OUT_DIR     = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(OUT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
RESULTS_PATH = os.path.join(RESULTS_DIR, "experiment_discrete_probe.json")
FIGURE_PATH  = os.path.join(OUT_DIR, "experiment_discrete_probe.png")

# --------------------------------------------------------------------------
# Configuration (matches Pendigits best winning cell from §5.2)
# --------------------------------------------------------------------------
N_SEEDS     = 10
T_TOTAL     = 5000
SEG_SIZE    = 500
N_SEGMENTS  = 10
D, R        = 105, 10
PROBE_EVERY = 10
PROBE_COST  = 0.02
WINDOW      = 400
LAM         = 0.01
DELTA       = 0.05


def make_env(seed):
    return RealPendigitsEnvironment(
        d=D, r=R, n_actions=40, segment_size=SEG_SIZE,
        n_segments=N_SEGMENTS, seed=seed * 13 + 7,
    )


# --------------------------------------------------------------------------
# Action-set tracker: makes env.last_action_set readable from the rng wrapper
# --------------------------------------------------------------------------
class TrackingEnv:
    def __init__(self, env):
        object.__setattr__(self, "_env", env)
        object.__setattr__(self, "last_action_set", None)

    def get_action_set(self, t, rng=None):
        a = self._env.get_action_set(t, rng=rng)
        object.__setattr__(self, "last_action_set", a)
        return a

    # Pass-through everything else
    def __getattr__(self, name):
        return getattr(self._env, name)

    def __setattr__(self, name, val):
        if name == "last_action_set":
            object.__setattr__(self, name, val)
        else:
            setattr(self._env, name, val)


# --------------------------------------------------------------------------
# RNG wrapper: redirects standard_normal(d) to an arm direction
# --------------------------------------------------------------------------
class ArmProbeRng:
    """
    Wraps a numpy Generator.  When SPSC calls standard_normal(d), returns a
    vector along a random arm of env.last_action_set; SPSC's normalisation
    u_t = sqrt(d) * z / ||z|| then yields a sphere-norm probe in arm direction.
    All other rng calls pass through unchanged.
    """
    _SENTINEL = ("_rng", "_env", "_d", "_mode", "_n_probe_calls")

    def __init__(self, base_rng, env, d, mode="arm_uniform"):
        for k in self._SENTINEL:
            object.__setattr__(self, k, None)
        object.__setattr__(self, "_rng", base_rng)
        object.__setattr__(self, "_env", env)
        object.__setattr__(self, "_d", int(d))
        object.__setattr__(self, "_mode", mode)
        object.__setattr__(self, "_n_probe_calls", 0)

    def standard_normal(self, size=None, *args, **kwargs):
        # Probe pattern: SPSC_Algorithm1 calls standard_normal(d) with
        # `size` as a positional int equal to ambient dim.
        if isinstance(size, (int, np.integer)) and int(size) == self._d:
            actset = self._env.last_action_set
            if actset is None or len(actset) == 0:
                return self._rng.standard_normal(int(size))

            n_arms = len(actset)
            if self._mode == "arm_uniform":
                idx = int(self._rng.integers(n_arms))
            elif self._mode == "arm_leverage":
                norms2 = np.sum(actset ** 2, axis=1) + 1e-12
                p = norms2 / norms2.sum()
                idx = int(self._rng.choice(n_arms, p=p))
            else:
                idx = int(self._rng.integers(n_arms))

            arm = actset[idx].astype(float)
            object.__setattr__(self, "_n_probe_calls",
                               self._n_probe_calls + 1)
            # Returning `arm`: SPSC normalises to sqrt(d) * arm / ||arm||,
            # giving a sphere-norm probe along the arm direction.
            return arm.copy()

        return self._rng.standard_normal(size, *args, **kwargs)

    # Pass through all other rng methods/attrs
    def __getattr__(self, name):
        return getattr(self._rng, name)

    def __setattr__(self, name, val):
        if name in self._SENTINEL:
            object.__setattr__(self, name, val)
        else:
            setattr(self._rng, name, val)


# --------------------------------------------------------------------------
# Run helpers
# --------------------------------------------------------------------------
def run_spsc(seed, mode):
    """mode in {sphere, arm_uniform, arm_leverage}."""
    base_env = make_env(seed)
    env = TrackingEnv(base_env)

    spsc = SPSC_Algorithm1(
        env, probe_every=PROBE_EVERY, probe_cost=PROBE_COST,
        window=WINDOW, lam=LAM, delta=DELTA, seed=seed,
        normalize_gamma_by_d=True,
    )
    if mode != "sphere":
        spsc.rng = ArmProbeRng(spsc.rng, env, d=D, mode=mode)

    metrics = spsc.run()
    return float(metrics.cumulative_control_regret[-1])


def run_linucb(seed):
    env = make_env(seed)
    lin = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000)
    metrics = lin.run()
    return float(metrics.cumulative_control_regret[-1])


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    print("=" * 80)
    print(f"Discrete-action probe ablation: Pendigits d={D}, r={R}, T={T_TOTAL}, K={N_SEGMENTS}, seeds={N_SEEDS}")
    print("=" * 80)

    results = {"sphere": [], "arm_uniform": [], "arm_leverage": [], "linucb": []}

    for seed in range(N_SEEDS):
        print(f"\n  -- seed {seed+1}/{N_SEEDS} --", flush=True)
        for mode in ("sphere", "arm_uniform", "arm_leverage"):
            t0 = time.time()
            r = run_spsc(seed, mode)
            results[mode].append(r)
            print(f"    SPSC ({mode:14s})  regret = {r:>8.0f}   [{time.time()-t0:.1f}s]",
                  flush=True)
        t0 = time.time()
        r = run_linucb(seed)
        results["linucb"].append(r)
        print(f"    LinUCB                      regret = {r:>8.0f}   [{time.time()-t0:.1f}s]",
              flush=True)

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {RESULTS_PATH}")

    # ----------------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"  Summary  (Pendigits d={D}, r={R}, {N_SEEDS} seeds)")
    print("-" * 80)
    print(f"  {'Method':<28}  {'Mean':>8}  {'SE':>6}  {'vs LinUCB':>10}")
    print("-" * 80)
    lin_mean = np.mean(results["linucb"])
    for k, label in [
        ("sphere",       "SPSC sphere probe"),
        ("arm_uniform",  "SPSC arm-uniform probe"),
        ("arm_leverage", "SPSC arm-leverage probe"),
        ("linucb",       "LinUCB (baseline)"),
    ]:
        v = np.array(results[k])
        m, s = v.mean(), v.std() / np.sqrt(len(v))
        delta = (m / max(lin_mean, 1e-8) - 1) * 100
        print(f"  {label:<28}  {m:>8.0f}  {s:>6.0f}  {delta:>+9.1f}%")
    print("=" * 80)

    plot(results)


def plot(results):
    LABELS = {
        "sphere":       "SPSC (sphere probe)",
        "arm_uniform":  "SPSC (arm-uniform probe)",
        "arm_leverage": "SPSC (arm-leverage probe)",
        "linucb":       "LinUCB",
    }
    COLORS = {
        "sphere":       "#1f77b4",
        "arm_uniform":  "#2ca02c",
        "arm_leverage": "#17becf",
        "linucb":       "#d62728",
    }
    keys = ["sphere", "arm_uniform", "arm_leverage", "linucb"]

    means = [np.mean(results[k]) for k in keys]
    ses   = [np.std(results[k]) / np.sqrt(len(results[k])) for k in keys]

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    y = np.arange(len(keys))
    ax.barh(y, means, xerr=ses, color=[COLORS[k] for k in keys],
            capsize=4, height=0.6, edgecolor="black", linewidth=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels([LABELS[k] for k in keys],
                       fontsize=12.5, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("Control Regret", fontsize=13, fontweight="bold")
    ax.set_title(
        f"Discrete-action probe ablation (Pendigits, "
        f"$d{{=}}{D}$, $r{{=}}{R}$, $K{{=}}{N_SEGMENTS}$, $T{{=}}{T_TOTAL}$)",
        fontsize=13, fontweight="bold",
    )
    ax.grid(True, axis="x", alpha=0.35)
    plt.tight_layout()
    plt.savefig(FIGURE_PATH, dpi=180, bbox_inches="tight")
    print(f"Saved: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
