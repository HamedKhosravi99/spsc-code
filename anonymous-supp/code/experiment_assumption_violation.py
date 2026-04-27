"""
Assumption-violation sensitivity study (revision W2).

Three sweeps, all on the synthetic LowRankLDSEnvironment, d=60, r=5, K=10, T=5000:
  (a) variance misspecification: algorithm is told sigma_hat != true sigma_eps.
      Cor. (misspec): the variance bias enters the Davis-Kahan bound only as
      a scaled identity for Gaussian probes, so subspace recovery should be
      robust and regret should degrade only through the eigengap constant.
  (b) approximate low rank: reward is (B_k w_t + eps_perp * v_t)^T x + noise,
      with v_t unit-norm off-subspace. Cor. 2 predicts an additive
      R_A * eps_perp * n_k per-segment regret term.
  (c) LDS instability: spectral_radius in {0.8, 0.95, 0.99, 1.0}. Testing the
      rho <= 1-alpha_0 assumption. At rho = 1.0 the LDS is a random walk
      (assumption violated); we expect graceful degradation up to 0.99.

Output: exps/results/experiment_assumption_violation.json

Run time estimate: ~60-90 min on a 16-core CPU (3 sweeps x 4 points x 10 seeds x
                   ~6 methods).
"""

import os, sys, time, copy
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from environments import LowRankLDSEnvironment
from algorithm import (
    SPSC_Algorithm1, SPSC_Adaptive, LinUCB, SWLinUCB, DLinUCB,
    LowOFUL, OracleLinUCB,
)
from results_io import save_results

# ---- fixed config ---------------------------------------------------------
N_SEEDS = 10
T, K, D, R = 5000, 10, 60, 5
N_ACTIONS = 40
PROBE_EVERY, PROBE_COST = 50, 0.1
WINDOW, LAM, DELTA = 400, 0.01, 0.05
BASE_SIGMA_EPS = 0.3
BASE_SPEC_RAD = 0.99
BASE_SIGMA_ETA = 0.04

METHODS = ["Oracle-LinUCB", "SPSC-Alg1", "SPSC-Adaptive",
           "LinUCB", "SW-LinUCB", "D-LinUCB", "LowOFUL"]


# ---- environment wrappers -------------------------------------------------

class OffSubspaceEnvironment:
    """Wraps a LowRankLDSEnvironment by adding eps_perp * v_t to theta_t, where
    v_t is a unit vector orthogonal to the current segment's subspace.
    Only theta (and therefore step()) is affected; the latent state w_t and
    the "true" projector B_k are unchanged, so the environment still reports
    the rank-r subspace that low-rank methods would ideally recover.
    """
    def __init__(self, base_env, eps_perp, seed=0):
        self._base = base_env
        self.eps_perp = float(eps_perp)
        rng = np.random.default_rng(seed)
        # For each segment, pick a unit vector in the orthogonal complement
        # of B_k; draw one v_k and hold it constant within the segment.
        v_list = []
        for k in range(base_env.K):
            Pk = base_env.segment_projector(k)
            while True:
                z = rng.standard_normal(base_env.d)
                z = z - Pk @ z  # project to orthogonal complement
                nrm = np.linalg.norm(z)
                if nrm > 1e-6:
                    v_list.append(z / nrm)
                    break
        # Apply the perturbation to theta_t in-place.
        for t in range(base_env.T):
            k = base_env.seg_of[t]
            base_env.theta[t] = base_env.theta[t] + self.eps_perp * v_list[k]
        # Update S (theta norm bound) after perturbation.
        base_env.S = float(np.max(np.linalg.norm(base_env.theta, axis=1)))

    def __getattr__(self, name):
        return getattr(self._base, name)


class MisspecSigmaEnvironment:
    """Exposes sigma_eps = sigma_hat to the algorithm (via env.sigma_eps) while
    drawing noise with the true sigma_eps via step(). Everything else is
    delegated to the base env.
    """
    def __init__(self, base_env, sigma_hat):
        self._base = base_env
        self._true_sigma = base_env.sigma_eps
        self.sigma_eps = float(sigma_hat)     # what the algorithm sees
        self.L_eps = base_env.L_eps
        self.L_x = base_env.L_x
        self.L = base_env.L
        self.S = base_env.S

    def step(self, action, t):
        # Draw noise with the TRUE sigma, not the one exposed.
        eps = self._base.rng.normal(0.0, self._true_sigma)
        eps = np.clip(eps, -self._base.L_eps, self._base.L_eps)
        return float(action @ self._base.theta[t]) + eps

    def __getattr__(self, name):
        return getattr(self._base, name)


# ---- algorithm runner -----------------------------------------------------

