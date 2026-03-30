"""
Criteo Attribution Dataset — Preprocessing.

Reproduces the Criteo benchmark environment from Russac et al. (NeurIPS 2019):
  1. Download the public Criteo 30-day live traffic sample
  2. Keep cat1–cat9 and campaign; build binary click label
  3. One-hot encode selected categoricals (sparse)
  4. Apply TruncatedSVD to 50 dimensions
  5. Fit theta_star via linear regression on the 50-dim features
  6. Build clicked / non-clicked context pools (10 000 each)
  7. Save processed arrays to .npz for fast reloads

Output
------
  criteo_processed.npz  containing:
    X_clicked      (10000, 50)   — clicked-banner pool
    X_nonclicked   (10000, 50)   — non-clicked-banner pool
    theta_star     (50,)         — fitted reward parameter
"""

import os
import sys
import gzip
import tarfile
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import Ridge

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "criteo")
RAW_FILE   = os.path.join(DATA_DIR, "criteo_attribution_dataset.tsv.gz")
OUT_FILE   = os.path.join(DATA_DIR, "criteo_processed.npz")
N_SVD      = 50          # target dimensionality
POOL_SIZE  = 10_000      # size of each context pool
MAX_ROWS   = 2_000_000   # max rows to read from raw data (memory safety)

