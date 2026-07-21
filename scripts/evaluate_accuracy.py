"""Accuracy Evaluation — compare CrossEncoder vs Semantic vs Fusion on validation data.

Usage:
    python scripts/evaluate_accuracy.py [--sample N]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
import pandas as pd

from duplicate_question_app._models.embeddings import predict_with_sentence_transformer
from duplicate_question_app._semantic_intelligence.fusion import DecisionFusion, FusionStrategy
from duplicate_question_app._semantic_intelligence.semantic_pipeline import SemanticPipelineService


def load_validation_data(sample: int | None = None) -> pd.DataFrame:
    data_path = Path(__file__).resolve().parent.parent / "data" / "cleaned_quora.csv"
    if not data_path.exists():
        print(f"Validation data not found at {data_path}")
        sys.exit(1)
    df = pd.read_csv(data_path, nrows=sample if sample else None)
    print(f"Loaded {len(df):,} validation pairs")
    return df


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray | None = None) -> dict:
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    result = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }

    if y_prob is not None:
        try:
            result["roc_auc"] = roc_auc_score(y_true, y_prob)
        except Exception:
            result["roc_auc"] = 0.0

    cm = confusion_matrix(y_true, y_pred)
    result["confusion_matrix"] = cm.tolist()

    return result


def main():
    parser = argparse.ArgumentParser(description="Accuracy Evaluation")
    parser.add_argument("--sample", type=int, default=500, help="Number of validation pairs to sample")
    parser.add_argument("--model", type=str, default="Cross-Encoder-Quora (Trained)")
    args = parser.parse_args()

    df = load_validation_data(args.sample)
    if "is_duplicate" not in df.columns:
        print("Expected 'is_duplicate' column in validation data")
        sys.exit(1)

    pairs = list(zip(df["question1"].fillna("").astype(str), df["question2"].fillna("").astype(str), strict=False))
    y_true = df["is_duplicate"].values

    semantic_pipeline = SemanticPipelineService()

    strategies = {
        "CrossEncoder Only": FusionStrategy.CROSS_ENCODER_ONLY,
        "Semantic Only": FusionStrategy.SEMANTIC_ONLY,
        "Fusion (Balanced)": FusionStrategy.FUSION,
        "CrossEncoder Dominant": FusionStrategy.CROSS_ENCODER_DOMINANT,
        "Semantic Dominant": FusionStrategy.SEMANTIC_DOMINANT,
        "Confidence Weighted": FusionStrategy.CONFIDENCE_WEIGHTED,
        "Adaptive": FusionStrategy.ADAPTIVE,
    }

    results = []

    for strategy_name, strategy in strategies.items():
        print(f"\nEvaluating {strategy_name}...")
        fusion = DecisionFusion(strategy=strategy)
        predictions = []
        probabilities = []
        latencies = []
        errors = 0

        start = time.time()
        for i, (q1, q2) in enumerate(pairs):
            if i % 100 == 0 and i > 0:
                elapsed = time.time() - start
                avg = elapsed / i
                remaining = avg * (len(pairs) - i)
                print(f"  [{i}/{len(pairs)}] avg={avg * 1000:.0f}ms ETA={remaining:.0f}s", end="\r")

            t0 = time.perf_counter()
            try:
                if strategy == FusionStrategy.CROSS_ENCODER_ONLY:
                    base = predict_with_sentence_transformer(args.model, q1, q2)
                    ce_score = float(base.get("prob_duplicate", 0.5))
                    fusion_result = fusion.fuse(cross_encoder_score=ce_score, semantic_assessment=None)
                else:
                    base = predict_with_sentence_transformer(args.model, q1, q2)
                    ce_score = float(base.get("prob_duplicate", 0.5))
                    assessment, _ = semantic_pipeline.assess(q1, q2)
                    assessment_dict = assessment.to_dict() if assessment else None
                    fusion_result = fusion.fuse(cross_encoder_score=ce_score, semantic_assessment=assessment_dict)

                score = fusion_result.get("final_score", 0.5)
                pred = 1 if score >= 0.5 else 0
                predictions.append(pred)
                probabilities.append(score)
                latencies.append((time.perf_counter() - t0) * 1000)
            except Exception:
                predictions.append(0)
                probabilities.append(0.5)
                errors += 1

        elapsed = time.time() - start
        avg_latency = np.mean(latencies) if latencies else 0

        metrics = evaluate_predictions(y_true, np.array(predictions), np.array(probabilities))
        metrics["strategy"] = strategy_name
        metrics["avg_latency_ms"] = round(avg_latency, 2)
        metrics["total_time_s"] = round(elapsed, 2)
        metrics["errors"] = errors
        results.append(metrics)

        print(f"\n  {strategy_name}:")
        print(f"    Accuracy:  {metrics['accuracy']:.4f}")
        print(f"    Precision: {metrics['precision']:.4f}")
        print(f"    Recall:    {metrics['recall']:.4f}")
        print(f"    F1:        {metrics['f1']:.4f}")
        print(f"    ROC-AUC:   {metrics.get('roc_auc', 0):.4f}")
        print(f"    Avg Lat:   {avg_latency:.1f}ms")
        print(f"    Total:     {elapsed:.1f}s")

    print("\n" + "=" * 80)
    print("ACCURACY COMPARISON REPORT")
    print("=" * 80)

    results_df = pd.DataFrame(results)
    results_df = results_df[
        ["strategy", "accuracy", "precision", "recall", "f1", "roc_auc", "avg_latency_ms", "total_time_s", "errors"]
    ]
    results_df.columns = [
        "Strategy",
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
        "ROC-AUC",
        "Avg Latency (ms)",
        "Total Time (s)",
        "Errors",
    ]
    results_df = results_df.sort_values("F1", ascending=False)
    print(results_df.to_string(index=False))

    best = results_df.iloc[0]
    ce_only = results_df[results_df["Strategy"] == "CrossEncoder Only"].iloc[0]
    print(f"\nBest strategy: {best['Strategy']} (F1={best['F1']:.4f})")
    print(f"CE Only: {ce_only['Strategy']} (F1={ce_only['F1']:.4f})")

    if best["Strategy"] != "CrossEncoder Only" and best["F1"] > ce_only["F1"]:
        print(f"\n✓ Fusion ({best['Strategy']}) improves over CrossEncoder-only!")
        print(f"  F1 gain: {best['F1'] - ce_only['F1']:+.4f}")
    else:
        print("\n✗ Fusion does NOT improve over CrossEncoder-only.")
        print("  Recommendation: Use CrossEncoder Only as default.")
        print("  Consider: Fusion strategies need weight tuning on validation data.")

    output_path = Path(__file__).resolve().parent.parent / "results" / "accuracy_evaluation.csv"
    results_df.to_csv(output_path, index=False)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
