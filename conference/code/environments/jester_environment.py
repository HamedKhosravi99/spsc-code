"""
Jester *fully real* bandit environment.

Uses Jester Dataset 1 (Goldberg et al.) — rewards are ACTUAL joke ratings (-10 to +10).

Setup:
  - Each round t corresponds to a real user from a specific cluster (segment).
  - Action set = feature vectors of jokes that user actually rated.
  - step() returns the user's actual rating (centered), not x^T theta + noise.
  - optimal_reward() returns the max actual rating in the action set.
  - theta/subspaces computed via OLS for oracle methods and regret normalization.

Non-stationarity: users sorted by KMeans clusters on latent preference factors.
"""

import os, zipfile, numpy as np

try:
    import urllib.request
except ImportError:
    pass

from sklearn.preprocessing import StandardScaler


_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".jester_cache")
_JESTER_URL = "https://eigentaste.berkeley.edu/dataset/jester_dataset_1_1.zip"


def _load_jester():
    """Download and parse Jester Dataset 1-1. Returns (n_users x 100) rating matrix, NaN=unrated."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    npy_cache = os.path.join(_CACHE_DIR, "jester_ratings.npy")

    if os.path.exists(npy_cache):
        return np.load(npy_cache)

    zip_path = os.path.join(_CACHE_DIR, "jester_dataset_1_1.zip")
    if not os.path.exists(zip_path):
        print("Downloading Jester Dataset 1-1...", flush=True)
        try:
            urllib.request.urlretrieve(_JESTER_URL, zip_path)
        except Exception as e:
            raise RuntimeError(
                f"Failed to download Jester data from {_JESTER_URL}\n"
                f"Error: {e}\n"
                f"You can manually download from https://eigentaste.berkeley.edu/dataset/ "
                f"and place the zip in {_CACHE_DIR}/"
            )
        print("  Done downloading.", flush=True)

    # Extract data file from zip
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if not names:
            raise RuntimeError(f"No files found in {zip_path}")
        data_name = names[0]
        raw = zf.read(data_name)

    # Try text parse first (some old .xls files are really tab/semicolon-delimited text)
    data = None
    try:
        from io import StringIO
        text = raw.decode("utf-8")
        for sep in [";", "\t", ","]:
            try:
                arr = np.genfromtxt(StringIO(text), delimiter=sep)
                if arr.ndim == 2 and arr.shape[1] >= 100:
                    data = arr
                    break
            except Exception:
                continue
    except Exception:
        pass

    if data is None:
        # Binary Excel — try xlrd directly (fastest), then pandas
        tmp = os.path.join(_CACHE_DIR, "temp_jester.xls")
        with open(tmp, "wb") as f:
            f.write(raw)
        try:
            import xlrd
            wb = xlrd.open_workbook(tmp)
            sheet = wb.sheet_by_index(0)
            data = np.array(
                [sheet.row_values(i) for i in range(sheet.nrows)]
            )
        except ImportError:
            try:
                import pandas as pd
                df = pd.read_excel(tmp, header=None)
                data = df.values.astype(float)
            except Exception as e:
                raise RuntimeError(
                    f"Cannot read Jester .xls file. Error: {e}\n"
                    "Fix: pip install xlrd"
                )

    # Column 0 = count of rated jokes, columns 1-100 = ratings (99 = unrated)
    if data.shape[1] == 101:
        ratings = data[:, 1:].copy()
    else:
        ratings = data.copy()

    ratings[ratings == 99] = np.nan

    np.save(npy_cache, ratings)
    print(f"  Jester: loaded {ratings.shape[0]} users x {ratings.shape[1]} jokes.", flush=True)
    return ratings


class RealJesterEnvironment:
    """
    Fully real Jester bandit — rewards are actual joke ratings.

    At each round t:
      - A user from the current segment's cluster is selected
      - Action set = jokes that user actually rated (so reward is known)
      - step() returns centered actual rating
      - optimal_reward() returns max actual rating in action set
    """

    def __init__(
        self,
        d: int = 55,
        r: int = 10,
        n_actions: int = 40,
        segment_size: int = 500,
        n_segments: int = 10,
        seed: int = 42,
    ):
        self.r = r
        self.n_actions = n_actions
        self.rng = np.random.default_rng(seed)

        self._load_and_prepare_data(d)
        self._build_segments(segment_size, n_segments)
        self._assign_rounds()
        self._build_theta_and_subspaces()

        self.L_x = 1.0
        self.L = 1.0
        self.L_eps = 10.0
        self.spectral_radius = 0.0
        self.sigma_eta = 0.0

        self._current_ratings = None

    def _load_and_prepare_data(self, target_d):
        ratings = _load_jester()  # n_users x n_jokes, NaN = unrated
        n_users, n_jokes = ratings.shape

        self._global_mean = float(np.nanmean(ratings))

        # Build per-user rating dicts
        self._user_ratings = {}
        for uid in range(n_users):
            rated = {}
            for jid in range(n_jokes):
                if not np.isnan(ratings[uid, jid]):
                    rated[jid] = float(ratings[uid, jid])
            if rated:
                self._user_ratings[uid] = rated

        # Filter users with enough ratings
        min_ratings = self.n_actions + 5
        self._valid_users = sorted(
            [u for u, r in self._user_ratings.items() if len(r) >= min_ratings]
        )
        assert len(self._valid_users) >= 50, (
            f"Only {len(self._valid_users)} users with {min_ratings}+ ratings"
        )

        # Build joke feature vectors via SVD of rating matrix
        joke_means = np.nanmean(ratings, axis=0)
        R_imputed = ratings.copy()
        for j in range(n_jokes):
            mask = np.isnan(R_imputed[:, j])
            R_imputed[mask, j] = joke_means[j]
        R_imputed -= R_imputed.mean(axis=0, keepdims=True)

        U, S, Vt = np.linalg.svd(R_imputed, full_matrices=False)
        n_latent = min(50, n_jokes)
        joke_latent = Vt[:n_latent].T * S[:n_latent]          # n_jokes x n_latent
        user_latent = U[:, :min(10, n_latent)] * S[:min(10, n_latent)]

        scaler_l = StandardScaler()
        latent_std = scaler_l.fit_transform(joke_latent)

        if target_d <= n_latent:
            X_full = latent_std[:, :target_d]
        else:
            # Add pairwise interactions to reach target_d
            interactions = []
            for i in range(n_latent):
                for j in range(i + 1, n_latent):
                    interactions.append(latent_std[:, i] * latent_std[:, j])
                    if len(interactions) + n_latent >= target_d:
                        break
                if len(interactions) + n_latent >= target_d:
                    break
            if interactions:
                X_inter = np.column_stack(interactions)
                X_full = np.hstack([latent_std, X_inter])[:, :target_d]
            else:
                X_full = latent_std[:, :target_d]

        norms = np.linalg.norm(X_full, axis=1, keepdims=True)
        X_full /= np.maximum(norms, 1e-8)
        self._joke_features = X_full
        self.d = X_full.shape[1]

        # Cluster valid users for non-stationarity
        from sklearn.cluster import KMeans
        valid_latent = user_latent[self._valid_users]
        n_clusters = min(20, len(self._valid_users))
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
        labels = km.fit_predict(valid_latent)

        self._user_cluster = {}
        for i, uid in enumerate(self._valid_users):
            self._user_cluster[uid] = labels[i]
        self._n_clusters = n_clusters

        self._valid_users.sort(key=lambda u: self._user_cluster[u])

    def _build_segments(self, segment_size, n_segments):
        self.K = n_segments
        self.T = segment_size * n_segments
        self.segment_lengths = [segment_size] * self.K
        self.segment_lengths[-1] += self.T - sum(self.segment_lengths)

        self.tau = [0]
        for l in self.segment_lengths[:-1]:
            self.tau.append(self.tau[-1] + l)

        self.seg_of = np.zeros(self.T, dtype=int)
        for k, start in enumerate(self.tau):
            self.seg_of[start : start + self.segment_lengths[k]] = k

    def _assign_rounds(self):
        n_per_seg = max(1, len(self._valid_users) // self.K)
        seg_users = []
        for k in range(self.K):
            start_u = k * n_per_seg
            end_u = (k + 1) * n_per_seg if k < self.K - 1 else len(self._valid_users)
            seg_users.append(self._valid_users[start_u:end_u])
            if not seg_users[-1]:
                seg_users[-1] = self._valid_users[:n_per_seg]

        self._round_user = np.zeros(self.T, dtype=int)
        for k in range(self.K):
            s = self.tau[k]
            e = s + self.segment_lengths[k]
            users_k = seg_users[k]
            for t in range(s, e):
                self._round_user[t] = users_k[t % len(users_k)]

    def _build_theta_and_subspaces(self):
        d = self.d
        self.theta = np.zeros((self.T, d))
        self.B_list = []
        residuals = []

        for k in range(self.K):
            s = self.tau[k]
            e = s + self.segment_lengths[k]

            X_list, y_list = [], []
            for t in range(s, e):
                uid = self._round_user[t]
                for jid, rating in self._user_ratings[uid].items():
                    X_list.append(self._joke_features[jid])
                    y_list.append(rating - self._global_mean)

            X_k = np.array(X_list)
            y_k = np.array(y_list)

            if len(y_k) > 5000:
                idx = self.rng.choice(len(y_k), 5000, replace=False)
                X_k, y_k = X_k[idx], y_k[idx]

            lam = 1.0
            theta_k = np.linalg.solve(X_k.T @ X_k + lam * np.eye(d), X_k.T @ y_k)
            resid = y_k - X_k @ theta_k
            residuals.extend(resid[:500].tolist())
            self.theta[s:e] = theta_k[np.newaxis, :]

            n_sub = min(len(y_k), 500)
            W = np.diag(np.abs(y_k[:n_sub]) + 0.1)
            X_sub = X_k[:n_sub]
            _, _, Vt = np.linalg.svd(W @ X_sub, full_matrices=False)
            B_k = Vt[: self.r].T
            Q, _ = np.linalg.qr(
                np.column_stack([theta_k.reshape(-1, 1), B_k])
            )
            B_k = Q[:, : self.r]
            self.B_list.append(B_k)

        self.sigma_eps = float(np.std(residuals))
        self.S = float(np.max(np.linalg.norm(self.theta, axis=1)))

    # ------------------------------------------------------------------
    # Per-round interface — REAL rewards
    # ------------------------------------------------------------------

    def get_action_set(self, t: int, rng=None):
        _rng = rng if rng is not None else self.rng
        uid = self._round_user[t]
        rated_jokes = list(self._user_ratings[uid].keys())

        n = min(self.n_actions, len(rated_jokes))
        chosen = _rng.choice(rated_jokes, size=n, replace=False)

        features = self._joke_features[chosen]
        real_ratings = np.array(
            [self._user_ratings[uid][jid] - self._global_mean for jid in chosen]
        )
        self._current_features = features
        self._current_ratings = real_ratings

        return features

    def step(self, action: np.ndarray, t: int) -> float:
        dists = np.linalg.norm(
            self._current_features - action[np.newaxis, :], axis=1
        )
        idx = int(np.argmin(dists))
        return float(self._current_ratings[idx])

    def optimal_reward(self, action_set: np.ndarray, t: int) -> float:
        return float(np.max(self._current_ratings))

    def segment_projector(self, k: int) -> np.ndarray:
        B = self.B_list[k]
        return B @ B.T

    def svd_spectrum(self):
        thetas = np.array([self.theta[self.tau[k]] for k in range(self.K)])
        _, svals, _ = np.linalg.svd(thetas, full_matrices=False)
        return svals / svals.sum()
