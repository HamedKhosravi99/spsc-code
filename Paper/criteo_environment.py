"""
Criteo environment for the Low-Rank LDS Bandit.

Reproduces the non-stationary Criteo benchmark from Russac et al. (NeurIPS 2019):
  - d=50 features (SVD-projected one-hot encoded categoricals)
  - T=8000 horizon with a single change-point at t=4000
  - Before change: theta_t = theta_star (fitted from data)
  - After change:  theta_t = theta_star with 60% of coordinates sign-flipped
  - Each round: 2 candidate actions (one clicked, one non-clicked context)
  - Reward: x^T theta_t + N(0, sigma_eps)

Matches the LowRankLDSEnvironment interface so SPSC_Algorithm1 and LinUCB
run unmodified.
"""

import os
import numpy as np


class CriteoEnvironment:
    """
    Criteo benchmark environment matching the LowRankLDSEnvironment interface.

    Parameters
    ----------
    data_path   : path to criteo_processed.npz
    T           : horizon (default 8000)
    change_t    : change-point time (default 4000)
    flip_frac   : fraction of theta_star coordinates to flip (default 0.6)
    sigma_eps   : noise std (default 0.15, matching Russac et al.)
    seed        : RNG seed
    r           : rank for subspace estimation (default 1)
    """

    def __init__(
        self,
        data_path: str,
        T: int = 8000,
        change_t: int = 4000,
        flip_frac: float = 0.6,
        sigma_eps: float = 0.15,
        seed: int = 42,
        r: int = 1,
    ):
        self.T = T
        self.change_t = change_t
        self.flip_frac = flip_frac
        self.sigma_eps = sigma_eps
        self.rng = np.random.default_rng(seed)
        self.r = r

        # Load processed data
        data = np.load(data_path)
        self.X_clicked = data["X_clicked"]
        self.X_nonclicked = data["X_nonclicked"]
        theta_star = data["theta_star"].astype(np.float64)

        self.d = theta_star.shape[0]
        self.K = 2
        self.n_actions = 2

        # Interface constants
        self.L_x = 1.0
        self.L = 1.0
        self.L_eps = 1.0
        self.spectral_radius = 0.0   # static within each segment
        self.sigma_eta = 0.0

        # Build theta trajectory
        self._build_theta(theta_star)
        self._build_segments()
        self._build_subspaces()

        self.S = float(np.max(np.linalg.norm(self.theta, axis=1)))

    def _build_theta(self, theta_star):
        """
        theta_t = theta_star for t < change_t,
        theta_t = theta_flipped for t >= change_t.

        Flipped: 60% of coordinates have their sign negated.
        """
        self.theta_star = theta_star.copy()

        # Select coordinates to flip (fixed for this seed)
        n_flip = int(self.flip_frac * self.d)
        flip_idx = self.rng.choice(self.d, size=n_flip, replace=False)

        self.theta_flipped = theta_star.copy()
        self.theta_flipped[flip_idx] *= -1.0
        self.flip_idx = flip_idx

        # Build full trajectory
        self.theta = np.zeros((self.T, self.d))
        self.theta[:self.change_t] = self.theta_star[np.newaxis, :]
        self.theta[self.change_t:] = self.theta_flipped[np.newaxis, :]

        # w trajectory (for interface compatibility)
        self.w = np.zeros((self.T, self.r))
        # Project onto segment subspace
        # Will be filled after _build_subspaces

    def _build_segments(self):
        """Two segments: [0, change_t) and [change_t, T)."""
        self.tau = [0, self.change_t]
        self.segment_lengths = [self.change_t, self.T - self.change_t]

        self.seg_of = np.zeros(self.T, dtype=int)
        self.seg_of[self.change_t:] = 1

    def _build_subspaces(self):
        """
        Build rank-r subspaces for each segment.

        For each segment, the "subspace" is the top-r left singular vectors
        of the segment's theta matrix. Since theta is constant within each
        segment, the rank-1 subspace is just the direction of theta.
        """
        self.B_list = []

        for k in range(self.K):
            start = self.tau[k]
            end = start + self.segment_lengths[k]
            seg_theta = self.theta[start:end]

            # SVD to get rank-r subspace
            U, S_vals, Vt = np.linalg.svd(seg_theta, full_matrices=False)
            B_k = Vt[:self.r].T  # (d, r)

            # Ensure orthonormal
            Q, _ = np.linalg.qr(B_k)
            B_k = Q[:, :self.r]
            self.B_list.append(B_k)

            # Fill w trajectory
            for t in range(start, end):
                self.w[t] = B_k.T @ self.theta[t]

    # ------------------------------------------------------------------
    # Per-round interface (matches LowRankLDSEnvironment)
    # ------------------------------------------------------------------

    def get_action_set(self, t: int, rng=None):
        """
        Return 2 x d action matrix: one clicked context, one non-clicked.
        """
        _rng = rng if rng is not None else self.rng
        actions = np.zeros((2, self.d))

        idx_c = _rng.integers(0, len(self.X_clicked))
        idx_nc = _rng.integers(0, len(self.X_nonclicked))

        actions[0] = self.X_clicked[idx_c]
        actions[1] = self.X_nonclicked[idx_nc]

        return actions

    def step(self, action: np.ndarray, t: int) -> float:
        """Deploy action at round t, return noisy reward."""
        eps = self.rng.normal(0.0, self.sigma_eps)
        return float(action @ self.theta[t]) + eps

    def optimal_reward(self, action_set: np.ndarray, t: int) -> float:
        """max_{x in action_set} x^T theta_t (noiseless)."""
        return float(np.max(action_set @ self.theta[t]))

    def segment_projector(self, k: int) -> np.ndarray:
        """True segment projector P_k = B_k B_k^T."""
        B = self.B_list[k]
        return B @ B.T
