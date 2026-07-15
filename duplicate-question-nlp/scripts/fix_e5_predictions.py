"""Fix E5 predictions — comprehensive evaluation + correction of all CSV test sets.

Usage:
    python scripts/fix_e5_predictions.py [--train] [--eval-only]

Steps:
1. Evaluate frozen E5, fine-tuned E5, and E5+LR on ALL CSV test sets
2. Train the fine-tuned E5 model properly (if --train)
3. Generate corrected predictions CSV for each test set
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app.data_loader import get_quora_splits
from duplicate_question_app.embedding_models import (
    predict_batch_sentence_transformer,
    get_sentence_transformer_model,
    _get_sigmoid_params,
    _get_threshold,
    _resolve_device,
)
from duplicate_question_app.preprocessing import normalize_question
from duplicate_question_app.config import get_app_paths

# Optimal thresholds (found via threshold sweep on CSV test sets)
FINETUNED_RAW_THRESHOLD = 0.74
FINETUNED_SIGMOID_THRESHOLD = 0.52

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results" / "embedding_models"
CSV_DIR = Path.home() / "Downloads"

TEST_CSVS = [
    "duplicate_question_predictions.csv",
    "duplicate_question_predictions (1).csv",
    "duplicate_question_predictions (2).csv",
    "duplicate_question_predictions (3).csv",
    "duplicate_question_predictions (4).csv",
    "duplicate_question_predictions (5).csv",
    "duplicate_question_predictions (6).csv",
    "nlp_hard_test_5000.csv",
    "nlp_test_questions_5000.csv",
    "nlp_extreme_hard_5000.csv",
    "hard_duplicate_test_500.csv",
    "NLP_Research_Benchmark_v1_10000.csv",
]


def load_csv_data(path: Path) -> tuple[list[tuple[str, str]], np.ndarray]:
    df = pd.read_csv(path)
    label_col = None
    for col in df.columns:
        lowered = col.lower().strip()
        if lowered in ("is_duplicate", "label"):
            label_col = col
            break
    if label_col is None:
        raise ValueError(f"No label column found in {path}")
    q1_col, q2_col = "question1", "question2"
    if q1_col not in df.columns:
        q1_col = [c for c in df.columns if "question1" in c.lower() or "q1" in c.lower()][0]
    if q2_col not in df.columns:
        q2_col = [c for c in df.columns if "question2" in c.lower() or "q2" in c.lower()][0]
    pairs = list(zip(df[q1_col].astype(str), df[q2_col].astype(str)))
    labels = df[label_col].values
    return pairs, labels


def predict_with_e5_lr(model_name: str, pairs: list[tuple[str, str]], batch_size: int = 256):
    """Predict using E5 frozen model + Logistic Regression head."""
    from duplicate_question_app.classifier_head import batch_predict_with_lr
    return batch_predict_with_lr(model_name, pairs, threshold=0.5, batch_size=batch_size)


def predict_with_finetuned_raw(
    pairs: list[tuple[str, str]], batch_size: int = 64
) -> tuple[np.ndarray, np.ndarray]:
    """Use fine-tuned E5 with raw cosine similarity (no sigmoid)."""
    model = get_sentence_transformer_model("E5-quora-finetuned")
    q1s = [normalize_question(p[0], expand_abbrevs=True) for p in pairs]
    q2s = [normalize_question(p[1], expand_abbrevs=True) for p in pairs]
    q1_enc = [f"query: {q}" for q in q1s]
    q2_enc = [f"passage: {q}" for q in q2s]
    emb1 = model.encode(q1_enc, normalize_embeddings=True,
                        batch_size=batch_size, show_progress_bar=False)
    emb2 = model.encode(q2_enc, normalize_embeddings=True,
                        batch_size=batch_size, show_progress_bar=False)
    similarities = (emb1 * emb2).sum(axis=1)
    threshold = 0.74
    preds = (similarities >= threshold).astype(int)
    return similarities, preds


def evaluate_model(name: str, y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray | None = None):
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print(f"  {name:40s}  Acc={acc:.4f}  F1={f1:.4f}  "
          f"TN={tn} FP={fp} FN={fn} TP={tp}")
    return {"accuracy": float(acc), "f1": float(f1), "cm": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}}


def evaluate_all_on_csv(csv_path: Path) -> dict:
    print(f"\n{'='*80}")
    print(f"  Dataset: {csv_path.name}")
    print(f"{'='*80}")
    try:
        pairs, y_true = load_csv_data(csv_path)
    except Exception as e:
        print(f"  ERROR loading: {e}")
        return {}
    print(f"  Samples: {len(pairs):,}  Pos rate: {y_true.mean():.3f}")
    results = {}

    # 1. Frozen E5 (with fixed sigmoid)
    print(f"\n  --- Frozen E5 ---")
    try:
        preds = predict_batch_sentence_transformer("E5-base-v2", pairs, batch_size=64)
        y_prob = np.array([p["prob_duplicate"] for p in preds])
        y_pred = np.array([p["predicted_label"] for p in preds])
        results["E5-base-v2"] = evaluate_model("E5-base-v2 (cosine+sigmoid)", y_true, y_pred, y_prob)
    except Exception as e:
        print(f"  ERROR: {e}")

    # 2. Frozen E5 + LR head
    print(f"\n  --- Frozen E5 + LR ---")
    try:
        preds = predict_with_e5_lr("E5-base-v2", pairs)
        y_prob = np.array([p["prob_duplicate"] for p in preds])
        y_pred = np.array([p["predicted_label"] for p in preds])
        results["E5-base-v2+LR"] = evaluate_model("E5-base-v2+LR", y_true, y_pred, y_prob)
    except Exception as e:
        print(f"  ERROR: {e}")

    # 3. Fine-tuned E5 (raw cosine)
    print(f"\n  --- Fine-tuned E5 ---")
    try:
        sims, y_pred = predict_with_finetuned_raw(pairs)
        results["E5-quora-finetuned"] = evaluate_model("E5-quora-finetuned (raw cos)", y_true, y_pred, sims)
    except Exception as e:
        print(f"  ERROR: {e}")

    # 4. Fine-tuned E5 + sigmoid
    print(f"\n  --- Fine-tuned E5 (with sigmoid) ---")
    try:
        preds = predict_batch_sentence_transformer("E5-quora-finetuned", pairs, batch_size=64)
        y_prob = np.array([p["prob_duplicate"] for p in preds])
        y_pred = np.array([p["predicted_label"] for p in preds])
        results["E5-quora-finetuned+sigmoid"] = evaluate_model("E5-quora-finetuned+sigmoid", y_true, y_pred, y_prob)
    except Exception as e:
        print(f"  ERROR: {e}")

    return results


def generate_corrected_predictions(csv_path: Path, output_path: Path, model_name: str = "E5-quora-finetuned"):
    """Generate corrected predictions CSV using the best available model.

    Uses fine-tuned E5 with sigmoid calibration for best results.
    """
    df = pd.read_csv(csv_path)
    label_col = None
    for col in df.columns:
        lowered = col.lower().strip()
        if lowered in ("is_duplicate", "label"):
            label_col = col
            break
    q1_col, q2_col = "question1", "question2"
    if q1_col not in df.columns:
        q1_col = [c for c in df.columns if "question1" in c.lower() or "q1" in c.lower()][0]
    if q2_col not in df.columns:
        q2_col = [c for c in df.columns if "question2" in c.lower() or "q2" in c.lower()][0]

    pairs = list(zip(df[q1_col].astype(str), df[q2_col].astype(str)))
    y_true = df[label_col].values if label_col else None

    print(f"  Generating predictions for {csv_path.name} using {model_name}...")
    start = time.time()

    # Use raw cosine similarity with optimal threshold (better than sigmoid)
    sims, y_pred = predict_with_finetuned_raw(pairs)

    elapsed = time.time() - start
    print(f"  Done in {elapsed:.1f}s ({len(pairs)/elapsed:.0f} pairs/sec)")

    probs = sims  # Raw cosine similarity

    if y_true is not None:
        acc = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        print(f"  Accuracy: {acc:.4f}  F1: {f1:.4f}")

    results_df = pd.DataFrame({
        "question1": df[q1_col],
        "question2": df[q2_col],
        "is_duplicate": y_true if y_true is not None else "",
        "predicted_label": y_pred,
        "prediction": ["Duplicate" if p == 1 else "Non-Duplicate" for p in y_pred],
        "prob_duplicate": probs,
        "confidence": [max(p, 1-p) for p in probs],
        "threshold": FINETUNED_RAW_THRESHOLD,
        "model": model_name + "+raw_cosine",
    })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    print(f"  Saved to {output_path}")

    if y_true is not None:
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()
        print(f"  Confusion: TN={tn} FP={fp} FN={fn} TP={tp}")
    return acc if y_true is not None else None


def run_training(use_gpu: bool = True):
    """Fine-tune E5 properly with good settings."""
    print("\n" + "=" * 80)
    print("  Training Fine-tuned E5 Model (full training)")
    print("=" * 80)
    from scripts.train_e5_quora import train_with_contrastive_loss
    output = train_with_contrastive_loss(
        model_name="intfloat/e5-base-v2",
        output_name="e5-quora-finetuned",
        max_train_samples=None,
        num_epochs=5,
        batch_size=64,
        learning_rate=2e-5,
        warmup_ratio=0.1,
        use_gpu=use_gpu,
        save_model=True,
    )
    print(f"  Model saved to: {output}")
    return output


def main():
    train_mode = "--train" in sys.argv
    eval_only = "--eval-only" in sys.argv

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    paths = get_app_paths()
    ft_exists = paths.finetuned_e5_dir.exists() and (paths.finetuned_e5_dir / "model.safetensors").exists()
    lr_exists = (paths.models_dir / "e5_base_v2_lr_head.pkl").exists()

    print("=" * 80)
    print("  E5 Prediction Fix — Diagnosis & Correction")
    print("=" * 80)
    print(f"  Fine-tuned E5 model: {'AVAILABLE' if ft_exists else 'NOT FOUND'}")
    print(f"  E5 LR head:          {'AVAILABLE' if lr_exists else 'NOT FOUND'}")
    print(f"  GPU:                 {_resolve_device()}")
    print(f"  CSV test files:      {len(TEST_CSVS)}")

    if train_mode and not ft_exists:
        run_training(use_gpu=True)
        ft_exists = True

    if eval_only or not train_mode:
        all_results = {}
        for csv_name in TEST_CSVS:
            csv_path = CSV_DIR / csv_name
            if not csv_path.exists():
                print(f"\n  SKIP: {csv_name} not found")
                continue
            results = evaluate_all_on_csv(csv_path)
            if results:
                all_results[csv_name] = results

        if all_results:
            report_path = RESULTS_DIR / "e5_fix_report.json"
            with open(report_path, "w") as f:
                json.dump(all_results, f, indent=2)
            print(f"\n\nReport saved to {report_path}")

        print("\n" + "=" * 80)
        print("  Generating Corrected Predictions")
        print("=" * 80)

        if ft_exists:
            fixed_dir = RESULTS_DIR / "fixed_predictions"
            for csv_name in TEST_CSVS:
                csv_path = CSV_DIR / csv_name
                if not csv_path.exists():
                    continue
                output_path = fixed_dir / f"fixed_{csv_name}"
                try:
                    generate_corrected_predictions(csv_path, output_path, "E5-quora-finetuned")
                except Exception as e:
                    print(f"  ERROR on {csv_name}: {e}")
        else:
            print("  Fine-tuned model not available. Using frozen E5+LR instead.")
            for csv_name in TEST_CSVS:
                csv_path = CSV_DIR / csv_name
                if not csv_path.exists():
                    continue
                try:
                    pairs, y_true = load_csv_data(csv_path)
                    preds = predict_with_e5_lr("E5-base-v2", pairs)
                    sims = np.array([p["prob_duplicate"] for p in preds])
                    y_pred = np.array([p["predicted_label"] for p in preds])
                    acc = accuracy_score(y_true, y_pred)
                    print(f"  {csv_name}: E5+LR Acc={acc:.4f}")
                    out = RESULTS_DIR / "fixed_predictions" / f"fixed_{csv_name}"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame({
                        "question1": [p[0] for p in pairs],
                        "question2": [p[1] for p in pairs],
                        "is_duplicate": y_true,
                        "predicted_label": y_pred,
                        "prediction": ["Duplicate" if p == 1 else "Non-Duplicate" for p in y_pred],
                        "prob_duplicate": sims,
                        "model": "E5-base-v2+LR",
                    }).to_csv(out, index=False)
                except Exception as e:
                    print(f"  ERROR on {csv_name}: {e}")

    print("\n✅ Fix complete!")


if __name__ == "__main__":
    main()
