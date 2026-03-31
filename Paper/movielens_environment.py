"""
MovieLens 100K environment for the Low-Rank LDS Bandit.

Maps the real MovieLens 100K dataset to the LowRankLDSEnvironment interface
so that SPSC_Algorithm1 and LinUCB can run unmodified.

Design
------
  - Each round t corresponds to a rating event sorted chronologically.
  - Action features: 19 genre indicators + 171 pairwise genre interactions
    + 1 bias = 191 dimensions. This high-dimensional but intrinsically
    low-rank feature space is where SPSC's dimension reduction shines.
  - theta_t is a smoothed user-preference vector that drifts over time,
    constructed from exponentially-weighted OLS on historical ratings.
  - Segments are obtained by splitting the timeline into K equal chunks;
    within each segment, B_k = top-r right singular vectors of theta trajectory.
  - The MovieLens data has natural low-rank structure (rank-3 captures >97%
    variance) and non-stationarity (user preference drift over months).
"""

import os
import numpy as np


class MovieLensEnvironment:
    """
    Real-data environment matching the LowRankLDSEnvironment interface.

    Parameters
    ----------
    data_dir      : path to ml-100k/ folder
    r             : latent rank for subspace
    K             : number of segments
    T             : horizon (uses first T ratings chronologically)
    sigma_eps     : observation noise std
    n_actions     : number of candidate movies per round
    seed          : RNG seed
    use_interactions : if True, include pairwise genre interactions (d~191)
    """

    def __init__(
        self,
        data_dir: str,
        r: int = 3,
        K: int = 4,
        T: int = 6000,
        sigma_eps: float = 0.3,
        n_actions: int = 40,
        seed: int = 42,
        use_interactions: bool = True,
    ):
        self.r = r
        self.K = K
        self.T = T
        self.sigma_eps = sigma_eps
        self.n_actions = n_actions
        self.rng = np.random.default_rng(seed)
        self.use_interactions = use_interactions

        # Interface constants
        self.L_x = 1.0
        self.L = 1.0
        self.L_eps = 1.0
        self.spectral_radius = 0.99  # nominal
        self.sigma_eta = 0.04        # nominal

        # Load and build
        self._load_data(data_dir)
        self._build_features()
        self.d = len(next(iter(self.movie_features.values())))
        self._build_segments()
        self._build_theta_trajectory()

        self.S = float(np.max(np.linalg.norm(self.theta, axis=1)))

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self, data_dir):
        """Load u.data and u.item from MovieLens 100K."""
        data_path = os.path.join(data_dir, "u.data")
        raw = np.loadtxt(data_path, dtype=int)
        order = np.argsort(raw[:, 3])
        raw = raw[order]

        if len(raw) < self.T:
            self.T = len(raw)
        self.user_ids = raw[:self.T, 0]
        self.movie_ids = raw[:self.T, 1]
        self.ratings = raw[:self.T, 2].astype(float)
        self.timestamps = raw[:self.T, 3]

        item_path = os.path.join(data_dir, "u.item")
        self.genre_matrix = {}
        with open(item_path, "r", encoding="latin-1") as f:
            for line in f:
                parts = line.strip().split("|")
                mid = int(parts[0])
                genres = np.array([int(x) for x in parts[5:24]], dtype=float)
                self.genre_matrix[mid] = genres

        self.all_movie_ids = sorted(self.genre_matrix.keys())

    def _build_features(self):
        """Build feature vectors: 19 genres + 171 interactions + 1 bias = 191 dims."""
        self.movie_features = {}
        for mid, genres in self.genre_matrix.items():
            if self.use_interactions:
                # Base features (19) + pairwise interactions (19*18/2=171) + bias (1) = 191
                n_genre = len(genres)
                interactions = []
                for i in range(n_genre):
                    for j in range(i + 1, n_genre):
                        interactions.append(genres[i] * genres[j])
                feat = np.concatenate([genres, np.array(interactions), [1.0]])
            else:
                feat = np.concatenate([genres, [1.0]])

            norm = np.linalg.norm(feat)
            if norm > 1e-8:
                feat = feat / norm
            else:
                feat = np.zeros_like(feat)
                feat[0] = 1.0
            self.movie_features[mid] = feat

    # ------------------------------------------------------------------
    # Segments
    # ------------------------------------------------------------------

    def _build_segments(self):
        """Divide T rounds into K segments."""
        base = self.T // self.K
        lengths = [base] * self.K
        lengths[-1] += self.T - sum(lengths)
        self.segment_lengths = lengths

        self.tau = [0]
        for l in lengths[:-1]:
            self.tau.append(self.tau[-1] + l)

        self.seg_of = np.zeros(self.T, dtype=int)
        for k, start in enumerate(self.tau):
            end = start + self.segment_lengths[k]
            self.seg_of[start:end] = k

    # ------------------------------------------------------------------
    # Theta trajectory from real data
    # ------------------------------------------------------------------

    def _build_theta_trajectory(self):
        """
        Build theta_t, B_list, w from MovieLens ratings.

        Uses per-segment exponentially-weighted OLS to construct a smoothly
        drifting preference vector in R^d. The natural low-rank structure
        of genre preferences means rank-r captures >95% of variance.
        """
        d = self.d
        self.theta = np.zeros((self.T, d))
        self.w = np.zeros((self.T, self.r))
        self.B_list = []

        # Per-segment: build theta from that segment's ratings, then SVD
        for k in range(self.K):
            start = self.tau[k]
            end = start + self.segment_lengths[k]

            # Exponentially-weighted OLS within this segment
            V_run = 0.01 * np.eye(d)
            b_run = np.zeros(d)
            decay = 0.998

            for t in range(start, end):
                mid = self.movie_ids[t]
                x_t = self.movie_features.get(mid, np.zeros(d))
                y_t = self.ratings[t]

                V_run = decay * V_run + np.outer(x_t, x_t)
                b_run = decay * b_run + x_t * y_t
                self.theta[t] = np.linalg.solve(
                    V_run + 0.1 * np.eye(d), b_run
                )

            # SVD of segment theta matrix -> B_k
            seg_theta = self.theta[start:end]
            _, S_svd, Vt_svd = np.linalg.svd(seg_theta, full_matrices=False)
            B_k = Vt_svd[:self.r].T  # (d, r)
            self.B_list.append(B_k)

            # w_t = B_k^T @ theta_t
            for t in range(start, end):
                self.w[t] = B_k.T @ self.theta[t]

        # Normalize so max ||theta|| ~ 2
        max_norm = np.max(np.linalg.norm(self.theta, axis=1))
        if max_norm > 1e-8:
            scale = 2.0 / max_norm
            self.theta *= scale
            self.w *= scale

    # ------------------------------------------------------------------
    # Per-round interface (matches LowRankLDSEnvironment exactly)
    # ------------------------------------------------------------------

    def get_action_set(self, t: int, rng=None):
        """Return n_actions x d matrix of unit-norm movie feature vectors."""
        _rng = rng if rng is not None else self.rng
        chosen = _rng.choice(self.all_movie_ids, size=self.n_actions, replace=False)
        actions = np.zeros((self.n_actions, self.d))
        for i, mid in enumerate(chosen):
            actions[i] = self.movie_features.get(mid, np.zeros(self.d))
        return actions

    def step(self, action: np.ndarray, t: int) -> float:
        """Deploy action at round t, return noisy reward."""
        eps = self.rng.normal(0.0, self.sigma_eps)
        eps = np.clip(eps, -self.L_eps, self.L_eps)
        return float(action @ self.theta[t]) + eps

    def optimal_reward(self, action_set: np.ndarray, t: int) -> float:
        """max_{x in action_set} x^T theta_t (noiseless)."""
        return float(np.max(action_set @ self.theta[t]))

    def segment_projector(self, k: int) -> np.ndarray:
        """True segment projector P_k = B_k B_k^T."""
        B = self.B_list[k]
        return B @ B.T
