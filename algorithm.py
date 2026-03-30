"""
Single-Play Subspace-Aware Control and baselines.

Algorithms
----------
SPSC_Algorithm1  -- faithful implementation of Algorithm 1 from the paper:
    - Single-play: on probe rounds x_t^dep = u_t (no separate UCB action)
    - Windowed design matrix: only exploitation rounds in [t-W, t) per segment
    - Control regret on probe rounds = r_opt - u_t^T theta_t  (actual, not a proxy)
    - Costed regret adds c per probe round on top of control regret

SPSC_rDim        -- earlier two-play variant (kept for reference/comparison):
    - Plays u_t for sensing AND a UCB action for reward on probe rounds
    - NOT the single-play model; breaks the paper's single-play premise

LinUCB           -- standard ambient-space ridge UCB baseline (no subspace)
OracleLinUCB     -- UCB with oracle knowledge of true subspace (performance ceiling)

K^{-1} operator for sphere probes u = sqrt(d) * z/||z||, z~N(0,I_d)
----------------------------------------------------------------------
  K(M) = d/(d+2) * (tr(M) I_d + 2M)
  K^{-1}(N) = (d+2)/(2d) * N - tr(N)/(2d) * I_d
  Proof: set M = K^{-1}(N), compute tr(M) = tr(N)/d, substitute back. QED.

Metrics per round
-----------------
  costed_regret_t  = r_t* - r_t + c * 1{probe}
  control_regret_t = r_t* - r_t
  probe_flag_t     = bool
  subspace_error_t = ||P_hat_k - P_k*||_2  (set only on probe rounds)
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from environment import LowRankLDSEnvironment


# ---------------------------------------------------------------------------
# K^{-1} operator (sphere probes)
# ---------------------------------------------------------------------------

def K_inverse(N: np.ndarray, d: int) -> np.ndarray:
    """
    K^{-1}(N) = (d+2)/(2d) * N - tr(N)/(2d) * I_d

    Valid for probe distribution u = sqrt(d) * z/||z||, z~N(0,I_d),
    which satisfies E[uu^T] = I_d and ||u||_2 = sqrt(d) exactly.
    """
    c = (d + 2) / (2.0 * d)
    return c * N - (np.trace(N) / (2.0 * d)) * np.eye(d)


# ---------------------------------------------------------------------------
# Metric container
# ---------------------------------------------------------------------------
# (defined once; used by all algorithm classes below)

@dataclass
class RunMetrics:
    name: str
    T: int
    costed_regret: np.ndarray = field(init=False)
    control_regret: np.ndarray = field(init=False)
    probe_flags: np.ndarray = field(init=False)
    subspace_error: np.ndarray = field(init=False)

    def __post_init__(self):
        self.costed_regret  = np.zeros(self.T)
        self.control_regret = np.zeros(self.T)
        self.probe_flags    = np.zeros(self.T, dtype=bool)
        self.subspace_error = np.full(self.T, np.nan)

    @property
    def cumulative_costed_regret(self) -> np.ndarray:
        return np.cumsum(self.costed_regret)

    @property
    def cumulative_control_regret(self) -> np.ndarray:
        return np.cumsum(self.control_regret)

    @property
    def total_probes(self) -> int:
        return int(self.probe_flags.sum())


# ---------------------------------------------------------------------------
# Algorithm 1 — faithful single-play implementation
# ---------------------------------------------------------------------------

class SPSC_Algorithm1:
    """
    Faithful implementation of Algorithm 1 from the paper:
    "Single-Play Subspace-Aware Control with Windowed r-Dimensional Exploitation"

    Single-play invariant
    ---------------------
    On probe rounds: x_t^dep = u_t  (the probe IS the only deployment).
    On exploitation rounds: x_t^dep = argmax UCB over A_t.
    Exactly one env.step() call per round.

    Windowed design matrix
    ----------------------
    V_tilde_t and b_tilde_t are built from exploitation rounds s in the
    current segment with t - W <= s < t.  This matches the W_t definition
    in Algorithm 1 exactly.  No cumulative summation across the whole segment.

    Regret accounting
    -----------------
    control_regret_t = r_opt - x_t^dep^T theta_t   (actual, every round)
    costed_regret_t  = control_regret_t + c * 1{probe round}
    """

    def __init__(
        self,
        env: "LowRankLDSEnvironment",
        probe_every: int = 5,
        probe_cost: float = 0.1,
        window: int = 200,
        lam: float = 1.0,
        delta: float = 0.05,
        seed: int = 0,
        normalize_gamma_by_d: bool = False,
    ):
        self.env         = env
        self.probe_every = probe_every
        self.c           = probe_cost
        self.W           = window
        self.lam         = lam
        self.delta       = delta
        self.rng         = np.random.default_rng(seed)

        d, r = env.d, env.r
        self.d = d
        self.r = r

        self.L_x       = env.L_x
        self.sigma_eps = env.sigma_eps
        self.S         = env.S
        # K^{-1} operator norm for sphere probes
        self.K_inv_op  = (d + 2) / (2.0 * d)
        # When True, R_X_hat in gamma is divided by d, removing the factor that
        # grows with d due to probe vector norm sqrt(d).  This is appropriate for
        # d-scaling experiments where ||G_t||_op ∝ d but the signal norm S^2 is
        # d-independent.  Defaults to False to leave Experiments 1-4 unchanged.
        self._normalize_gamma_by_d = normalize_gamma_by_d
        # Per-segment observed G_t norms (for data-adaptive gamma)
        self._G_norms: list = []

    # ------------------------------------------------------------------
    # Probe schedule: first round of each segment + every probe_every steps
    # ------------------------------------------------------------------

    def _is_probe(self, t: int, k: int) -> bool:
        seg_start = self.env.tau[k]
        if t == seg_start:
            return True
        return ((t - seg_start) % self.probe_every) == 0

    # ------------------------------------------------------------------
    # Confidence radii
    # ------------------------------------------------------------------

    def _beta(self, n_exploit: int) -> float:
        """
        beta_t^{(r,W)}: confidence radius in r-dimensional reduced space,
        calibrated to the effective window size (at most W exploitation steps).

        beta = sigma_eps * sqrt(r * log((1 + n_exploit * L_x^2 / lam) / delta))
               + sqrt(lam) * S
        """
        effective_n = min(n_exploit, self.W)
        arg = max(1.0 + effective_n * self.L_x ** 2 / self.lam, 1.0 + 1e-12)
        return (
            self.sigma_eps * np.sqrt(self.r * np.log(arg / self.delta))
            + np.sqrt(self.lam) * self.S
        )

    def _gamma(self, m_probe: int, M_hat: Optional[np.ndarray] = None) -> float:
        """
        gamma_t = Gamma_k + V_{k,t}(W): subspace mismatch + local drift radius.
        Uses data-adaptive eigengap and empirical G_t norms.
        """
        if m_probe < 2:
            return float(self.S)

        R_X_hat = (
            float(np.percentile(self._G_norms, 90))
            if len(self._G_norms) >= 2
            else self.K_inv_op * self.d * ((self.S + 1.0) ** 2 + self.sigma_eps ** 2)
        )
        # Optional: normalize by d so gamma is d-independent for sphere probes.
        # ||G_t||_op ∝ d due to ||u_t|| = sqrt(d); the signal norm S^2 is d-independent.
        if self._normalize_gamma_by_d:
            R_X_hat = R_X_hat / self.d

        if M_hat is not None:
            eigs = np.sort(np.linalg.eigvalsh(M_hat))[::-1]
            gap = max(float(eigs[self.r - 1] - eigs[self.r]), 1e-4) if len(eigs) > self.r else 1e-4
        else:
            gap = 1e-4

        return (
            8.0 * self.S * R_X_hat / gap
            * np.sqrt(np.log(2.0 * self.d / self.delta) / m_probe)
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> "RunMetrics":
        env = self.env
        d, r, T = self.d, self.r, env.T
        metrics = RunMetrics(name="SPSC-Alg1", T=T)

        # Subspace state
        M_sum       = np.zeros((d, d))
        U_hat       = np.eye(d, r)            # initial: first r standard basis cols
        P_hat       = U_hat @ U_hat.T
        m_probe_seg = 0
        current_k   = -1

        # Exploitation buffer: list of (x_s, y_s, s) for exploitation rounds
        # within the current segment.  Stores raw actions (not projected features)
        # so they can be reprojected with the current U_hat at each step —
        # this eliminates the stale-feature problem from changing U_hat.
        expl_buf: List[tuple] = []

        for t in range(T):
            k = env.seg_of[t]

            # ---- Segment boundary: reset accumulator, clear buffers ----
            if k != current_k:
                M_sum       = np.zeros((d, d))
                m_probe_seg = 0
                self._G_norms = []
                expl_buf    = []
                # Carry forward U_hat / P_hat until first probe updates them
                current_k = k

            action_set = env.get_action_set(t, rng=self.rng)
            r_opt      = env.optimal_reward(action_set, t)

            # ==============================================================
            # PROBE ROUND — single play: x_t^dep = u_t
            # ==============================================================
            if self._is_probe(t, k):
                metrics.probe_flags[t] = True

                # Draw isotropic sphere probe: u = sqrt(d) * z/||z||
                z_probe = self.rng.standard_normal(d)
                u_t     = np.sqrt(d) * z_probe / (np.linalg.norm(z_probe) + 1e-12)

                # Deploy u_t — this is the ONLY action this round
                y_t = env.step(u_t, t)

                # Subspace estimation update
                s_t = y_t ** 2 - self.sigma_eps ** 2
                G_t = K_inverse(s_t * np.outer(u_t, u_t), d)

                self._G_norms.append(float(np.linalg.norm(G_t, ord=2)))
                M_sum       += G_t
                m_probe_seg += 1

                M_hat_now = M_sum / m_probe_seg
                eig_vals, eig_vecs = np.linalg.eigh(M_hat_now)
                U_hat = eig_vecs[:, -r:]       # top-r eigenvectors, d x r
                P_hat = U_hat @ U_hat.T

                # Subspace error diagnostic (oracle ground truth)
                P_true = env.segment_projector(k)
                metrics.subspace_error[t] = np.linalg.norm(P_hat - P_true, ord=2)

                # Regret: actual reward from playing u_t
                r_t = float(u_t @ env.theta[t])
                metrics.control_regret[t] = r_opt - r_t
                metrics.costed_regret[t]  = r_opt - r_t + self.c

            # ==============================================================
            # EXPLOITATION ROUND — windowed reduced-space UCB
            # ==============================================================
            else:
                # Build windowed design from exploitation rounds in [t-W, t)
                # within the current segment (Algorithm 1: W_t definition).
                # Reproject all stored actions with the CURRENT U_hat so all
                # features in the window share a consistent subspace basis —
                # eliminates regression inconsistency from changing U_hat.
                window_entries = [(x_s, y_s) for (x_s, y_s, s) in expl_buf if s >= t - self.W]

                V_tilde = self.lam * np.eye(r)
                b_tilde = np.zeros(r)
                n_exploit = len(window_entries)
                for x_s, y_s in window_entries:
                    z_s = U_hat.T @ x_s   # reproject with current U_hat
                    V_tilde += np.outer(z_s, z_s)
                    b_tilde += z_s * y_s

                a_hat   = np.linalg.solve(V_tilde, b_tilde)
                beta_t  = self._beta(n_exploit)
                gamma_t = self._gamma(
                    m_probe_seg,
                    M_hat=M_sum / max(m_probe_seg, 1),
                )

                # UCB index for each candidate action
                Z       = action_set @ U_hat                          # (n_a, r)
                V_inv_Z = np.linalg.solve(V_tilde, Z.T).T            # (n_a, r)
                ellip   = np.sqrt(np.einsum('ij,ij->i', Z, V_inv_Z)) # (n_a,)
                x_norms = np.linalg.norm(action_set, axis=1)         # (n_a,)
                ucb     = Z @ a_hat + beta_t * ellip + gamma_t * x_norms

                best_idx = int(np.argmax(ucb))
                x_dep    = action_set[best_idx]

                # Single play: deploy x_dep
                y_t = env.step(x_dep, t)

                # Store raw action (not projected feature) so future steps
                # can reproject with their current U_hat
                expl_buf.append((x_dep, y_t, t))

                # Trim buffer to keep only rounds within [t-W, t] (saves memory)
                if len(expl_buf) > self.W + 10:
                    expl_buf = [(x_s, y_s, s) for (x_s, y_s, s) in expl_buf
                                if s >= t - self.W]

                # Subspace estimate unchanged on exploitation rounds
                r_t = float(x_dep @ env.theta[t])
                metrics.control_regret[t] = r_opt - r_t
                metrics.costed_regret[t]  = r_opt - r_t

        return metrics


# ---------------------------------------------------------------------------
# SPSC with r-dimensional exploitation  (earlier two-play variant, for reference)
# ---------------------------------------------------------------------------
# NOTE: This class is NOT Algorithm 1.  On probe rounds it plays u_t for sensing
# AND a separate UCB action for reward — two plays per round — which violates the
# single-play constraint central to the paper.  Kept for comparison only.

class SPSC_rDim:
    """
    Single-Play Subspace-Aware Control — r-dimensional exploitation.

    Probe phase  : isotropic sphere probes -> lifted estimator G_t -> M_hat_k -> U_hat_k
    Exploit phase: reduced features z = U_hat^T x in R^r, r x r ridge regression,
                   UCB with beta_t^{(r)} ~ sqrt(r log T) -- gains sqrt(r/d) vs LinUCB.

    Gamma_t uses a data-adaptive estimate of the eigengap and noise level,
    replacing the worst-case theoretical constants (which are ~10^4x too large
    in practice due to conservative bounding of ||G_t||_2).
    """

    def __init__(
        self,
        env: LowRankLDSEnvironment,
        probe_every: int = 5,
        probe_cost: float = 0.1,
        lam: float = 1.0,
        delta: float = 0.05,
        seed: int = 0,
        forgetting_factor: float = 1.0,
    ):
        self.env        = env
        self.probe_every = probe_every
        self.c          = probe_cost
        self.lam        = lam
        self.delta      = delta
        self.rng        = np.random.default_rng(seed)
        self.ff         = forgetting_factor  # exponential forgetting for non-stationary theta

        d, r = env.d, env.r
        self.d = d
        self.r = r

        # Constants
        self.L_x       = env.L_x
        self.L         = np.sqrt(d)        # ||u||_2 exactly for sphere probes
        self.L_eps     = env.L_eps
        self.sigma_eps = env.sigma_eps
        self.S         = env.S
        # For sphere probes: ||K^{-1}||_op = (d+2)/(2d)
        self.K_inv_op  = (d + 2) / (2.0 * d)
        self.R_s       = (self.L * self.S + self.L_eps) ** 2 + self.sigma_eps ** 2
        self.R_X       = self.K_inv_op * self.L ** 2 * self.R_s + self.S ** 2

        # Per-segment running tracker of ||G_t||_2 for data-adaptive gamma
        self._G_norms: list = []

    # ------------------------------------------------------------------
    # Probe schedule
    # ------------------------------------------------------------------

    def _is_probe(self, t: int, k: int) -> bool:
        seg_start = self.env.tau[k]
        if t == seg_start:
            return True
        return ((t - seg_start) % self.probe_every) == 0

    # ------------------------------------------------------------------
    # Confidence bounds
    # ------------------------------------------------------------------

    def _beta_r(self, t: int) -> float:
        """
        Statistical confidence radius in the r-dimensional reduced space.
        Uses r (not d) in the log factor -- this is the core gain.
        beta_t^{(r)} = sigma_eps * sqrt(r * log((1 + t*L_x^2/lam)/delta)) + sqrt(lam)*S
        """
        arg = max(1.0 + t * self.L_x ** 2 / self.lam, 1.0 + 1e-12)
        return (
            self.sigma_eps * np.sqrt(self.r * np.log(arg / self.delta))
            + np.sqrt(self.lam) * self.S
        )

    def _gamma(self, m_probe: int, M_hat: Optional[np.ndarray] = None) -> float:
        """
        Subspace mismatch radius.

        Theoretical: 8 * S * R_X / lambda_min * sqrt(log(2d/delta)/m)
        Practical  : use empirical eigengap and observed G_t norms to replace
                     worst-case constants (otherwise gamma_t >> signal for any
                     finite T when d is moderate and S is large).
        """
        if m_probe < 2:
            return float(self.S)

        # Empirical noise level: 90th pct of observed ||G_t||_2
        R_X_hat = (
            float(np.percentile(self._G_norms, 90))
            if len(self._G_norms) >= 2
            else self.R_X
        )

        # Empirical eigengap from M_hat
        if M_hat is not None:
            eigs = np.sort(np.linalg.eigvalsh(M_hat))[::-1]
            if len(eigs) > self.r:
                gap = max(float(eigs[self.r - 1] - eigs[self.r]), 1e-4)
            else:
                gap = 1e-4
        else:
            gap = 1e-4

        return (
            8.0 * self.S * R_X_hat / gap
            * np.sqrt(np.log(2.0 * self.d / self.delta) / m_probe)
        )

    # ------------------------------------------------------------------
    # Main run
    # ------------------------------------------------------------------

    def run(self) -> RunMetrics:
        env = self.env
        d, r, T = self.d, self.r, env.T
        metrics = RunMetrics(name="SPSC-rDim", T=T)

        # Ridge estimator lives in R^r (r x r matrix, r-vector)
        V_tilde = self.lam * np.eye(r)          # r x r design
        b_tilde = np.zeros(r)                   # r-vector response

        # Subspace state
        M_sum    = np.zeros((d, d))             # running sum of G_t (unnormalized)
        U_hat    = np.eye(d, r)                 # initial: first r standard basis cols
        P_hat    = U_hat @ U_hat.T              # d x d projector
        m_probe_seg = 0
        current_k   = -1

        for t in range(T):
            k = env.seg_of[t]

            # --- Segment boundary reset ---
            if k != current_k:
                V_tilde     = self.lam * np.eye(r)
                b_tilde     = np.zeros(r)
                M_sum       = np.zeros((d, d))
                m_probe_seg = 0
                self._G_norms = []
                # Carry forward U_hat / P_hat until first probe in new segment
                current_k = k

            action_set = env.get_action_set(t, rng=self.rng)
            r_opt      = env.optimal_reward(action_set, t)

            if self._is_probe(t, k):
                # ============================================================
                # PROBE ROUND — sensing + acting simultaneously
                # ============================================================
                metrics.probe_flags[t] = True

                # --- SENSE: isotropic probe u for subspace identification ---
                # Draw u = sqrt(d) * z/||z||, z~N(0,I_d)
                z = self.rng.standard_normal(d)
                u = np.sqrt(d) * z / (np.linalg.norm(z) + 1e-12)

                y_probe = env.step(u, t)
                s_t     = y_probe ** 2 - self.sigma_eps ** 2
                G_t     = K_inverse(s_t * np.outer(u, u), d)

                self._G_norms.append(float(np.linalg.norm(G_t, ord=2)))
                M_sum       += G_t
                m_probe_seg += 1

                # Rank-r eigendecomposition of normalized estimator
                M_hat_now = M_sum / m_probe_seg
                eig_vals, eig_vecs = np.linalg.eigh(M_hat_now)
                U_hat_new = eig_vecs[:, -r:]          # d x r, orthonormal
                P_hat_new = U_hat_new @ U_hat_new.T

                # If subspace changed significantly, old regression data is stale
                subspace_shift = np.linalg.norm(P_hat_new - P_hat, 'fro')
                if subspace_shift > 0.3:
                    V_tilde = self.lam * np.eye(r)
                    b_tilde = np.zeros(r)

                U_hat = U_hat_new
                P_hat = P_hat_new

                # Subspace error (oracle diagnostic)
                P_true = env.segment_projector(k)
                metrics.subspace_error[t] = np.linalg.norm(P_hat - P_true, ord=2)

                # --- ACT: play UCB action for reward (no lost reward on probe rounds) ---
                Z       = action_set @ U_hat
                a_hat   = np.linalg.solve(V_tilde, b_tilde)
                beta_t  = self._beta_r(t)
                gamma_t = self._gamma(m_probe_seg, M_hat=M_hat_now)

                V_inv_Z = np.linalg.solve(V_tilde, Z.T).T
                ellip   = np.sqrt(np.einsum('ij,ij->i', Z, V_inv_Z))
                x_norms = np.linalg.norm(action_set, axis=1)
                ucb     = Z @ a_hat + beta_t * ellip + gamma_t * x_norms

                best_idx = int(np.argmax(ucb))
                x_dep    = action_set[best_idx]
                y_act    = env.step(x_dep, t)
                z_dep    = U_hat.T @ x_dep

                V_tilde = self.ff * V_tilde + np.outer(z_dep, z_dep)
                b_tilde = self.ff * b_tilde + z_dep * y_act

                r_t = float(x_dep @ env.theta[t])
                metrics.control_regret[t] = r_opt - r_t
                metrics.costed_regret[t]  = r_opt - r_t + self.c  # sensing cost only

            else:
                # ============================================================
                # EXPLOITATION ROUND  — all operations in R^r
                # ============================================================

                # Reduced features for all candidate actions: z = U_hat^T x  (n_a x r)
                Z = action_set @ U_hat            # (n_a, r)

                # Reduced ridge estimate
                a_hat = np.linalg.solve(V_tilde, b_tilde)  # r-vector

                # Confidence radii
                beta_t  = self._beta_r(t)
                gamma_t = self._gamma(
                    m_probe_seg,
                    M_hat=M_sum / max(m_probe_seg, 1)
                )

                # UCB index: z^T a_hat + beta * ||z||_{V_tilde^{-1}} + gamma * ||x||_2
                V_inv_Z = np.linalg.solve(V_tilde, Z.T).T   # (n_a, r)
                ellip   = np.sqrt(np.einsum('ij,ij->i', Z, V_inv_Z))  # (n_a,)
                x_norms = np.linalg.norm(action_set, axis=1)           # (n_a,)
                ucb     = Z @ a_hat + beta_t * ellip + gamma_t * x_norms

                best_idx = int(np.argmax(ucb))
                x_dep    = action_set[best_idx]

                y = env.step(x_dep, t)

                # Reduced feature of deployed action
                z_dep = U_hat.T @ x_dep           # r-vector

                # Update r x r design matrix and response (with optional forgetting)
                V_tilde = self.ff * V_tilde + np.outer(z_dep, z_dep)
                b_tilde = self.ff * b_tilde + z_dep * y

                r_t = float(x_dep @ env.theta[t])
                metrics.control_regret[t] = r_opt - r_t
                metrics.costed_regret[t]  = r_opt - r_t

        return metrics


# ---------------------------------------------------------------------------
# Baseline: Standard LinUCB (no subspace, full d x d design matrix)
# ---------------------------------------------------------------------------

class LinUCB:
    """
    Ridge regression UCB in full ambient space R^d.
    No probing, no subspace. Statistical regret O(d sqrt(T)).
    Resets at segment boundaries (same oracle info as SPSC).
    """

    def __init__(
        self,
        env: LowRankLDSEnvironment,
        probe_cost: float = 0.1,
        lam: float = 1.0,
        delta: float = 0.05,
        seed: int = 1,
        forgetting_factor: float = 1.0,
    ):
        self.env       = env
        self.c         = probe_cost
        self.lam       = lam
        self.delta     = delta
        self.rng       = np.random.default_rng(seed)
        self.ff        = forgetting_factor
        self.S         = env.S
        self.sigma_eps = env.sigma_eps
        self.L_x       = env.L_x

    def _beta(self, t: int) -> float:
        d   = self.env.d
        arg = max(1.0 + t * self.L_x ** 2 / self.lam, 1.0 + 1e-12)
        return (
            self.sigma_eps * np.sqrt(d * np.log(arg / self.delta))
            + np.sqrt(self.lam) * self.S
        )

    def run(self) -> RunMetrics:
        env     = self.env
        d, T    = env.d, env.T
        metrics = RunMetrics(name="LinUCB", T=T)

        V       = self.lam * np.eye(d)
        b       = np.zeros(d)
        current_k = -1

        for t in range(T):
            k = env.seg_of[t]
            if k != current_k:
                V = self.lam * np.eye(d)
                b = np.zeros(d)
                current_k = k

            action_set = env.get_action_set(t, rng=self.rng)
            r_opt      = env.optimal_reward(action_set, t)

            theta_hat  = np.linalg.solve(V, b)
            beta_t     = self._beta(t)

            V_inv_A = np.linalg.solve(V, action_set.T).T
            ucb     = (
                action_set @ theta_hat
                + beta_t * np.sqrt(np.einsum('ij,ij->i', action_set, V_inv_A))
            )
            x_dep = action_set[int(np.argmax(ucb))]
            y     = env.step(x_dep, t)

            V = self.ff * V + np.outer(x_dep, x_dep)
            b = self.ff * b + x_dep * y

            r_t = float(x_dep @ env.theta[t])
            metrics.control_regret[t] = r_opt - r_t
            metrics.costed_regret[t]  = r_opt - r_t

        return metrics


# ---------------------------------------------------------------------------
# Baseline: Oracle LinUCB (knows true P_k* at all times, operates in R^r)
# ---------------------------------------------------------------------------

class OracleLinUCB:
    """
    UCB with oracle knowledge of the true r-dim subspace P_k* at every t.
    Uses the same windowed design matrix as SPSC_Algorithm1 for a fair comparison:
    only exploitation rounds in [t-W, t) within the current segment contribute
    to V_tilde and b_tilde.
    """

    def __init__(
        self,
        env: LowRankLDSEnvironment,
        window: int = 100,
        lam: float = 1.0,
        delta: float = 0.05,
        seed: int = 2,
    ):
        self.env       = env
        self.W         = window
        self.lam       = lam
        self.delta     = delta
        self.rng       = np.random.default_rng(seed)
        self.S         = env.S
        self.sigma_eps = env.sigma_eps
        self.L_x       = env.L_x

    def _beta_r(self, n_exploit: int) -> float:
        r   = self.env.r
        effective_n = min(n_exploit, self.W)
        arg = max(1.0 + effective_n * self.L_x ** 2 / self.lam, 1.0 + 1e-12)
        return (
            self.sigma_eps * np.sqrt(r * np.log(arg / self.delta))
            + np.sqrt(self.lam) * self.S
        )

    def run(self) -> RunMetrics:
        env     = self.env
        d, r, T = env.d, env.r, env.T
        metrics = RunMetrics(name="Oracle-LinUCB", T=T)

        expl_buf: List[tuple] = []   # (z_s, y_s, s)
        current_k = -1

        for t in range(T):
            k = env.seg_of[t]
            if k != current_k:
                expl_buf  = []
                current_k = k

            U_true     = env.B_list[k]
            action_set = env.get_action_set(t, rng=self.rng)
            r_opt      = env.optimal_reward(action_set, t)

            # Windowed design — same W as SPSC_Algorithm1
            window_buf = [(z_s, y_s) for (z_s, y_s, s) in expl_buf if s >= t - self.W]
            V_tilde = self.lam * np.eye(r)
            b_tilde = np.zeros(r)
            for z_s, y_s in window_buf:
                V_tilde += np.outer(z_s, z_s)
                b_tilde += z_s * y_s

            Z       = action_set @ U_true
            a_hat   = np.linalg.solve(V_tilde, b_tilde)
            beta_t  = self._beta_r(len(window_buf))

            V_inv_Z = np.linalg.solve(V_tilde, Z.T).T
            ucb     = Z @ a_hat + beta_t * np.sqrt(np.einsum('ij,ij->i', Z, V_inv_Z))

            x_dep  = action_set[int(np.argmax(ucb))]
            y      = env.step(x_dep, t)
            z_dep  = U_true.T @ x_dep

            expl_buf.append((z_dep, y, t))
            if len(expl_buf) > self.W + 10:
                expl_buf = [(z_s, y_s, s) for (z_s, y_s, s) in expl_buf
                            if s >= t - self.W]

            r_t = float(x_dep @ env.theta[t])
            metrics.control_regret[t] = r_opt - r_t
            metrics.costed_regret[t]  = r_opt - r_t

        return metrics
