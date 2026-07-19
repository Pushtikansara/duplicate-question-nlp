"""Data Loader — loads the Quora duplicate questions dataset and provides
train/val/test splits accessible from Python modules (not just notebooks).

Split: 80/10/10 — stratified by label, random_state=42.

Usage:
    from duplicate_question_app.data_loader import get_quora_splits
    train_df, val_df, test_df = get_quora_splits()
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split


def get_quora_splits(
    data_path: Path | str | None = None,
    random_state: int = 42,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load cleaned Quora data and return stratified train/val/test splits.

    Args:
        data_path: Path to cleaned_quora.parquet. If None, auto-detect.
        random_state: Random seed for reproducibility.
        val_ratio: Fraction for validation (default 0.1).
        test_ratio: Fraction for testing (default 0.1).

    Returns:
        (train_df, val_df, test_df) each with columns [q1, q2, label].
    """
    if data_path is None:
        root = Path(__file__).resolve().parents[2]  # project root
        data_path = root / "data" / "cleaned_quora.parquet"

    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    df = pd.read_parquet(data_path)

    # Standardize to [q1, q2, label] columns
    rename_map: dict[str, str] = {}
    for col in df.columns:
        lowered = col.lower().strip()
        if lowered in ("sentence1", "question1", "q1"):
            rename_map[col] = "q1"
        elif lowered in ("sentence2", "question2", "q2"):
            rename_map[col] = "q2"
        elif lowered in ("label", "is_duplicate"):
            rename_map[col] = "label"

    if rename_map:
        df = df.rename(columns=rename_map)
    df = df[["q1", "q2", "label"]].copy()

    # Split: first separate test, then split remaining into train/val
    train_val, test_df = train_test_split(
        df,
        test_size=test_ratio,
        random_state=random_state,
        stratify=df["label"],
    )

    # Adjust val_ratio for the smaller pool: val_ratio / (1 - test_ratio)
    adjusted_val = val_ratio / (1.0 - test_ratio)
    train_df, val_df = train_test_split(
        train_val,
        test_size=adjusted_val,
        random_state=random_state,
        stratify=train_val["label"],
    )

    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    return train_df, val_df, test_df


def load_quora_data(
    data_path: Path | str | None = None,
) -> pd.DataFrame:
    """Load the full cleaned Quora dataset with standardized columns."""
    if data_path is None:
        root = Path(__file__).resolve().parents[2]
        data_path = root / "data" / "cleaned_quora.parquet"

    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    df = pd.read_parquet(data_path)

    rename_map: dict[str, str] = {}
    for col in df.columns:
        lowered = col.lower().strip()
        if lowered in ("sentence1", "question1", "q1"):
            rename_map[col] = "q1"
        elif lowered in ("sentence2", "question2", "q2"):
            rename_map[col] = "q2"
        elif lowered in ("label", "is_duplicate"):
            rename_map[col] = "label"

    if rename_map:
        df = df.rename(columns=rename_map)

    return df
