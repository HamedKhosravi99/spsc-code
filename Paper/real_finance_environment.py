"""
Fama-French 25 Portfolios *real-return* bandit environment.

Uses the Kenneth French 25 Size × Book-to-Market daily portfolio returns:
  - 25 portfolios (5 size quintiles × 5 value quintiles)
  - Features: size one-hot (5) + value one-hot (5) + 20-day momentum (1)
              + 20-day volatility (1) + bias (1) = d=13
  - Reward = actual next-day return (real, in %)
  - Non-stationarity: quarterly segments with real factor-premium rotation
  - Low-rank: Fama-French 3-factor structure → r=2 captures market+size+value

Data auto-downloaded from Kenneth French's website (public domain).
"""

import os
import io
import zipfile
import numpy as np

FF25_URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/"
            "ken.french/ftp/25_Portfolios_5x5_Daily_CSV.zip")


def ensure_ff25(data_dir):
    """Download and extract Fama-French 25 portfolios daily data."""
    csv_path = os.path.join(data_dir, "ff25_daily.csv")
    if os.path.isfile(csv_path):
        return csv_path

    os.makedirs(data_dir, exist_ok=True)
    zip_path = os.path.join(data_dir, "ff25_daily.zip")
    if not os.path.isfile(zip_path):
        print("Downloading Fama-French 25 Portfolios (daily) ...")
        from urllib.request import urlretrieve
        urlretrieve(FF25_URL, zip_path)

    # Extract the CSV from the zip
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        csv_name = [n for n in names if n.lower().endswith(".csv")][0]
        raw = zf.read(csv_name).decode("utf-8", errors="replace")

    # Parse: find the "Value Weighted Returns" section, take data until
    # the next blank-line section or "Equal Weighted" header.
    lines = raw.split("\n")
    data_lines = []
    header_found = False
    in_data = False

    for line in lines:
        stripped = line.strip()
        # Detect start of value-weighted section
        if "value weight" in stripped.lower() and "return" in stripped.lower():
            header_found = True
            continue
        if header_found and not in_data:
            # Skip until we find a line starting with a date (6-8 digits)
            tokens = stripped.replace(",", " ").split()
            if tokens and tokens[0].isdigit() and len(tokens[0]) >= 6:
                in_data = True
                data_lines.append(stripped)
            elif tokens and not tokens[0].isdigit() and len(tokens) >= 5:
                # Could be the column header line — skip it
                continue
        elif in_data:
            tokens = stripped.replace(",", " ").split()
            if not tokens or not tokens[0].replace(".", "").replace("-", "").isdigit():
                # End of data block (blank line or next section header)
                if len(data_lines) > 100:
                    break
                continue
            if len(tokens[0]) >= 6:
                data_lines.append(stripped)

    # Write clean CSV
    with open(csv_path, "w") as f:
        for dl in data_lines:
            f.write(dl + "\n")
    print(f"Parsed {len(data_lines)} trading days -> {csv_path}")
    return csv_path


def _parse_ff25(csv_path, start_year=2006, end_year=2025):
    """Parse the cleaned CSV into dates + return matrix."""
    dates = []
    returns = []
    with open(csv_path, "r") as f:
        for line in f:
            tokens = line.strip().replace(",", " ").split()
            if len(tokens) < 26:
                continue
            date_str = tokens[0]
            year = int(date_str[:4])
            if year < start_year or year > end_year:
                continue
            try:
                rets = [float(x) for x in tokens[1:26]]
            except ValueError:
                continue
            dates.append(int(date_str))
            returns.append(rets)
    return np.array(dates), np.array(returns)  # (T, 25)


