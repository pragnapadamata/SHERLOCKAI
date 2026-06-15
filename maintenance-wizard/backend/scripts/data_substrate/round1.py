"""Read-only access and profiling for the real Round 1 hot-rolling CSVs.

This module never modifies the Round 1 files. It loads them, exposes the
defect-positive Coil IDs (used to bind the data into the plant narrative), and
computes a profile for documentation. The actual defect classifier is a Phase 3
concern.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from backend.scripts.data_substrate import spec

TRAIN_PATH = spec.ROUND1_DIR / "train.csv"
TEST_PATH = spec.ROUND1_DIR / "test.csv"

FEATURE_COLS = [f"X{i}" for i in range(1, 50)]
ID_COL = "CoilID"
TARGET_COL = "Y"


@lru_cache
def load_train() -> pd.DataFrame:
    return pd.read_csv(TRAIN_PATH)


@lru_cache
def load_test() -> pd.DataFrame:
    return pd.read_csv(TEST_PATH)


def positive_coil_ids(n: int | None = None) -> list[str]:
    """Return defect-positive (Y==1) Coil IDs, sorted for determinism."""

    df = load_train()
    ids = sorted(df.loc[df[TARGET_COL] == 1, ID_COL].astype(str).tolist())
    return ids if n is None else ids[:n]


def iter_all_coils() -> list[tuple[str, str]]:
    """Return (coil_id, source) for every coil: train rows first, then test."""

    train_ids = [(str(c), "train") for c in load_train()[ID_COL].tolist()]
    test_ids = [(str(c), "test") for c in load_test()[ID_COL].tolist()]
    return train_ids + test_ids


def profile() -> dict:
    """Compute a documentation profile of the Round 1 data (no modification)."""

    train = load_train()
    test = load_test()

    target = train[TARGET_COL]
    positives = int((target == 1).sum())

    missing_per_col = train[FEATURE_COLS].isna().sum()
    cols_with_missing = {
        col: int(cnt) for col, cnt in missing_per_col.items() if cnt > 0
    }

    feature_stats: dict[str, dict] = {}
    for col in FEATURE_COLS:
        s = train[col]
        feature_stats[col] = {
            "mean": _round(s.mean()),
            "std": _round(s.std()),
            "min": _round(s.min()),
            "max": _round(s.max()),
            "missing": int(s.isna().sum()),
        }

    return {
        "source": "Tata Steel Round 1 - Defect Detection in Hot Rolling",
        "train_rows": int(train.shape[0]),
        "train_cols": int(train.shape[1]),
        "test_rows": int(test.shape[0]),
        "test_cols": int(test.shape[1]),
        "feature_columns": len(FEATURE_COLS),
        "target_column": TARGET_COL,
        "target_positives": positives,
        "target_positive_fraction": _round(positives / len(target), 5),
        "total_missing_cells_train": int(missing_per_col.sum()),
        "columns_with_missing_count": len(cols_with_missing),
        "columns_with_missing": cols_with_missing,
        "sample_positive_coil_ids": positive_coil_ids(8),
        "feature_stats": feature_stats,
        "original_metric": "100% recall with >90% precision (recall-prioritized defect detection)",
    }


def _round(value, ndigits: int = 4):
    try:
        return round(float(value), ndigits)
    except (TypeError, ValueError):
        return None
