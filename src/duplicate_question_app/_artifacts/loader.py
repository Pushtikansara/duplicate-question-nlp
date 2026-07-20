from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from duplicate_question_app._config.settings import AppPaths


def _read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _read_parquet_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def _parse_tensor_label(value: Any) -> int:
    if isinstance(value, (int, np.integer)):
        return int(value)
    if pd.isna(value):
        return 0

    text = str(value).strip()
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return 0


def load_dataset_frame(paths: AppPaths) -> pd.DataFrame:
    parquet_path = paths.data_dir / "cleaned_quora.parquet"
    csv_path = paths.data_dir / "cleaned_quora.csv"

    if parquet_path.exists():
        return pd.read_parquet(parquet_path)
    if csv_path.exists():
        return pd.read_csv(csv_path)
    raise FileNotFoundError("No cleaned dataset found. Expected data/cleaned_quora.parquet or data/cleaned_quora.csv.")


def build_dataset_summary(df: pd.DataFrame) -> dict[str, Any]:
    summary = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "missing_values": df.isna().sum().to_dict(),
        "preview": df.head(5),
    }

    label_column = "label" if "label" in df.columns else "is_duplicate"
    if label_column in df.columns:
        label_counts = df[label_column].value_counts(dropna=False).sort_index()
        summary["label_column"] = label_column
        summary["label_counts"] = label_counts.to_dict()
        summary["duplicate_ratio"] = float(label_counts.get(1, 0) / len(df)) if len(df) else 0.0
        summary["non_duplicate_ratio"] = float(label_counts.get(0, 0) / len(df)) if len(df) else 0.0
    else:
        summary["label_column"] = None
        summary["label_counts"] = {}
        summary["duplicate_ratio"] = 0.0
        summary["non_duplicate_ratio"] = 0.0

    return summary


def reconstruct_week3_test_frame(paths: AppPaths) -> pd.DataFrame:
    df = load_dataset_frame(paths).copy()

    question1_column = "clean_q1" if "clean_q1" in df.columns else "sentence1" if "sentence1" in df.columns else "q1"
    question2_column = "clean_q2" if "clean_q2" in df.columns else "sentence2" if "sentence2" in df.columns else "q2"
    label_column = "label" if "label" in df.columns else "is_duplicate"

    working_df = df.rename(
        columns={
            question1_column: "q1",
            question2_column: "q2",
            label_column: "is_duplicate",
        }
    )[["q1", "q2", "is_duplicate"]]

    # Use a deterministic hash-based split to avoid non-reproducible test sets
    # when the dataset changes or train_test_split produces different indices
    row_hash = (
        working_df["q1"].str.len().astype(str)
        + working_df["q2"].str.len().astype(str)
        + working_df["is_duplicate"].astype(str)
    )
    test_mask = pd.util.hash_pandas_object(row_hash) % 5 == 0
    test_df = working_df[test_mask].reset_index(drop=True)
    if len(test_df) < 100:
        _, test_df = train_test_split(
            working_df,
            test_size=0.2,
            random_state=42,
            stratify=working_df["is_duplicate"],
        )
    return test_df.reset_index(drop=True)


def load_week2_vs_week3_comparison(paths: AppPaths) -> pd.DataFrame:
    comparison_path = paths.transformer_results_dir / "week2_vs_week3_comparison.csv"
    return _read_csv_if_exists(comparison_path)


def load_week2_model_comparison(paths: AppPaths) -> pd.DataFrame:
    comparison_path = paths.baseline_results_dir / "week2_model_comparison.parquet"
    df = _read_parquet_if_exists(comparison_path)
    if df.empty:
        return df

    return df.reset_index().rename(columns={"index": "Model"})


def load_transformer_predictions(paths: AppPaths) -> pd.DataFrame:
    predictions_path = paths.transformer_results_dir / "transformer_test_predictions.csv"
    df = _read_csv_if_exists(predictions_path)
    if df.empty:
        return df

    df["true_label"] = df["true_label"].map(_parse_tensor_label)
    df["predicted_label"] = df["predicted_label"].astype(int)

    logits = df[["confidence_non_dup", "confidence_dup"]].to_numpy(dtype=float)
    probabilities = softmax(logits, axis=1)
    df["prob_non_duplicate"] = probabilities[:, 0]
    df["prob_duplicate"] = probabilities[:, 1]
    df["confidence"] = df[["prob_non_duplicate", "prob_duplicate"]].max(axis=1)
    df["predicted_class_name"] = np.where(df["predicted_label"] == 1, "Duplicate", "Non-Duplicate")
    df["actual_class_name"] = np.where(df["true_label"] == 1, "Duplicate", "Non-Duplicate")
    return df