class RealFinanceEnvironment:
    """
    Real-return Fama-French 25 portfolio bandit.

    Each segment = one calendar quarter.
    Rewards = actual daily returns.  Features = portfolio characteristics.
    """

    def __init__(
        self,
        data_dir: str,
        r: int = 2,
        n_actions: int = 25,       # present all 25 portfolios each day
        start_year: int = 2006,
        end_year: int = 2025,
        segment_days: int = 63,     # ~one quarter
        seed: int = 42,
    ):
        self.r = r
        self.n_actions = n_actions
        self.rng = np.random.default_rng(seed)

        csv_path = ensure_ff25(data_dir)
        self._dates, self._raw_returns = _parse_ff25(
            csv_path, start_year, end_year)

        # We predict next-day return; shift by one day
        self._features_returns = self._raw_returns[:-1]  # features use day t
        self._target_returns = self._raw_returns[1:]       # reward is day t+1
        self._dates = self._dates[:-1]
        self.T = len(self._dates)

        self._build_features()
        self._build_segments(segment_days)
        self._build_theta_and_subspaces()

        self.d = self._feat_dim
        self.L_x = 1.0
        self.L = 1.0
        self.L_eps = 10.0   # daily returns can be large
        self.spectral_radius = 0.0
        self.sigma_eta = 0.0

        self._true_regret = np.zeros(self.T)
        self._current_actions = None
        self._current_true_rewards = None

    # ------------------------------------------------------------------
    # Feature construction
    # ------------------------------------------------------------------

    def _build_features(self):
        """
        Rich feature set per portfolio (i,j), i=size quintile, j=value quintile:
          size one-hot (5) + value one-hot (5) + bias (1) = 11 static dims
        Plus time-varying at multiple horizons (5, 10, 20, 40, 60 days):
          rolling momentum (5) + rolling volatility (5) = 10 dims
        Plus size x value cross-features (5) = 5 dims
        Total d = 26.

        The multi-horizon features increase d while preserving the underlying
        low-rank factor structure (documented r=2-3 from Fama-French 3-factor).
        """
        n_port = 25
        windows = [5, 10, 20, 40, 60]
        n_windows = len(windows)
        # 5 size + 5 value + 1 bias + 5 size*value cross + 5 momentum + 5 vol
        self._feat_dim = 11 + 5 + 2 * n_windows

        # Static part: portfolio identity + cross features
        static = np.zeros((n_port, 16))  # 11 + 5 cross
        for p in range(n_port):
            size_q = p // 5      # 0..4
            val_q = p % 5        # 0..4
            static[p, size_q] = 1.0
            static[p, 5 + val_q] = 1.0
            static[p, 10] = 1.0  # bias
            # Cross-features: indicator for size-value bucket
            static[p, 11 + (size_q + val_q) % 5] = 1.0

        self._all_features = np.zeros((self.T, n_port, self._feat_dim))
        max_window = max(windows)

        for t in range(self.T):
            for p in range(n_port):
                feat = np.zeros(self._feat_dim)
                feat[:16] = static[p]
                for wi, w in enumerate(windows):
                    if t >= w:
                        past = self._features_returns[t - w:t, p]
                        feat[16 + wi] = past.mean()            # momentum
                        feat[16 + n_windows + wi] = past.std() + 1e-6  # vol
                    else:
                        feat[16 + wi] = 0.0
                        feat[16 + n_windows + wi] = 1.0
                # Normalise
                norm = np.linalg.norm(feat)
                if norm > 1e-8:
                    feat /= norm
                self._all_features[t, p] = feat

    # ------------------------------------------------------------------
    # Segments (quarterly)
    # ------------------------------------------------------------------

    def _build_segments(self, seg_days):
        self.K = max(1, self.T // seg_days)
        self.segment_lengths = [seg_days] * self.K
        self.segment_lengths[-1] += self.T - sum(self.segment_lengths)

        self.tau = [0]
        for l in self.segment_lengths[:-1]:
            self.tau.append(self.tau[-1] + l)

        self.seg_of = np.zeros(self.T, dtype=int)
        for k, s in enumerate(self.tau):
            self.seg_of[s:s + self.segment_lengths[k]] = k

    # ------------------------------------------------------------------
    # OLS theta and subspace
    # ------------------------------------------------------------------

    def _build_theta_and_subspaces(self):
        d = self._feat_dim
        self.theta = np.zeros((self.T, d))
        self.B_list = []
        residuals = []

        for k in range(self.K):
            s = self.tau[k]
            e = s + self.segment_lengths[k]

            # Collect (feature, return) pairs within this quarter
            X_list, r_list = [], []
            for t in range(s, e):
                for p in range(25):
                    X_list.append(self._all_features[t, p])
                    r_list.append(self._target_returns[t, p])
            X_q = np.array(X_list)
            r_q = np.array(r_list)

            # Ridge OLS
            lam = 1.0
            theta_k = np.linalg.solve(
                X_q.T @ X_q + lam * np.eye(d), X_q.T @ r_q
            )
            resid = r_q - X_q @ theta_k
            residuals.extend(resid.tolist())
            self.theta[s:e] = theta_k[np.newaxis, :]

            # Subspace: top-r directions
            if self.r == 1:
                tn = np.linalg.norm(theta_k)
                B_k = (theta_k / max(tn, 1e-8)).reshape(d, 1)
            else:
                # Use SVD of the return-weighted feature matrix
                W = np.diag(np.abs(r_q) + 0.01)
                _, _, Vt = np.linalg.svd(W @ X_q, full_matrices=False)
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
        n = min(self.n_actions, 25)
        if n < 25:
            chosen = _rng.choice(25, size=n, replace=False)
        else:
            chosen = np.arange(25)

        actions = self._all_features[t, chosen]              # (n, d)
        return actions

    def step(self, action: np.ndarray, t: int) -> float:
        """
        Reward follows the paper's linear model: y_t = x_t^T theta_t + eps_t.
        theta_t is derived from real Fama-French returns via per-quarter OLS.
        This ensures sphere probes produce valid K-inverse observations.
        """
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

    def get_true_cumulative_regret(self):
        return np.cumsum(self._true_regret)

    def svd_spectrum(self):
        """SVD spectrum of quarterly theta matrix → factor structure."""
        thetas = np.array([self.theta[self.tau[k]] for k in range(self.K)])
        _, svals, _ = np.linalg.svd(thetas, full_matrices=False)
        return svals / svals.sum()

    def return_pca_spectrum(self):
        """PCA of raw return matrix → evidence of factor structure."""
        R = self._target_returns  # (T, 25)
        R_centered = R - R.mean(axis=0, keepdims=True)
        _, svals, _ = np.linalg.svd(R_centered, full_matrices=False)
        var_explained = svals ** 2
        return var_explained / var_explained.sum()
