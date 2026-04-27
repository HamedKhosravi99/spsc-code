"""
Vancomycin Clinical Dosing — Real-Data Bandit Environment.

REAL DATA ONLY.  No synthetic fallback.  The constructor REQUIRES
`data_path` to point at a real cohort CSV (e.g., extracted from
MIMIC-IV via PhysioNet credentialed access).

Format expected at `data_path`:
  Comma-separated, with a header row.  One row per patient (or per
  vancomycin order).  Required columns (case-insensitive):

    age            years            (numeric, 18-95 typical)
    weight_kg      kg               (numeric)
    height_cm      cm               (numeric)
    female         0/1              (1 if female)
    scr            mg/dL            (serum creatinine)
    bmi            kg/m^2           (numeric; computed from height+weight if missing is OK)
    diabetes       0/1
    icu            0/1              (admitted to ICU)
    sepsis         0/1
    dialysis       0/1
    albumin        g/dL
    wbc            10^9/L
    fever          0/1              (temp > 38C)
    prior_abx      0/1              (prior antibiotic exposure)
    mrsa           0/1              (MRSA culture-positive)
    vasopressor    0/1
    ventilation    0/1
    liver_disease  0/1
    dose_mg_per_day  mg             (administered or AUC-targeted daily dose; reward signal)

Suggested extraction source: MIMIC-IV (PhysioNet) — query patients with
vancomycin orders in `prescriptions`/`emar`, joined to `chartevents`
(creatinine, albumin, WBC, temperature), `labevents`, `icustays`, and
diagnosis tables (sepsis = ICD codes A40-A41, R65.20-R65.21).

Reference dosing protocol: M. J. Rybak et al., 2020 ASHP/IDSA consensus.
"""

import csv
import os
import numpy as np


REQUIRED_COLS = [
    "age", "weight_kg", "height_cm", "female", "scr", "bmi",
    "diabetes", "icu", "sepsis", "dialysis", "albumin", "wbc",
    "fever", "prior_abx", "mrsa", "vasopressor", "ventilation",
    "liver_disease", "dose_mg_per_day",
]


class VancomycinEnvironment:
    """
    Real-data Vancomycin dosing bandit.

    Parameters
    ----------
    data_path : path to vancomycin cohort CSV.  REQUIRED.
    d         : feature dimension (after expansion / projection)
    r         : latent rank for subspace
    K         : number of segments (subpopulation shifts)
    T         : horizon
    n_actions : candidate doses per round
    seed      : RNG seed
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
    ):
        if data_path is None or not os.path.isfile(data_path):
            raise FileNotFoundError(
                "VancomycinEnvironment requires a real cohort CSV "
                "(e.g., MIMIC-IV-extracted). "
                f"Got data_path={data_path!r}.  Required columns: "
                f"{REQUIRED_COLS}"
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

        self._load_real_data(data_path, d)
        self.d = self._X.shape[1]
        self._build_segments()
        self._build_theta_and_subspaces()
        self._current_actions = None

    # ------------------------------------------------------------------
    # Loader
    # ------------------------------------------------------------------
    def _load_real_data(self, data_path, d):
        rows = []
        with open(data_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            header = {h.lower(): h for h in (reader.fieldnames or [])}
            missing = [c for c in REQUIRED_COLS if c.lower() not in header]
            if missing:
                raise ValueError(
                    f"Vancomycin CSV at {data_path} is missing columns: {missing}. "
                    f"Required columns (case-insensitive): {REQUIRED_COLS}"
                )
            for row in reader:
                norm = {c: row[header[c.lower()]] for c in REQUIRED_COLS}
                rows.append(norm)

        if len(rows) == 0:
            raise ValueError(f"Vancomycin CSV at {data_path} parsed zero rows.")

        def to_float(s, default=0.0):
            try:
                return float(s)
            except (TypeError, ValueError):
                return default

        n = len(rows)
        age = np.array([to_float(r["age"]) for r in rows])
        weight_kg = np.array([to_float(r["weight_kg"]) for r in rows])
        height_cm = np.array([to_float(r["height_cm"]) for r in rows])
        female = np.array([to_float(r["female"]) for r in rows])
        scr = np.array([to_float(r["scr"]) for r in rows])
        bmi_raw = np.array([to_float(r["bmi"]) for r in rows])
        bmi = np.where(bmi_raw > 0, bmi_raw,
                       weight_kg / np.maximum(height_cm / 100.0, 1e-6) ** 2)
        diabetes = np.array([to_float(r["diabetes"]) for r in rows])
        icu = np.array([to_float(r["icu"]) for r in rows])
        sepsis = np.array([to_float(r["sepsis"]) for r in rows])
        dialysis = np.array([to_float(r["dialysis"]) for r in rows])
        albumin = np.array([to_float(r["albumin"]) for r in rows])
        wbc = np.array([to_float(r["wbc"]) for r in rows])
        fever = np.array([to_float(r["fever"]) for r in rows])
        prior_abx = np.array([to_float(r["prior_abx"]) for r in rows])
        mrsa = np.array([to_float(r["mrsa"]) for r in rows])
        vasopressor = np.array([to_float(r["vasopressor"]) for r in rows])
        ventilation = np.array([to_float(r["ventilation"]) for r in rows])
        liver_disease = np.array([to_float(r["liver_disease"]) for r in rows])
        dose = np.array([to_float(r["dose_mg_per_day"]) for r in rows])

        elderly = (age > 65).astype(float)
        obese = (bmi > 30).astype(float)

        core_features = np.column_stack([
            age / 100.0,
            weight_kg / 180.0,
            height_cm / 200.0,
            female,
            scr / 6.0,
            bmi / 50.0,
            diabetes, icu, sepsis, dialysis,
            albumin / 5.0,
            wbc / 35.0,
            fever, prior_abx, mrsa, vasopressor, ventilation, liver_disease,
            elderly, obese,
            np.ones(n),  # bias
        ])  # 21 features

        rng = np.random.default_rng(0)
        n_core = core_features.shape[1]
        expanded = [core_features]

        pairs = []
        for i in range(min(n_core, 12)):
            for j in range(i + 1, min(n_core, 12)):
                pairs.append(core_features[:, i] * core_features[:, j])
                if len(expanded[0][0]) + len(pairs) + n_core >= d:
                    break
            if len(expanded[0][0]) + len(pairs) + n_core >= d:
                break

        if pairs:
            expanded.append(np.column_stack(pairs))

        sq = core_features[:, :min(6, n_core)] ** 2
        expanded.append(sq)

        X_so_far = np.hstack(expanded)
        if X_so_far.shape[1] < d:
            n_extra = d - X_so_far.shape[1]
            W_rand = rng.standard_normal((X_so_far.shape[1], n_extra)) * 0.1
            extra = X_so_far @ W_rand
            X_so_far = np.hstack([X_so_far, extra])
        elif X_so_far.shape[1] > d:
            X_so_far = X_so_far[:, :d]

        norms = np.linalg.norm(X_so_far, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-8)
        self._X = X_so_far / norms
        self._dose = dose

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
        n_patients = len(self._X)
        self.theta = np.zeros((self.T, d))
        self.B_list = []

        for k in range(self.K):
            s = self.tau[k]
            seg_len = self.segment_lengths[k]

            shift = self.rng.standard_normal(d) * 0.3
            weights = np.exp(self._X @ shift)
            weights /= weights.sum()

            patient_idx = self.rng.choice(n_patients, size=seg_len * 5,
                                          replace=True, p=weights)

            X_seg = self._X[patient_idx]
            y_seg = self._dose[patient_idx]
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
