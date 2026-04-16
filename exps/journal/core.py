"""
Shared utilities for the journal-paper theory-validating experiments.

Model (matches journal.tex Section "Supporting Experiments"):
    theta_t = B_k^* w_t                       t in segment k
    w_t     = A_k w_{t-1} + eta_t             eta_t ~ N(0, I_r)
    y_t     = x_t^T theta_t + eps_t           eps_t ~ N(0, sigma_eps^2)

    B_k^*   ~ uniform on Stiefel manifold (d x r orthonormal frames)
    A_k     = 0.5 * I_r
    sigma_eps = 1
    probes  u_t ~ N(0, I_d) (isotropic Gaussian)

Probe-side lifted estimator (Gaussian probes)
---------------------------------------------
For u ~ N(0, I_d):
    E[(u^T M u) u u^T] = tr(M) I_d + 2 M                 =: K(M)
    K^{-1}(N) = (N - tr(N)/(d+2) I_d) / 2

Per-round lifted observation:
    s_t = y_t^2 - sigma_eps^2   (unbiased for (u_t^T theta_t)^2)
    G_t = K^{-1}(s_t * u_t u_t^T)

Estimator:
    M_hat = (1/m) sum_t G_t    ->   E[M_hat | theta_{1:m}] = (1/m) sum_t theta_t theta_t^T
    top-r eigenspace of M_hat  ->   estimate of span(B_k^*)
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional


# ---------------------------------------------------------------------------
# 1. Model generation
# ---------------------------------------------------------------------------

def stiefel(d: int, r: int, rng: np.random.Generator) -> np.ndarray:
    """Uniform random d x r orthonormal frame (first r columns of Haar Q)."""
    A = rng.standard_normal((d, r))
    Q, R = np.linalg.qr(A)
    # Fix sign so the distribution is exactly Haar-invariant.
    Q = Q * np.sign(np.diag(R))
    return Q[:, :r]


def make_segments(B_list: List[np.ndarray],
                  segment_lengths: List[int],
                  rng: np.random.Generator,
                  rho: float = 0.5,
                  sigma_eta: float = 1.0,
                  static: bool = False) -> np.ndarray:
    """
    Generate the theta_t trajectory for K segments.

    If static=True, theta is constant within each segment (drawn once as
    theta_k = B_k w_k with w_k ~ N(0, I_r) normalized to unit length).
    This is the piecewise-stationary setting used in, e.g., Experiment 3
    where the rank-vs-dimension comparison requires the learner to converge
    to a fixed best arm within each segment.

    Otherwise, theta_t follows the AR(1) LDS
        w_t = rho w_{t-1} + sigma_eta eta_t,     eta_t ~ N(0, I_r)
    and theta_t = B_k w_t.

    Returns theta of shape (T, d).
    """
    r = B_list[0].shape[1]
    d = B_list[0].shape[0]
    T = sum(segment_lengths)
    theta = np.empty((T, d))
    t = 0
    if static:
        for k, Bk in enumerate(B_list):
            w = rng.standard_normal(r)
            w = w / np.linalg.norm(w)         # unit-norm latent
            theta_k = Bk @ w
            L = segment_lengths[k]
            theta[t:t + L] = theta_k
            t += L
        return theta

    A = rho * np.eye(r)
    for k, Bk in enumerate(B_list):
        # Start each segment from the stationary distribution of the AR(1):
        # Var(w) = sigma_eta^2 / (1 - rho^2) * I_r.
        w = (sigma_eta / np.sqrt(1.0 - rho**2)) * rng.standard_normal(r)
        L = segment_lengths[k]
        for _ in range(L):
            w = A @ w + sigma_eta * rng.standard_normal(r)
            theta[t] = Bk @ w
            t += 1
    return theta


# ---------------------------------------------------------------------------
# 2. Lifted operator and subspace estimator
# ---------------------------------------------------------------------------

def K_inv_gaussian(N: np.ndarray, d: int) -> np.ndarray:
    """K^{-1} for probes u ~ N(0, I_d): K(M) = tr(M) I + 2M."""
    return 0.5 * (N - (np.trace(N) / (d + 2.0)) * np.eye(d))


def K_inv_sphere(N: np.ndarray, d: int) -> np.ndarray:
    """K^{-1} for sphere probes u = sqrt(d) z/||z||: K(M) = (d/(d+2))*(tr(M) I + 2 M).
    Same-signal-norm variant with lower variance than Gaussian probes — useful
    when finite-sample slopes are what we care about.
    """
    c = (d + 2.0) / (2.0 * d)
    return c * N - (np.trace(N) / (2.0 * d)) * np.eye(d)


def draw_probes(m: int, d: int, rng: np.random.Generator,
                kind: str = 'gaussian') -> np.ndarray:
    if kind == 'gaussian':
        return rng.standard_normal((m, d))
    elif kind == 'sphere':
        Z = rng.standard_normal((m, d))
        Z /= np.linalg.norm(Z, axis=1, keepdims=True) + 1e-12
        return np.sqrt(d) * Z
    else:
        raise ValueError(kind)


def subspace_from_probes(U_probes: np.ndarray,
                         Y_probes: np.ndarray,
                         sigma_eps: float,
                         d: int,
                         r: int,
                         probe_kind: str = 'gaussian') -> Tuple[np.ndarray, np.ndarray]:
    """
    Given m probe vectors (rows of U_probes, shape m x d) and observations
    Y_probes (shape m), return:
        U_hat : d x r orthonormal top-r eigenbasis of M_hat
        M_hat : d x d symmetric estimate of (1/m) sum theta_t theta_t^T

    probe_kind selects the appropriate K^{-1} operator.
    """
    m = U_probes.shape[0]
    s = Y_probes**2 - sigma_eps**2
    M_raw = (U_probes.T * s) @ U_probes / m
    if probe_kind == 'gaussian':
        M_hat = K_inv_gaussian(M_raw, d)
    elif probe_kind == 'sphere':
        M_hat = K_inv_sphere(M_raw, d)
    else:
        raise ValueError(probe_kind)
    M_hat = 0.5 * (M_hat + M_hat.T)
    eigvals, eigvecs = np.linalg.eigh(M_hat)
    U_hat = eigvecs[:, -r:]
    return U_hat, M_hat


def projector_error(U_hat: np.ndarray, B_true: np.ndarray) -> float:
    """Operator-norm distance between projectors P_hat and P_true."""
    P_hat = U_hat @ U_hat.T
    P_true = B_true @ B_true.T
    return float(np.linalg.norm(P_hat - P_true, ord=2))


# ---------------------------------------------------------------------------
# 3. Action sets + oracle
# ---------------------------------------------------------------------------

def draw_actions(n_actions: int, d: int,
                 rng: np.random.Generator) -> np.ndarray:
    """n_actions fresh unit vectors in R^d, returned as (n_actions, d)."""
    X = rng.standard_normal((n_actions, d))
    X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
    return X


def optimal_reward(actions: np.ndarray, theta_t: np.ndarray) -> float:
    """max_a a^T theta_t over the finite action set."""
    return float(np.max(actions @ theta_t))


# ---------------------------------------------------------------------------
# 4. Projected ridge-UCB (r-dimensional)
# ---------------------------------------------------------------------------

@dataclass
class RidgeUCBState:
    dim: int
    lam: float = 1.0
    V: np.ndarray = None          # dim x dim
    b: np.ndarray = None          # dim
    n: int = 0

    def __post_init__(self):
        self.V = self.lam * np.eye(self.dim)
        self.b = np.zeros(self.dim)

    def reset(self):
        self.V = self.lam * np.eye(self.dim)
        self.b = np.zeros(self.dim)
        self.n = 0

    def update(self, phi: np.ndarray, y: float):
        self.V += np.outer(phi, phi)
        self.b += y * phi
        self.n += 1

    def ucb_pick(self, feats: np.ndarray, beta: float) -> int:
        """feats: n x dim. Returns argmax of mean + beta * ellipsoid norm."""
        Vinv = np.linalg.inv(self.V)
        theta_hat = Vinv @ self.b
        means = feats @ theta_hat
        # ||phi||_{V^{-1}} for each row
        quad = np.einsum('ij,jk,ik->i', feats, Vinv, feats)
        widths = beta * np.sqrt(np.maximum(quad, 0.0))
        return int(np.argmax(means + widths))


def beta_schedule(dim: int, n: int, sigma_eps: float,
                  lam: float = 1.0, S: float = 1.0,
                  delta: float = 0.05, L_x: float = 1.0) -> float:
    """Standard self-normalized confidence width (Abbasi-Yadkori et al., 2011)."""
    arg = max(1.0 + n * L_x**2 / lam, 1.0 + 1e-12)
    return sigma_eps * np.sqrt(dim * np.log(arg / delta)) + np.sqrt(lam) * S


# ---------------------------------------------------------------------------
# 5. Full segment runners: probe phase then exploit phase
# ---------------------------------------------------------------------------

def run_segment_projected(theta_seg: np.ndarray,
                          sigma_eps: float,
                          n_actions: int,
                          m_probes: int,
                          r: int,
                          rng: np.random.Generator,
                          probe_cost: float = 0.0,
                          U_oracle: Optional[np.ndarray] = None,
                          probe_scale: float = 1.0,
                          probe_sampler=None,
                          fixed_actions: Optional[np.ndarray] = None) -> Tuple[float, float]:
    """
    Run ETC-style probing + projected ridge-UCB on one segment of length L.

    Returns (control_regret, total_cost_regret).
    If U_oracle is provided, skip probing and use the oracle subspace.
    """
    L, d = theta_seg.shape
    control_reg = 0.0
    cost_reg = 0.0

    # -------- Probe phase --------
    if U_oracle is not None:
        U_hat = U_oracle
        m_used = 0
    else:
        m_used = min(m_probes, L)
        if probe_sampler is None:
            U_probes = probe_scale * rng.standard_normal((m_used, d))
        else:
            U_probes = probe_sampler(m_used, d, rng)
        Y_probes = np.empty(m_used)
        for i in range(m_used):
            t = i
            noise = sigma_eps * rng.standard_normal()
            Y_probes[i] = U_probes[i] @ theta_seg[t] + noise
            # Probes incur cost; reward of the probe is u_t^T theta_t
            action_set = draw_actions(n_actions, d, rng)
            r_opt = optimal_reward(action_set, theta_seg[t])
            control_reg += r_opt - U_probes[i] @ theta_seg[t]
            cost_reg += r_opt - U_probes[i] @ theta_seg[t] + probe_cost
        U_hat, _ = subspace_from_probes(U_probes, Y_probes, sigma_eps, d, r)

    # -------- Exploit phase: projected ridge-UCB --------
    state = RidgeUCBState(dim=r, lam=1.0)
    for t in range(m_used, L):
        if fixed_actions is not None:
            action_set = fixed_actions
        else:
            action_set = draw_actions(n_actions, d, rng)
        feats = action_set @ U_hat     # n_actions x r
        beta = beta_schedule(r, state.n, sigma_eps)
        i_star = state.ucb_pick(feats, beta)
        x_t = action_set[i_star]
        r_opt = optimal_reward(action_set, theta_seg[t])
        reward = x_t @ theta_seg[t]
        y = reward + sigma_eps * rng.standard_normal()
        state.update(feats[i_star], y)
        control_reg += r_opt - reward
        cost_reg += r_opt - reward
    return float(control_reg), float(cost_reg)


def run_segment_ambient(theta_seg: np.ndarray,
                        sigma_eps: float,
                        n_actions: int,
                        rng: np.random.Generator,
                        fixed_actions: Optional[np.ndarray] = None) -> float:
    """Ambient LinUCB baseline: no probe phase, ridge-UCB in R^d."""
    L, d = theta_seg.shape
    state = RidgeUCBState(dim=d, lam=1.0)
    reg = 0.0
    for t in range(L):
        if fixed_actions is not None:
            action_set = fixed_actions
        else:
            action_set = draw_actions(n_actions, d, rng)
        beta = beta_schedule(d, state.n, sigma_eps)
        i_star = state.ucb_pick(action_set, beta)
        x_t = action_set[i_star]
        r_opt = optimal_reward(action_set, theta_seg[t])
        reward = x_t @ theta_seg[t]
        y = reward + sigma_eps * rng.standard_normal()
        state.update(x_t, y)
        reg += r_opt - reward
    return float(reg)