def _run_method(name, env, seed):
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
    if name == "Oracle-LinUCB":
        m = OracleLinUCB(env, lam=LAM, delta=DELTA, seed=seed + 1000).run()
    elif name == "LinUCB":
        m = LinUCB(env, lam=LAM, delta=DELTA, seed=seed + 2000).run()
    elif name == "SW-LinUCB":
        m = SWLinUCB(env, window=WINDOW, lam=LAM, delta=DELTA, seed=seed + 3000).run()
    elif name == "D-LinUCB":
        m = DLinUCB(env, gamma=0.998, lam=LAM, delta=DELTA, seed=seed + 4000).run()
    elif name == "LowOFUL":
        m = LowOFUL(env, lam=LAM, delta=DELTA, seed=seed + 5000).run()
    else:
        raise ValueError(name)
    return float(m.cumulative_control_regret[-1])


def _make_env(seed):
    return LowRankLDSEnvironment(
        d=D, r=R, K=K, T=T, sigma_eps=BASE_SIGMA_EPS,
        spectral_radius=BASE_SPEC_RAD, n_actions=N_ACTIONS,
        sigma_eta=BASE_SIGMA_ETA, seed=seed * 100,
        piecewise_constant=True, feature_decay=1.5,
    )


def run_cell(env_factory):
    """Run all methods on envs built by env_factory(seed)."""
    out = {m: [] for m in METHODS}
    for s in range(N_SEEDS):
        for m in METHODS:
            env = env_factory(s)
            out[m].append(_run_method(m, env, s))
    return {m: np.array(v) for m, v in out.items()}


# ---- sweep drivers --------------------------------------------------------

def sweep_variance_misspec():
    print("\n[Sweep A] Variance misspecification: sigma_hat / sigma_true")
    ratios = [0.5, 1.0, 2.0, 4.0]
    results = {}
    for ratio in ratios:
        print(f"  ratio = {ratio}")
        t0 = time.time()
        sigma_hat = BASE_SIGMA_EPS * ratio

        def factory(seed, sh=sigma_hat):
            return MisspecSigmaEnvironment(_make_env(seed), sh)
        res = run_cell(factory)
        results[ratio] = res
        for m in METHODS:
            arr = res[m]
            print(f"    {m:<15} {arr.mean():>7.0f} +/- {arr.std()/np.sqrt(N_SEEDS):>5.0f}")
        print(f"    [{time.time()-t0:.1f}s]")
    return results


def sweep_approximate_rank():
    print("\n[Sweep B] Approximate low rank: eps_perp (off-subspace magnitude)")
    eps_vals = [0.0, 0.05, 0.1, 0.2, 0.4]
    results = {}
    for ep in eps_vals:
        print(f"  eps_perp = {ep}")
        t0 = time.time()

        def factory(seed, e=ep):
            return OffSubspaceEnvironment(_make_env(seed), eps_perp=e, seed=seed + 999)
        res = run_cell(factory)
        results[ep] = res
        for m in METHODS:
            arr = res[m]
            print(f"    {m:<15} {arr.mean():>7.0f} +/- {arr.std()/np.sqrt(N_SEEDS):>5.0f}")
        print(f"    [{time.time()-t0:.1f}s]")
    return results


def sweep_spectral_radius():
    print("\n[Sweep C] LDS spectral radius (stability)")
    rhos = [0.8, 0.95, 0.99, 1.0]
    results = {}
    for rho in rhos:
        print(f"  rho = {rho}")
        t0 = time.time()

        def factory(seed, r_=rho):
            return LowRankLDSEnvironment(
                d=D, r=R, K=K, T=T, sigma_eps=BASE_SIGMA_EPS,
                spectral_radius=r_, n_actions=N_ACTIONS,
                sigma_eta=BASE_SIGMA_ETA, seed=seed * 100,
                piecewise_constant=False,  # LDS active so spectral radius matters
                feature_decay=1.5,
            )
        res = run_cell(factory)
        results[rho] = res
        for m in METHODS:
            arr = res[m]
            print(f"    {m:<15} {arr.mean():>7.0f} +/- {arr.std()/np.sqrt(N_SEEDS):>5.0f}")
        print(f"    [{time.time()-t0:.1f}s]")
    return results


# ---- main -----------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 80)
    print(f"Assumption-violation study   d={D}, r={R}, K={K}, T={T}, seeds={N_SEEDS}")
    print("=" * 80)

    overall_t0 = time.time()
    all_results = {
        "variance_misspec": sweep_variance_misspec(),
        "approximate_rank": sweep_approximate_rank(),
        "spectral_radius": sweep_spectral_radius(),
    }
    print(f"\nTotal time: {(time.time()-overall_t0)/60:.1f} min")

    save_results(
        __file__,
        config={
            "N_SEEDS": N_SEEDS, "T": T, "K": K, "D": D, "R": R,
            "N_ACTIONS": N_ACTIONS, "PROBE_EVERY": PROBE_EVERY,
            "PROBE_COST": PROBE_COST, "WINDOW": WINDOW,
            "LAM": LAM, "DELTA": DELTA,
            "BASE_SIGMA_EPS": BASE_SIGMA_EPS, "BASE_SPEC_RAD": BASE_SPEC_RAD,
            "BASE_SIGMA_ETA": BASE_SIGMA_ETA, "METHODS": METHODS,
        },
        results=all_results,
    )
    print("Done.")
