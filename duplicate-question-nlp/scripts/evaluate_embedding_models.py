"""Evaluate all embedding models on the real Quora test split.

Measures accuracy, F1, precision, recall, ROC-AUC, ECE, Brier score
for E5, BGE, MPNet, and the ensemble on the held-out Quora test set.

Usage:
    python scripts/evaluate_embedding_models.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    brier_score_loss,
    log_loss,
    roc_curve,
    auc,
)

# Add src to path
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app.data_loader import get_quora_splits
from duplicate_question_app.embedding_models import (
    predict_batch_sentence_transformer,
    get_ensemble_prediction,
)


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results" / "embedding_models"
EMBEDDING_MODELS = ["E5-base-v2", "BGE-base-en-v1.5", "MPNet-base-v2"]


def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error."""
    if len(probs) == 0:
        return 0.0
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (probs >= bin_boundaries[i]) & (probs < bin_boundaries[i + 1])
        if i == n_bins - 1:
            mask = (probs >= bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])
        if not mask.any():
            continue
        bin_conf = probs[mask].mean()
        bin_acc = labels[mask].mean()
        ece += np.abs(bin_acc - bin_conf) * mask.sum()
    return float(ece / len(probs)) if len(probs) > 0 else 0.0


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    model_name: str,
) -> dict:
    """Compute comprehensive metrics."""
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        "model": model_name,
        "n_samples": int(len(y_true)),
        "n_duplicate": int(y_true.sum()),
        "n_non_duplicate": int((1 - y_true).sum()),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
        "log_loss": float(log_loss(y_true, y_prob)),
        "ece": float(compute_ece(y_prob, y_true)),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "classification_report": classification_report(
            y_true, y_pred, target_names=["Non-Duplicate", "Duplicate"]
        ),
    }
    return metrics


def run_evaluation() -> None:
    """Run full evaluation of all embedding models on Quora test split."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("  Embedding Model Evaluation — Real Quora Test Split")
    print("=" * 70)

    # Load data
    print("\n[1/3] Loading Quora data splits...")
    _, _, test_df = get_quora_splits()
    pairs = list(zip(test_df["q1"], test_df["q2"]))
    y_true = test_df["label"].values
    print(f"  Test pairs: {len(pairs):,}")
    print(f"  Duplicate rate: {y_true.mean():.3f}")

    all_results: dict[str, dict] = {}

    # Evaluate embedding models
    for model_name in EMBEDDING_MODELS:
        print(f"\n[2/3] Evaluating {model_name}...")
        try:
            start = time.time()
            predictions = predict_batch_sentence_transformer(
                model_name, pairs, batch_size=64
            )
            elapsed = time.time() - start

            y_prob = np.array([p["prob_duplicate"] for p in predictions])
            y_pred = np.array([p["predicted_label"] for p in predictions])

            metrics = evaluate_predictions(y_true, y_pred, y_prob, model_name)
            metrics["inference_time_sec"] = round(elapsed, 2)
            metrics["inference_speed_pairs_per_sec"] = round(len(pairs) / elapsed, 1)

            all_results[model_name] = metrics

            # Print summary
            print(f"  Accuracy:  {metrics['accuracy']:.4f}")
            print(f"  F1:        {metrics['f1']:.4f}")
            print(f"  Precision: {metrics['precision']:.4f}")
            print(f"  Recall:    {metrics['recall']:.4f}")
            print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
            print(f"  ECE:       {metrics['ece']:.4f}")
            print(f"  Brier:     {metrics['brier_score']:.4f}")
            cm = metrics["confusion_matrix"]
            print(f"  Confusion: TN={cm['tn']} FP={cm['fp']} FN={cm['fn']} TP={cm['tp']}")
            print(f"  Speed:     {metrics['inference_speed_pairs_per_sec']:.0f} pairs/sec")

        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            all_results[model_name] = {"model": model_name, "error": str(e)}

    # Evaluate ensemble
    print(f"\n[2/3] Evaluating Ensemble...")
    try:
        ensemble_probs = []
        ensemble_preds = []
        start = time.time()
        for i, (q1, q2) in enumerate(zip(test_df["q1"], test_df["q2"])):
            result = get_ensemble_prediction(q1, q2)
            ensemble_probs.append(result.get("prob_duplicate", 0.5))
            ensemble_preds.append(result.get("predicted_label", 0))
        elapsed = time.time() - start

        y_prob = np.array(ensemble_probs)
        y_pred = np.array(ensemble_preds)

        metrics = evaluate_predictions(y_true, y_pred, y_prob, "Ensemble")
        metrics["inference_time_sec"] = round(elapsed, 2)
        metrics["inference_speed_pairs_per_sec"] = round(len(pairs) / elapsed, 1)

        all_results["Ensemble"] = metrics
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  F1:        {metrics['f1']:.4f}")
        print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
        print(f"  ECE:       {metrics['ece']:.4f}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        all_results["Ensemble"] = {"model": "Ensemble", "error": str(e)}

    # Save results
    leaderboard_path = RESULTS_DIR / "leaderboard.json"
    with open(leaderboard_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[3/3] Results saved to {leaderboard_path}")

    # Print leaderboard
    print("\n" + "=" * 70)
    print("  LEADERBOARD (sorted by F1)")
    print("=" * 70)
    ranked = sorted(
        [(k, v) for k, v in all_results.items() if "error" not in v],
        key=lambda x: x[1]["f1"],
        reverse=True,
    )
    for rank, (name, m) in enumerate(ranked, 1):
        print(f"  {rank}. {name:35s} F1={m['f1']:.4f}  Acc={m['accuracy']:.4f}  "
              f"ROC={m['roc_auc']:.4f}  ECE={m['ece']:.4f}")


if __name__ == "__main__":
    run_evaluation()
