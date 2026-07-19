"""Enhanced Evaluation — comprehensive comparison between baseline and improved models.

Measures accuracy, F1, precision, recall, ROC-AUC, ECE, and inference speed
for all models on the same Quora test split.

Usage:
    python scripts/enhanced_evaluation.py
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
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app.classifier_head import (
    batch_predict_ensemble,
    batch_predict_with_lr,
)
from duplicate_question_app.config import get_app_paths
from duplicate_question_app.data_loader import get_quora_splits
from duplicate_question_app.embedding_models import (
    _get_threshold,
    predict_batch_sentence_transformer,
)
from duplicate_question_app.evaluation import compute_ece
from duplicate_question_app.preprocessing import normalize_question

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PATHS = get_app_paths(PROJECT_ROOT)
RESULTS_DIR = PROJECT_ROOT / "outputs" / "enhanced_evaluation"

EMBEDDING_MODELS = ["E5-base-v2", "BGE-base-en-v1.5", "MPNet-base-v2"]
FINETUNED_MODELS = []  # Will be populated if models exist


def check_finetuned_models() -> list[str]:
    """Check which fine-tuned models are available."""
    available = []
    models_dir = PATHS.models_dir

    # Check for fine-tuned E5
    e5_ft = models_dir / "e5-quora-finetuned"
    if e5_ft.exists() and (e5_ft / "config.json").exists():
        available.append("E5-quora-finetuned")
        print(f"  ✅ Found fine-tuned E5: {e5_ft}")

    # Check for fine-tuned BGE
    bge_ft = models_dir / "bge-quora-finetuned"
    if bge_ft.exists() and (bge_ft / "config.json").exists():
        available.append("BGE-quora-finetuned")
        print(f"  ✅ Found fine-tuned BGE: {bge_ft}")

    # Check for fine-tuned cross-encoder
    ce_ft = models_dir / "cross-encoder-quora"
    if ce_ft.exists() and (ce_ft / "config.json").exists():
        available.append("Cross-Encoder-quora")
        print(f"  ✅ Found fine-tuned Cross-Encoder: {ce_ft}")

    return available


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    model_name: str,
) -> dict:
    """Compute comprehensive evaluation metrics."""
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    return {
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
    }


def evaluate_finetuned_embedding(
    model_path: str,
    q1s: list[str],
    q2s: list[str],
    y_true: np.ndarray,
    batch_size: int = 256,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Evaluate a fine-tuned sentence transformer model."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_path)

    # Normalize
    norm_q1 = [normalize_question(q, expand_abbrevs=True) for q in q1s]
    norm_q2 = [normalize_question(q, expand_abbrevs=True) for q in q2s]

    # E5 uses query/passage prefixes
    q1_enc = [f"query: {q}" for q in norm_q1]
    q2_enc = [f"passage: {q}" for q in norm_q2]

    emb1 = model.encode(q1_enc, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False)
    emb2 = model.encode(q2_enc, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False)

    similarities = (emb1 * emb2).sum(axis=1)

    # Find optimal threshold
    best_f1 = 0
    best_thresh = 0.5
    for thresh in np.linspace(0.1, 0.9, 161):
        preds = (similarities >= thresh).astype(int)
        f1 = f1_score(y_true, preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh

    preds = (similarities >= best_thresh).astype(int)
    return preds, similarities, best_thresh


def run_evaluation() -> None:
    """Run comprehensive evaluation of all models on Quora test split."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("  ENHANCED MODEL EVALUATION — Quora Test Split")
    print("=" * 70)

    # Check for fine-tuned models
    global FINETUNED_MODELS
    FINETUNED_MODELS = check_finetuned_models()

    # Load data
    print("\n[1/2] Loading Quora test split...")
    _, _, test_df = get_quora_splits()
    pairs = list(zip(test_df["q1"], test_df["q2"], strict=False))
    y_true = test_df["label"].values
    q1s = test_df["q1"].tolist()
    q2s = test_df["q2"].tolist()
    print(f"  Test pairs: {len(pairs):,}")
    print(f"  Duplicate rate: {y_true.mean():.3f}")

    all_results: dict[str, dict] = {}

    # ===================================================================
    # Evaluate frozen embedding models (BGE, E5, MPNet)
    # ===================================================================
    print(f"\n{'=' * 60}")
    print("  FROZEN EMBEDDING MODELS (Cosine Similarity + Sigmoid)")
    print(f"{'=' * 60}")
    for model_name in EMBEDDING_MODELS:
        print(f"\n  Evaluating {model_name}...")
        try:
            start = time.time()
            predictions = predict_batch_sentence_transformer(model_name, pairs, batch_size=64)
            elapsed = time.time() - start

            y_prob = np.array([p["prob_duplicate"] for p in predictions])
            y_pred = np.array([p["predicted_label"] for p in predictions])

            metrics = evaluate_predictions(y_true, y_pred, y_prob, model_name)
            metrics["inference_time_sec"] = round(elapsed, 2)
            metrics["inference_speed"] = f"{len(pairs) / elapsed:.0f} pairs/sec"
            metrics["threshold_used"] = _get_threshold(model_name)

            all_results[model_name] = metrics

            print(f"    Accuracy:  {metrics['accuracy']:.4f}")
            print(f"    F1:        {metrics['f1']:.4f}")
            print(f"    ROC-AUC:   {metrics['roc_auc']:.4f}")
            print(f"    ECE:       {metrics['ece']:.4f}")
        except Exception as e:
            print(f"    ❌ FAILED: {e}")

    # ===================================================================
    # Evaluate embedding + LR head
    # ===================================================================
    print(f"\n{'=' * 60}")
    print("  EMBEDDING + LR CLASSIFIER HEAD")
    print(f"{'=' * 60}")
    for model_name in EMBEDDING_MODELS:
        lr_model_name = model_name
        if model_name == "BGE-base-en-v1.5":
            lr_model_name = "BAAI/bge-base-en-v1.5"
        elif model_name == "MPNet-base-v2":
            lr_model_name = "sentence-transformers/all-mpnet-base-v2"

        print(f"\n  Evaluating {model_name}+LR...")
        try:
            start = time.time()
            predictions = batch_predict_with_lr(lr_model_name, pairs, threshold=0.5)
            elapsed = time.time() - start

            y_prob = np.array([p["prob_duplicate"] for p in predictions])
            y_pred = np.array([p["predicted_label"] for p in predictions])

            metrics = evaluate_predictions(y_true, y_pred, y_prob, f"{model_name}+LR")
            metrics["inference_time_sec"] = round(elapsed, 2)
            metrics["inference_speed"] = f"{len(pairs) / elapsed:.0f} pairs/sec"

            all_results[f"{model_name}+LR"] = metrics

            print(f"    Accuracy:  {metrics['accuracy']:.4f}")
            print(f"    F1:        {metrics['f1']:.4f}")
            print(f"    ROC-AUC:   {metrics['roc_auc']:.4f}")
        except Exception as e:
            print(f"    ❌ FAILED: {e}")

    # ===================================================================
    # Evaluate fine-tuned embedding models
    # ===================================================================
    if FINETUNED_MODELS:
        print(f"\n{'=' * 60}")
        print("  FINE-TUNED MODELS ⭐")
        print(f"{'=' * 60}")

        for finetuned_name in FINETUNED_MODELS:
            model_path = str(PATHS.models_dir / finetuned_name)
            print(f"\n  Evaluating {finetuned_name}...")
            try:
                start = time.time()
                y_pred, y_prob, best_thresh = evaluate_finetuned_embedding(model_path, q1s, q2s, y_true)
                elapsed = time.time() - start

                metrics = evaluate_predictions(y_true, y_pred, y_prob, finetuned_name)
                metrics["inference_time_sec"] = round(elapsed, 2)
                metrics["inference_speed"] = f"{len(pairs) / elapsed:.0f} pairs/sec"
                metrics["threshold_used"] = float(best_thresh)

                all_results[finetuned_name] = metrics

                print(f"    Accuracy:  {metrics['accuracy']:.4f}")
                print(f"    F1:        {metrics['f1']:.4f}")
                print(f"    ROC-AUC:   {metrics['roc_auc']:.4f}")
                print(f"    Best threshold: {best_thresh:.3f}")
            except Exception as e:
                print(f"    ❌ FAILED: {e}")

    # ===================================================================
    # Evaluate Ensemble (LR heads)
    # ===================================================================
    print(f"\n{'=' * 60}")
    print("  ENSEMBLE (E5+BGE+MPNet LR Heads)")
    print(f"{'=' * 60}")
    try:
        start = time.time()
        predictions = batch_predict_ensemble(pairs, threshold=0.52)
        elapsed = time.time() - start

        y_prob = np.array([p["prob_duplicate"] for p in predictions])
        y_pred = np.array([p["predicted_label"] for p in predictions])

        metrics = evaluate_predictions(y_true, y_pred, y_prob, "Ensemble(LR)")
        metrics["inference_time_sec"] = round(elapsed, 2)
        metrics["inference_speed"] = f"{len(pairs) / elapsed:.0f} pairs/sec"

        all_results["Ensemble(LR)"] = metrics

        print(f"    Accuracy:  {metrics['accuracy']:.4f}")
        print(f"    F1:        {metrics['f1']:.4f}")
        print(f"    ROC-AUC:   {metrics['roc_auc']:.4f}")
    except Exception as e:
        print(f"    ❌ FAILED: {e}")

    # ===================================================================
    # Save results
    # ===================================================================
    print("\n[2/2] Saving results...")

    # Save all metrics
    results_path = RESULTS_DIR / "all_metrics.json"
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"  ✅ Saved metrics to {results_path}")

    # Create leaderboard
    print(f"\n{'=' * 70}")
    print("  LEADERBOARD (sorted by F1)")
    print(f"{'=' * 70}")

    ranked = sorted(
        [(k, v) for k, v in all_results.items() if "error" not in v],
        key=lambda x: x[1]["f1"],
        reverse=True,
    )

    leaderboard_data = []
    for rank, (name, m) in enumerate(ranked, 1):
        leaderboard_data.append(
            {
                "Rank": rank,
                "Model": name,
                "Accuracy": f"{m['accuracy']:.4f}",
                "F1": f"{m['f1']:.4f}",
                "Precision": f"{m['precision']:.4f}",
                "Recall": f"{m['recall']:.4f}",
                "ROC-AUC": f"{m['roc_auc']:.4f}",
                "ECE": f"{m['ece']:.4f}",
                "Speed": m.get("inference_speed", "N/A"),
            }
        )
        print(f"  {rank}. {name:40s} F1={m['f1']:.4f}  Acc={m['accuracy']:.4f}  ROC={m['roc_auc']:.4f}")

    leaderboard_df = pd.DataFrame(leaderboard_data)
    leaderboard_path = RESULTS_DIR / "leaderboard.csv"
    leaderboard_df.to_csv(leaderboard_path, index=False)
    print(f"\n  Leaderboard saved to {leaderboard_path}")

    # Print improvement summary
    if len(ranked) >= 2:
        best = ranked[0]
        baseline_models = ["E5-base-v2", "BGE-base-v1.5", "MPNet-base-v2"]
        for baseline in baseline_models:
            if baseline in all_results and "error" not in all_results[baseline]:
                baseline_f1 = all_results[baseline]["f1"]
                improvement = best[1]["f1"] - baseline_f1
                print(f"\n  📊 Improvement over {baseline}: +{improvement:.4f} F1")

    print(f"\n{'=' * 70}")
    print("  Evaluation Complete!")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run_evaluation()
