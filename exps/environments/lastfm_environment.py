"""
Last.fm *fully real* bandit environment.

Uses Last.fm HetRec 2011 (Cantador et al.) — rewards are ACTUAL listening counts.

  - 1,892 users, 17,632 artists, 92,800 listening records
  - Features built from artist tags (bag-of-tags) + SVD of listening matrix
  - Tag features are naturally high-dimensional with many noise dimensions
    → ideal for low-rank subspace methods
  - Rewards = log(1 + listening_count), centered

Non-stationarity: users sorted by KMeans clusters on latent listening factors.
"""

import os, zipfile, numpy as np

try:
    import urllib.request
except ImportError:
    pass

from sklearn.preprocessing import StandardScaler


_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".lastfm_cache")
_LASTFM_URL = "https://files.grouplens.org/datasets/hetrec2011/hetrec2011-lastfm-2k.zip"


def _load_lastfm():
    """Download and parse Last.fm HetRec 2011. Returns (user_artists, artist_tags)."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    ua_cache = os.path.join(_CACHE_DIR, "user_artists.npy")
    at_cache = os.path.join(_CACHE_DIR, "artist_tag_matrix.npz")

    if os.path.exists(ua_cache) and os.path.exists(at_cache):
        ua_arr = np.load(ua_cache)
        at_data = np.load(at_cache)
        return ua_arr, at_data["tag_matrix"], at_data["artist_ids"]

    zip_path = os.path.join(_CACHE_DIR, "hetrec2011-lastfm-2k.zip")
    if not os.path.exists(zip_path):
        print("Downloading Last.fm HetRec 2011...", flush=True)
        try:
            urllib.request.urlretrieve(_LASTFM_URL, zip_path)
        except Exception as e:
            raise RuntimeError(
                f"Failed to download Last.fm data from {_LASTFM_URL}\n"
                f"Error: {e}\n"
                f"You can manually download from https://grouplens.org/datasets/hetrec-2011/ "
                f"and place the zip in {_CACHE_DIR}/"
            )
        print("  Done downloading.", flush=True)

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        # Find files (might be in a subdirectory)
        ua_name = [n for n in names if n.endswith("user_artists.dat")][0]
        ut_name = [n for n in names if n.endswith("user_taggedartists.dat")][0]

        ua_text = zf.read(ua_name).decode("utf-8")
        ut_text = zf.read(ut_name).decode("utf-8")

    # Parse user_artists.dat: userID, artistID, weight
    ua_records = []
    for line in ua_text.strip().split("\n")[1:]:
        parts = line.strip().split("\t")
        if len(parts) >= 3:
            ua_records.append((int(parts[0]), int(parts[1]), float(parts[2])))
    ua_arr = np.array(ua_records)  # N x 3

    # Parse user_taggedartists.dat: userID, artistID, tagID, ...
    artist_tag_counts = {}
    all_tags = set()
    for line in ut_text.strip().split("\n")[1:]:
        parts = line.strip().split("\t")
        if len(parts) >= 3:
            aid, tid = int(parts[1]), int(parts[2])
            all_tags.add(tid)
            if aid not in artist_tag_counts:
                artist_tag_counts[aid] = {}
            artist_tag_counts[aid][tid] = artist_tag_counts[aid].get(tid, 0) + 1

    # Select top tags by total frequency
    tag_freq = {}
    for aid, tags in artist_tag_counts.items():
        for tid, cnt in tags.items():
            tag_freq[tid] = tag_freq.get(tid, 0) + cnt
    n_tag_features = min(200, len(tag_freq))
    top_tags = sorted(tag_freq.keys(), key=lambda t: -tag_freq[t])[:n_tag_features]
    tag_to_idx = {t: i for i, t in enumerate(top_tags)}

    # Build tag feature matrix for all artists that appear in listening data
    all_aids = sorted(set(int(r[1]) for r in ua_records))
    aid_to_row = {a: i for i, a in enumerate(all_aids)}
    n_artists = len(all_aids)

    tag_matrix = np.zeros((n_artists, n_tag_features), dtype=np.float32)
    for aid in all_aids:
        if aid in artist_tag_counts:
            for tid, cnt in artist_tag_counts[aid].items():
                if tid in tag_to_idx:
                    tag_matrix[aid_to_row[aid], tag_to_idx[tid]] = cnt

    artist_ids = np.array(all_aids)

    # Cache
    np.save(ua_cache, ua_arr)
    np.savez(at_cache, tag_matrix=tag_matrix, artist_ids=artist_ids)
    print(f"  Last.fm: {len(set(ua_arr[:,0].astype(int)))} users, "
          f"{n_artists} artists, {len(ua_records)} records, "
          f"{n_tag_features} tag features.", flush=True)

    return ua_arr, tag_matrix, artist_ids


class RealLastfmEnvironment:
    """
    Fully real Last.fm bandit — rewards are actual listening counts (log-transformed).

    At each round t:
      - A user from the current segment's cluster is selected
      - Action set = artists that user actually listened to
      - step() returns log(1 + listening_count), centered
      - optimal_reward() returns max reward in the action set
    """

    def __init__(
        self,
        d: int = 105,
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
        ua_arr, tag_matrix, artist_ids = _load_lastfm()

        n_artists = len(artist_ids)
        aid_to_row = {int(a): i for i, a in enumerate(artist_ids)}

        # Build per-user listening dicts (artist_row_idx -> log_weight)
        self._user_ratings = {}
        all_weights = []
        for row in ua_arr:
            uid, aid, weight = int(row[0]), int(row[1]), float(row[2])
            if aid not in aid_to_row:
                continue
            log_w = float(np.log1p(weight))
            all_weights.append(log_w)
            if uid not in self._user_ratings:
                self._user_ratings[uid] = {}
            self._user_ratings[uid][aid_to_row[aid]] = log_w

        self._global_mean = float(np.mean(all_weights))

        # Filter users with enough listens
        min_ratings = self.n_actions + 5
        self._valid_users = sorted(
            [u for u, r in self._user_ratings.items() if len(r) >= min_ratings]
        )
        assert len(self._valid_users) >= 50, (
            f"Only {len(self._valid_users)} users with {min_ratings}+ artists. "
            f"Try reducing n_actions."
        )

        # Build artist feature vectors
        # Part 1: tag features (naturally high-d, many noise dimensions)
        scaler_t = StandardScaler()
        tag_std = scaler_t.fit_transform(tag_matrix.astype(np.float64))

        # Part 2: SVD of user-artist listening matrix (collaborative features)
        uid_list = sorted(self._user_ratings.keys())
        uid_to_idx = {u: i for i, u in enumerate(uid_list)}
        R_mat = np.zeros((len(uid_list), n_artists))
        for uid in uid_list:
            for aidx, log_w in self._user_ratings[uid].items():
                R_mat[uid_to_idx[uid], aidx] = log_w

        U, S, Vt = np.linalg.svd(R_mat, full_matrices=False)
        n_svd = min(50, n_artists)
        svd_features = Vt[:n_svd].T * S[:n_svd]
        user_latent = U[:, :min(10, n_svd)] * S[:min(10, n_svd)]

        scaler_s = StandardScaler()
        svd_std = scaler_s.fit_transform(svd_features)

        # Combine: [tag_features | svd_features]
        n_tag = tag_std.shape[1]
        X_base = np.hstack([tag_std, svd_std])
        d_base = X_base.shape[1]

        if target_d <= d_base:
            X_full = X_base[:, :target_d]
        else:
            interactions = []
            for i in range(min(n_tag, 50)):
                for j in range(i + 1, min(n_tag, 50)):
                    interactions.append(tag_std[:, i] * tag_std[:, j])
                    if len(interactions) + d_base >= target_d:
                        break
                if len(interactions) + d_base >= target_d:
                    break
            if interactions:
                X_inter = np.column_stack(interactions)
                X_full = np.hstack([X_base, X_inter])[:, :target_d]
            else:
                X_full = X_base[:, :target_d]

        norms = np.linalg.norm(X_full, axis=1, keepdims=True)
        X_full /= np.maximum(norms, 1e-8)
        self._artist_features = X_full
        self.d = X_full.shape[1]

        # Cluster valid users for non-stationarity
        from sklearn.cluster import KMeans
        valid_latent = user_latent[[uid_to_idx[u] for u in self._valid_users]]
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
                for aidx, log_w in self._user_ratings[uid].items():
                    X_list.append(self._artist_features[aidx])
                    y_list.append(log_w - self._global_mean)

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
        listened = list(self._user_ratings[uid].keys())

        n = min(self.n_actions, len(listened))
        chosen = _rng.choice(listened, size=n, replace=False)

        features = self._artist_features[chosen]
        real_rewards = np.array(
            [self._user_ratings[uid][aidx] - self._global_mean for aidx in chosen]
        )
        self._current_features = features
        self._current_ratings = real_rewards

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
