"""
Criteo Display Advertising — Real-Data Bandit Environment.

REAL DATA ONLY.  No synthetic fallback.  The constructor REQUIRES
`data_path` to point at the Criteo Display Advertising Challenge
TSV (`train.txt`) released by Criteo on Kaggle (2014).

Format expected at `data_path`:
  Tab-separated, no header.  One row per ad impression, columns:
    label, I1..I13, C1..C26
  - label in {0, 1}                         (click outcome)
  - I1..I13                                  13 integer features
  - C1..C26                                  26 hashed categorical features
  Missing values are blank strings.

Download:
  https://www.kaggle.com/c/criteo-display-ad-challenge/data
  (or the public mirror at https://labs.criteo.com/2014/02/kaggle-display-advertising-challenge-dataset/)
"""

import os
import numpy as np


N_NUM = 13
N_CAT = 26
HASH_BUCKETS = 64


class CriteoEnvironment:
    """
    Real-data Criteo display-advertising bandit.

    Parameters
    ----------
    data_path : path to Criteo train.txt (TSV).  REQUIRED.
    d         : feature dimension after random projection
    r         : latent rank for subspace
    K         : number of segments
    T         : horizon
    n_actions : candidate action vectors per round
    seed      : RNG seed
    max_rows  : cap on rows loaded from the TSV
    """

    def __init__(
        self,
        data_path: str,
        d: int = 93,
        r: int = 3,
        K: int = 8,
        T: int = 5000,
        n_actions: int = 40,
        sigma_eps: float = 0.3,
        seed: int = 42,
        max_rows: int = 200_000,
    ):
        if data_path is None or not os.path.isfile(data_path):
            raise FileNotFoundError(
                "CriteoEnvironment requires the real Criteo Display "
                "Advertising Challenge TSV (train.txt). "
                f"Got data_path={data_path!r}."
            )

        self.r = r
        self.K = K
        self.T = T
        self.n_actions = n_actions
        self.sigma_eps = sigma_eps
        self.rng = np.random.default_rng(seed)

        self.L_x = 1.0
        self.L = 1.0
        self.L_eps = 3.0
        self.spectral_radius = 0.0
        self.sigma_eta = 0.0

        self._load_real_data(data_path, d, max_rows)
        self.d = self._X.shape[1]
        self._build_segments()
        self._build_theta_and_subspaces()
        self._current_actions = None

    # ------------------------------------------------------------------
    # Loader
    # ------------------------------------------------------------------
    def _load_real_data(self, data_path, d, max_rows):
        labels = []
        nums = []
        cats = []

        with open(data_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= max_rows:
                    break
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 1 + N_NUM + N_CAT:
                    continue
                labels.append(int(parts[0]))
                num_row = []
                for v in parts[1:1 + N_NUM]:
                    num_row.append(float(v) if v != "" else 0.0)
                nums.append(num_row)
                cats.append(parts[1 + N_NUM:1 + N_NUM + N_CAT])

        if len(labels) == 0:
            raise ValueError(f"Criteo TSV at {data_path} parsed zero rows.")

        labels = np.asarray(labels, dtype=np.float32)
        nums = np.asarray(nums, dtype=np.float32)
        nums = np.log1p(np.clip(nums, 0, None))
        mu = nums.mean(axis=0, keepdims=True)
        sd = nums.std(axis=0, keepdims=True) + 1e-6
        nums = (nums - mu) / sd

        n = len(cats)
        cat_dim = N_CAT * HASH_BUCKETS
        cat_mat = np.zeros((n, cat_dim), dtype=np.float32)
        for i, row in enumerate(cats):
            for j, v in enumerate(row):
                if v == "":
                    continue
                bucket = (hash((j, v)) % HASH_BUCKETS)
                cat_mat[i, j * HASH_BUCKETS + bucket] = 1.0

        X_full = np.concatenate([nums, cat_mat], axis=1)

        rng = np.random.default_rng(0)
        if X_full.shape[1] > d:
            P = rng.standard_normal((X_full.shape[1], d)).astype(np.float32)
            P /= np.sqrt(d)
            X_full = X_full @ P
        elif X_full.shape[1] < d:
            extra = rng.standard_normal((n, d - X_full.shape[1])).astype(np.float32) * 0.01
            X_full = np.concatenate([X_full, extra], axis=1)

        norms = np.linalg.norm(X_full, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-8)
        self._X = (X_full / norms).astype(np.float64)
        self._dose = labels.astype(np.float64)

    # ------------------------------------------------------------------
    # Segmentation + theta build
    # ------------------------------------------------------------------
    def _build_segments(self):
        base = self.T // self.K
        self.segment_lengths = [base] * self.K
        self.segment_lengths[-1] += self.T - sum(self.segment_lengths)

        self.tau = [0]
        for l in self.segment_lengths[:-1]:
            self.tau.append(self.tau[-1] + l)

        self.seg_of = np.zeros(self.T, dtype=int)
        for k, s in enumerate(self.tau):
            self.seg_of[s:s + self.segment_lengths[k]] = k

    def _build_theta_and_subspaces(self):
        d = self._X.shape[1]
        n_rows = len(self._X)
        self.theta = np.zeros((self.T, d))
        self.B_list = []

        for k in range(self.K):
            s = self.tau[k]
            seg_len = self.segment_lengths[k]

            shift = self.rng.standard_normal(d) * 0.3
            weights = np.exp(self._X @ shift)
            weights /= weights.sum()

            row_idx = self.rng.choice(n_rows, size=seg_len * 5,
                                      replace=True, p=weights)

            X_seg = self._X[row_idx]
            y_seg = self._dose[row_idx]
            y_seg = (y_seg - y_seg.mean()) / max(y_seg.std(), 1e-8)

            lam = 1.0
            theta_k = np.linalg.solve(X_seg.T @ X_seg + lam * np.eye(d),
                                      X_seg.T @ y_seg)

            theta_norm = np.linalg.norm(theta_k)
            if theta_norm > 1e-8:
                theta_k = theta_k / theta_norm * 1.5

            self.theta[s:s + seg_len] = theta_k[np.newaxis, :]

            if self.r == 1:
                B_k = (theta_k / max(np.linalg.norm(theta_k), 1e-8)).reshape(d, 1)
            else:
                W = np.diag(np.abs(y_seg[:min(500, len(y_seg))]) + 0.01)
                X_sub = X_seg[:min(500, len(X_seg))]
                _, _, Vt = np.linalg.svd(W @ X_sub, full_matrices=False)
                B_k = Vt[:self.r].T
                Q, _ = np.linalg.qr(
                    np.column_stack([theta_k.reshape(-1, 1), B_k]))
                B_k = Q[:, :self.r]
            self.B_list.append(B_k)

        self.S = float(np.max(np.linalg.norm(self.theta, axis=1)))

    # ------------------------------------------------------------------
    # Bandit interface
    # ------------------------------------------------------------------
    def segment_projector(self, k: int) -> np.ndarray:
        B = self.B_list[k]
        return B @ B.T

    def get_action_set(self, t: int, rng=None):
        _rng = rng if rng is not None else self.rng
        n = self.n_actions
        idx = _rng.choice(len(self._X), size=n, replace=False)
        actions = self._X[idx].copy()
        norms = np.linalg.norm(actions, axis=1, keepdims=True)
        actions = actions / np.maximum(norms, 1e-8)
        return actions

    def step(self, action: np.ndarray, t: int) -> float:
        eps = self.rng.normal(0.0, self.sigma_eps)
        eps = np.clip(eps, -self.L_eps, self.L_eps)
        return float(action @ self.theta[t]) + eps

    def optimal_reward(self, action_set: np.ndarray, t: int) -> float:
        return float(np.max(action_set @ self.theta[t]))
