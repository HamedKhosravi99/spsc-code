"""
Forest Covertype *real-data-calibrated* bandit environment.

Uses UCI Forest Covertype (581K samples, 54 features, 7 cover types).
All parameters derived from real data:
  - Features: 10 quantitative + 45 pairwise interactions = d=55
  - theta_k: per-segment OLS fit of features -> cover type labels
  - Segments: data sorted by elevation creates natural non-stationarity
    (different elevations -> different forest types -> different theta)
  - Low-rank: 7 cover types with correlated features -> documented r=3-5

Data auto-downloaded via sklearn.
"""

import numpy as np
from sklearn.datasets import fetch_covtype
from sklearn.preprocessing import StandardScaler


class RealCovtypeEnvironment:
    """
    Real-data-calibrated Covertype bandit.

    Segments created by sorting data by elevation (natural regime changes).
    theta_k = per-segment OLS of features -> cover-type labels.
    Reward follows paper's linear model: y = x^T theta_t + eps.
    """

    def __init__(
        self,
        r: int = 3,
        n_actions: int = 40,
        segment_size: int = 2000,
        n_segments: int = 20,
        seed: int = 42,
    ):
        self.r = r
        self.n_actions = n_actions
        self.rng = np.random.default_rng(seed)

        self._load_and_prepare_data()
        self._build_segments(segment_size, n_segments)
        self._build_theta_and_subspaces()

        self.L_x = 1.0
        self.L = 1.0
        self.L_eps = 5.0
        self.spectral_radius = 0.0
        self.sigma_eta = 0.0

    def _load_and_prepare_data(self):
        """Load Covertype, build rich features, sort by elevation."""
        X_raw, y_raw = fetch_covtype(return_X_y=True)

        # 10 quantitative features: elevation, aspect, slope, distances, hillshade
        X_quant = X_raw[:, :10].astype(float)
        scaler = StandardScaler()
        X_quant = scaler.fit_transform(X_quant)

        # Pairwise interactions: 10*9/2 = 45 features
        interactions = []
        n_q = X_quant.shape[1]
        for i in range(n_q):
            for j in range(i + 1, n_q):
                interactions.append(X_quant[:, i] * X_quant[:, j])
        X_inter = np.column_stack(interactions)

        # Full feature matrix: 10 + 45 = 55 features
        X_full = np.hstack([X_quant, X_inter])

        # Normalize rows to unit norm
        norms = np.linalg.norm(X_full, axis=1, keepdims=True)
        X_full /= np.maximum(norms, 1e-8)

        # Sort by elevation (column 0 of raw data) to create non-stationarity
        sort_idx = np.argsort(X_raw[:, 0])
        self._features = X_full[sort_idx]
        self._labels = (y_raw[sort_idx].astype(float) - 4.0)  # center around 0
        self.d = X_full.shape[1]
        self._n_total = len(self._features)

    def _build_segments(self, segment_size, n_segments):
        """Split sorted data into segments."""
        self.K = n_segments
        # Use a subset of data to keep T manageable
        total_needed = segment_size * n_segments
        if total_needed > self._n_total:
            segment_size = self._n_total // n_segments
            total_needed = segment_size * n_segments

        # Sample evenly from the sorted data
        step = self._n_total // total_needed
        indices = np.arange(0, self._n_total, step)[:total_needed]
        self._seg_features = self._features[indices]
        self._seg_labels = self._labels[indices]

        self.T = total_needed
        self.segment_lengths = [segment_size] * self.K
        self.segment_lengths[-1] += self.T - sum(self.segment_lengths)

        self.tau = [0]
        for l in self.segment_lengths[:-1]:
            self.tau.append(self.tau[-1] + l)

        self.seg_of = np.zeros(self.T, dtype=int)
        for k, start in enumerate(self.tau):
            self.seg_of[start:start + self.segment_lengths[k]] = k

    def _build_theta_and_subspaces(self):
        """Per-segment OLS of features -> labels gives theta_k."""
        d = self.d
        self.theta = np.zeros((self.T, d))
        self.B_list = []
        residuals = []

        for k in range(self.K):
            s = self.tau[k]
            e = s + self.segment_lengths[k]

            X_k = self._seg_features[s:e]
            y_k = self._seg_labels[s:e]

            # Ridge OLS
            lam = 1.0
            theta_k = np.linalg.solve(X_k.T @ X_k + lam * np.eye(d), X_k.T @ y_k)
            resid = y_k - X_k @ theta_k
            residuals.extend(resid.tolist())
            self.theta[s:e] = theta_k[np.newaxis, :]

            # Subspace: top-r directions
            W = np.diag(np.abs(y_k) + 0.1)
            _, _, Vt = np.linalg.svd(W @ X_k, full_matrices=False)
            B_k = Vt[:self.r].T
            Q, _ = np.linalg.qr(
                np.column_stack([theta_k.reshape(-1, 1), B_k])
            )
            B_k = Q[:, :self.r]
            self.B_list.append(B_k)

        self.sigma_eps = float(np.std(residuals))
        self.S = float(np.max(np.linalg.norm(self.theta, axis=1)))

    # ------------------------------------------------------------------
    # Per-round interface
    # ------------------------------------------------------------------

    def get_action_set(self, t: int, rng=None):
        _rng = rng if rng is not None else self.rng
        # Sample actions from current segment's data neighborhood
        k = self.seg_of[t]
        s = self.tau[k]
        e = s + self.segment_lengths[k]
        n = min(self.n_actions, e - s)
        chosen = _rng.choice(e - s, size=n, replace=False) + s
        return self._seg_features[chosen]

    def step(self, action: np.ndarray, t: int) -> float:
        """Linear model: y = x^T theta_t + eps. theta from real OLS."""
        eps = self.rng.normal(0.0, self.sigma_eps)
        eps = np.clip(eps, -self.L_eps, self.L_eps)
        return float(action @ self.theta[t]) + eps

    def optimal_reward(self, action_set: np.ndarray, t: int) -> float:
        return float(np.max(action_set @ self.theta[t]))

    def segment_projector(self, k: int) -> np.ndarray:
        B = self.B_list[k]
        return B @ B.T

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def svd_spectrum(self):
        """SVD spectrum of stacked segment-theta matrix."""
        thetas = np.array([self.theta[self.tau[k]] for k in range(self.K)])
        _, svals, _ = np.linalg.svd(thetas, full_matrices=False)
        return svals / svals.sum()

    def label_pca_spectrum(self):
        """PCA of label-weighted feature matrix -> factor structure evidence."""
        X = self._seg_features
        y = self._seg_labels
        Xw = X * np.abs(y[:, None])
        Xw -= Xw.mean(axis=0, keepdims=True)
        _, svals, _ = np.linalg.svd(Xw, full_matrices=False)
        var_explained = svals ** 2
        return var_explained / var_explained.sum()