def build_transformer_metrics(predictions_df: pd.DataFrame) -> dict[str, Any]:
    if predictions_df.empty:
        return {}

    y_true = predictions_df["true_label"].to_numpy(dtype=int)
    y_pred = predictions_df["predicted_label"].to_numpy(dtype=int)
    y_score = predictions_df["prob_duplicate"].to_numpy(dtype=float)

    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred),
    }

    try:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
        fpr, tpr, thresholds = roc_curve(y_true, y_score)
        metrics["roc_curve"] = {
            "fpr": fpr,
            "tpr": tpr,
            "thresholds": thresholds,
        }
    except ValueError:
        metrics["roc_auc"] = None
        metrics["roc_curve"] = None

    return metrics


def load_confusion_matrix_csv(paths: AppPaths) -> pd.DataFrame:
    cm_path = paths.transformer_results_dir / "transformer_confusion_matrix.csv"
    return _read_csv_if_exists(cm_path)


def load_week4_threshold_analysis(paths: AppPaths) -> pd.DataFrame:
    threshold_path = paths.week4_results_dir / "threshold_analysis.csv"
    return _read_csv_if_exists(threshold_path)


def load_week4_ablation(paths: AppPaths) -> pd.DataFrame:
    ablation_path = paths.week4_results_dir / "ablation_study.csv"
    return _read_csv_if_exists(ablation_path)


def load_week4_predictions(paths: AppPaths) -> pd.DataFrame:
    predictions_path = paths.week4_results_dir / "predictions_week4.csv"
    df = _read_csv_if_exists(predictions_path)
    if df.empty:
        return df

    if "true_label" in df.columns:
        df["true_label"] = df["true_label"].map(_parse_tensor_label)
    if "pred_label" in df.columns:
        df["pred_label"] = df["pred_label"].astype(int)

    if "prob_dup" in df.columns:
        df["prob_duplicate"] = df["prob_dup"].astype(float)
        df["prob_non_duplicate"] = 1.0 - df["prob_duplicate"]
    elif {"confidence_non_dup", "confidence_dup"}.issubset(df.columns):
        logits = df[["confidence_non_dup", "confidence_dup"]].to_numpy(dtype=float)
        probabilities = softmax(logits, axis=1)
        df["prob_non_duplicate"] = probabilities[:, 0]
        df["prob_duplicate"] = probabilities[:, 1]
    else:
        df["prob_non_duplicate"] = np.nan
        df["prob_duplicate"] = np.nan

    if "confidence" not in df.columns:
        df["confidence"] = df[["prob_non_duplicate", "prob_duplicate"]].max(axis=1)

    if "pred_label" in df.columns:
        df["predicted_class_name"] = np.where(df["pred_label"] == 1, "Duplicate", "Non-Duplicate")
    if "true_label" in df.columns:
        df["actual_class_name"] = np.where(df["true_label"] == 1, "Duplicate", "Non-Duplicate")

    return df


def build_week4_metrics(predictions_df: pd.DataFrame) -> dict[str, Any]:
    if predictions_df.empty:
        return {}

    required_columns = {"true_label", "pred_label"}
    if not required_columns.issubset(predictions_df.columns):
        return {}

    y_true = predictions_df["true_label"].to_numpy(dtype=int)
    y_pred = predictions_df["pred_label"].to_numpy(dtype=int)
    y_score = (
        predictions_df["prob_duplicate"].to_numpy(dtype=float) if "prob_duplicate" in predictions_df.columns else None
    )

    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred),
    }

    if y_score is None or np.isnan(y_score).all():
        metrics["roc_auc"] = None
        metrics["roc_curve"] = None
        return metrics

    try:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
        fpr, tpr, thresholds = roc_curve(y_true, y_score)
        metrics["roc_curve"] = {"fpr": fpr, "tpr": tpr, "thresholds": thresholds}
    except ValueError:
        metrics["roc_auc"] = None
        metrics["roc_curve"] = None

    return metrics


def available_week4_plots(paths: AppPaths) -> list[Path]:
    if not paths.week4_results_dir.exists():
        return []

    preferred_order = [
        "fig1_threshold_tuning.png",
        "fig2_error_analysis.png",
        "fig3_ablation_comparison.png",
        "fig4_roc_comparison.png",
    ]
    plots: list[Path] = []
    for filename in preferred_order:
        plot_path = paths.week4_results_dir / filename
        if plot_path.exists():
            plots.append(plot_path)
    return plots
