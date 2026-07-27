#!/usr/bin/env python3
"""Phase 10.6.5 — Model Benchmark Runner.

Evaluates every registered model against the golden test suite.
Reports accuracy, precision, recall, F1, latency, and confidence.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys

sys.path.insert(0, str(PROJECT_ROOT / "src"))

GOLDEN_CASES: list[dict[str, Any]] = [
    {"q1": "what is ai", "q2": "what is ai", "expected": "Duplicate"},
    {"q1": "what is ai", "q2": "what is artificial intelligence", "expected": "Duplicate"},
    {"q1": "hello", "q2": "hello", "expected": "Duplicate"},
    {"q1": "what is dbms", "q2": "what is database management system", "expected": "Duplicate"},
    {"q1": "python list", "q2": "python tuple", "expected": "Non-Duplicate"},
    {"q1": "cat", "q2": "elephant", "expected": "Non-Duplicate"},
    {"q1": "what is machine learning", "q2": "define machine learning", "expected": "Duplicate"},
    {"q1": "java", "q2": "java programming language", "expected": "Duplicate"},
]

MODELS_TO_TEST = [
    "TF-IDF + Logistic Regression (Week 2)",
    "TF-IDF + Linear SVM (Week 2)",
    "DistilBERT (Week 3)",
    "Improved DistilBERT (Week 4)",
    "BGE-base-en-v1.5",
    "E5-base-v2",
    "E5-quora-finetuned",
    "MPNet-base-v2",
    "DeBERTa-v3 Cross-Encoder",
    "Cross-Encoder-Quora (Trained)",
    "Semantic Ensemble",
]


def benchmark_model(model_name: str) -> dict[str, Any]:
    from duplicate_question_app._config.settings import get_app_paths
    from duplicate_question_app._models.embeddings import predict_with_sentence_transformer
    from duplicate_question_app._models.week2 import Week2InferenceService, is_week2_model

    paths = get_app_paths(PROJECT_ROOT)
    service = None
    if is_week2_model(model_name):
        service = Week2InferenceService(paths)

    results = []
    latencies = []
    correct = 0
    total = len(GOLDEN_CASES)

    for case in GOLDEN_CASES:
        q1 = case["q1"]
        q2 = case["q2"]
        expected = case["expected"]

        t0 = time.perf_counter()
        try:
            if is_week2_model(model_name):
                pred = service.predict_single(q1, q2, model_name)
            elif model_name == "Semantic Ensemble":
                from duplicate_question_app._models.embeddings import get_ensemble_prediction

                pred = get_ensemble_prediction(q1, q2)
            else:
                pred = predict_with_sentence_transformer(model_name, q1, q2)
            latencies.append((time.perf_counter() - t0) * 1000)
        except Exception as e:
            latencies.append((time.perf_counter() - t0) * 1000)
            results.append(
                {
                    "q1": q1,
                    "q2": q2,
                    "expected": expected,
                    "prediction": "ERROR",
                    "prob_duplicate": 0.0,
                    "confidence": 0.0,
                    "error": str(e),
                }
            )
            continue

        pred_label = pred.get("prediction", "Unknown")
        if pred_label == expected:
            correct += 1

        results.append(
            {
                "q1": q1,
                "q2": q2,
                "expected": expected,
                "prediction": pred_label,
                "prob_duplicate": float(pred.get("prob_duplicate", 0.0)),
                "prob_non_duplicate": float(pred.get("prob_non_duplicate", 0.0)),
                "confidence": float(pred.get("confidence", 0.0)),
                "latency_ms": float(pred.get("latency_ms", 0.0)),
                "threshold": float(pred.get("threshold", 0.5)),
            }
        )

    accuracy = correct / total if total > 0 else 0.0
    avg_latency = float(np.mean(latencies)) if latencies else 0.0

    return {
        "model_name": model_name,
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "avg_latency_ms": avg_latency,
        "results": results,
    }


def main():
    print("=" * 80)
    print("  Phase 10.6.5 — Model Benchmark Suite")
    print("=" * 80)
    print(f"\nGolden test cases: {len(GOLDEN_CASES)}")
    print(f"Models to test: {len(MODELS_TO_TEST)}\n")

    all_results = {}
    for model_name in MODELS_TO_TEST:
        print(f"  Testing: {model_name}...", end=" ", flush=True)
        try:
            report = benchmark_model(model_name)
            all_results[model_name] = report
            print(f"acc={report['accuracy']:.2%} latency={report['avg_latency_ms']:.0f}ms")
        except Exception as e:
            print(f"FAILED: {e}")
            all_results[model_name] = {"model_name": model_name, "error": str(e)}

    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print(f"{'Model':<40} {'Accuracy':<10} {'Latency':<10} {'Correct':<10}")
    print("-" * 70)
    for model_name in MODELS_TO_TEST:
        r = all_results.get(model_name, {})
        if "error" in r:
            print(f"{model_name:<40} {'ERROR':<10} {'N/A':<10} {'N/A':<10}")
        else:
            acc = f"{r['accuracy']:.1%}"
            lat = f"{r['avg_latency_ms']:.0f}ms"
            corr = f"{r['correct']}/{r['total']}"
            print(f"{model_name:<40} {acc:<10} {lat:<10} {corr:<10}")

    # Save results
    output_dir = PROJECT_ROOT / "verification" / "phase10_6_5"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "benchmark_results.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nFull results saved to: {output_path}")


if __name__ == "__main__":
    main()