DOWNLOAD_URLS = [
    ("http://go.criteo.net/criteo-research-attribution-dataset.zip", "zip"),
]


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_criteo():
    """Attempt to download the Criteo Attribution dataset."""
    import urllib.request
    import zipfile

    os.makedirs(DATA_DIR, exist_ok=True)

    if os.path.isfile(RAW_FILE):
        print(f"Raw data already exists: {RAW_FILE}")
        return True

    # Check for already-extracted TSV (uncompressed)
    tsv_uncompressed = os.path.join(DATA_DIR, "criteo_attribution_dataset.tsv")
    if os.path.isfile(tsv_uncompressed):
        print(f"Found uncompressed TSV: {tsv_uncompressed}")
        return True

    # Check for existing zip/tar downloads
    for ext in ["zip", "tar.gz"]:
        archive = os.path.join(DATA_DIR, f"criteo_attribution_dataset.{ext}")
        if os.path.isfile(archive):
            print(f"Found archive: {archive}, extracting ...")
            if ext == "zip":
                with zipfile.ZipFile(archive, "r") as zf:
                    zf.extractall(DATA_DIR)
            else:
                with tarfile.open(archive, "r:gz") as tar:
                    tar.extractall(DATA_DIR)
            # Check what was extracted
            for candidate in [RAW_FILE, tsv_uncompressed]:
                if os.path.isfile(candidate):
                    return True
            # List extracted files
            print(f"  Extracted files: {os.listdir(DATA_DIR)}")
            return True

    # Try downloading
    for url, fmt in DOWNLOAD_URLS:
        dest = os.path.join(DATA_DIR, f"criteo_download.{fmt}")
        print(f"Downloading from {url} ...")
        print("  (This is ~2.6 GB, may take several minutes)")
        try:
            urllib.request.urlretrieve(url, dest)
            fsize = os.path.getsize(dest)
            print(f"  Downloaded {fsize / 1e9:.1f} GB")
            if fsize < 1_000_000:
                print("  File too small, likely an error page. Removing.")
                os.remove(dest)
                continue
            # Extract
            print(f"  Extracting ...")
            if fmt == "zip":
                with zipfile.ZipFile(dest, "r") as zf:
                    zf.extractall(DATA_DIR)
            elif fmt == "tar.gz":
                with tarfile.open(dest, "r:gz") as tar:
                    tar.extractall(DATA_DIR)
            print(f"  Extracted files: {os.listdir(DATA_DIR)}")
            return True
        except Exception as e:
            print(f"  Download failed: {e}")
            if os.path.isfile(dest):
                os.remove(dest)

    print("\n" + "=" * 70)
    print("Could not download the Criteo Attribution dataset automatically.")
    print("Please download manually:")
    print("  1. Go to: https://ailab.criteo.com/criteo-attribution-modeling-bidding-dataset/")
    print("  2. Download the dataset")
    print(f"  3. Place it in: {DATA_DIR}/")
    print("=" * 70)
    return False


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def preprocess():
    """
    Load raw Criteo data → one-hot encode → SVD → fit theta_star → save pools.
    """
    if os.path.isfile(OUT_FILE):
        print(f"Processed data already exists: {OUT_FILE}")
        data = np.load(OUT_FILE)
        print(f"  X_clicked:    {data['X_clicked'].shape}")
        print(f"  X_nonclicked: {data['X_nonclicked'].shape}")
        print(f"  theta_star:   {data['theta_star'].shape}")
        return data

    # Find the raw data file (may be .tsv.gz or .tsv)
    tsv_uncompressed = os.path.join(DATA_DIR, "criteo_attribution_dataset.tsv")
    if os.path.isfile(RAW_FILE):
        data_file = RAW_FILE
        compression = "gzip"
    elif os.path.isfile(tsv_uncompressed):
        data_file = tsv_uncompressed
        compression = None
    else:
        # Search DATA_DIR for any TSV file
        tsv_files = [f for f in os.listdir(DATA_DIR)
                     if f.endswith(".tsv") or f.endswith(".tsv.gz")]
        if tsv_files:
            data_file = os.path.join(DATA_DIR, tsv_files[0])
            compression = "gzip" if data_file.endswith(".gz") else None
        else:
            raise FileNotFoundError(
                f"No Criteo data found in {DATA_DIR}. "
                f"Files present: {os.listdir(DATA_DIR)}"
            )

    print(f"\nLoading raw data from {data_file} ...")
    print(f"  (reading up to {MAX_ROWS:,} rows)")

    # Read in chunks for memory efficiency
    cat_cols = [f"cat{i}" for i in range(1, 10)] + ["campaign"]
    use_cols = cat_cols + ["click"]

    chunks = []
    n_read = 0
    for chunk in pd.read_csv(
        data_file, sep="\t", usecols=use_cols,
        chunksize=200_000, dtype=str, na_values=[""],
        compression=compression,
    ):
        chunk["click"] = pd.to_numeric(chunk["click"], errors="coerce").fillna(0).astype(int)
        # Fill NaN categoricals with "MISSING"
        for c in cat_cols:
            chunk[c] = chunk[c].fillna("MISSING")
        chunks.append(chunk)
        n_read += len(chunk)
        print(f"  Read {n_read:,} rows ...", end="\r", flush=True)
        if n_read >= MAX_ROWS:
            break

    df = pd.concat(chunks, ignore_index=True)
    print(f"\n  Total rows loaded: {len(df):,}")
    print(f"  Click rate: {df['click'].mean():.4f}")
    print(f"  Clicked:     {df['click'].sum():,}")
    print(f"  Non-clicked: {(1 - df['click']).sum():,.0f}")

    # ---- One-hot encode ----
    print("\nOne-hot encoding categorical features ...")
    # Limit cardinality: keep top-N most frequent values per feature
    MAX_CARD = 500
    for c in cat_cols:
        top_vals = df[c].value_counts().head(MAX_CARD).index
        df[c] = df[c].where(df[c].isin(top_vals), other="OTHER")

    from sklearn.preprocessing import OneHotEncoder
    enc = OneHotEncoder(sparse_output=True, handle_unknown="ignore")
    X_onehot = enc.fit_transform(df[cat_cols])
    print(f"  One-hot shape: {X_onehot.shape}")

    y = df["click"].values.astype(float)

    # ---- Truncated SVD ----
    print(f"\nApplying TruncatedSVD to {N_SVD} dimensions ...")
    svd = TruncatedSVD(n_components=N_SVD, random_state=42)
    X_svd = svd.fit_transform(X_onehot)
    explained = svd.explained_variance_ratio_.sum()
    print(f"  Explained variance ratio (top {N_SVD}): {explained:.4f}")
    print(f"  X_svd shape: {X_svd.shape}")

    # Normalize rows to unit norm
    norms = np.linalg.norm(X_svd, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-8)
    X_svd = X_svd / norms

    # ---- Fit theta_star ----
    print("\nFitting theta_star via Ridge regression ...")
    reg = Ridge(alpha=1.0)
    reg.fit(X_svd, y)
    theta_star = reg.coef_.astype(np.float64)
    print(f"  theta_star shape: {theta_star.shape}")
    print(f"  ||theta_star||_2 = {np.linalg.norm(theta_star):.4f}")
    print(f"  R^2 on training data: {reg.score(X_svd, y):.4f}")

    # ---- Build pools ----
    print("\nBuilding clicked / non-clicked pools ...")
    clicked_mask = (y == 1)
    nonclicked_mask = (y == 0)

    X_clicked_all = X_svd[clicked_mask]
    X_nonclicked_all = X_svd[nonclicked_mask]
    print(f"  Available clicked:     {X_clicked_all.shape[0]:,}")
    print(f"  Available non-clicked: {X_nonclicked_all.shape[0]:,}")

    rng = np.random.default_rng(42)

    n_clicked = min(POOL_SIZE, X_clicked_all.shape[0])
    n_nonclicked = min(POOL_SIZE, X_nonclicked_all.shape[0])

    idx_c = rng.choice(X_clicked_all.shape[0], size=n_clicked, replace=False)
    idx_nc = rng.choice(X_nonclicked_all.shape[0], size=n_nonclicked, replace=False)

    X_clicked = X_clicked_all[idx_c]
    X_nonclicked = X_nonclicked_all[idx_nc]

    print(f"  Pool sizes: clicked={n_clicked}, non-clicked={n_nonclicked}")

    # ---- Save ----
    os.makedirs(DATA_DIR, exist_ok=True)
    np.savez_compressed(
        OUT_FILE,
        X_clicked=X_clicked,
        X_nonclicked=X_nonclicked,
        theta_star=theta_star,
    )
    print(f"\nSaved processed data to: {OUT_FILE}")

    return dict(X_clicked=X_clicked, X_nonclicked=X_nonclicked, theta_star=theta_star)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not download_criteo():
        sys.exit(1)
    preprocess()
    print("\nDone.")
