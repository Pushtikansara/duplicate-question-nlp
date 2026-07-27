"""Model Comparison Benchmark for Phase 10.6.6.

Runs regression tests on every registered model and outputs
Accuracy, Precision, Recall, F1, Latency, Confidence.
"""

from __future__ import annotations

import time

import pytest

from ares.inference.dispatcher import InferenceDispatcher

GROUND_TRUTH = [
    ("what is ai", "what is ai", 1),
    ("what is ai", "what is artificial intelligence", 1),
    ("dbms", "database management system", 1),
    ("ml", "machine learning", 1),
    ("cnn", "convolutional neural network", 1),
    ("nlp", "natural language processing", 1),
    ("cat", "dog", 0),
    ("python list", "python tuple", 0),
    ("hello", "hello", 1),
    ("what is nlp", "natural language processing", 1),
    ("oop", "object oriented programming", 1),
    ("lstm", "long short term memory", 1),
    ("bert", "bidirectional encoder representations from transformers", 1),
    ("gpt", "generative pretrained transformer", 1),
    ("what is ai", "what is ml", 0),
]


def get_available_models() -> list[str]:
    try:
        return InferenceDispatcher.list_models()
    except Exception:
        return []


@pytest.fixture(scope="session")
def benchmark_results():
    models = get_available_models()
    if not models:
        pytest.skip("No models available")
    results = {}
    for model in models:
        tp = tn = fp = fn = 0
        latencies = []
        confidences = []
        for q1, q2, expected in GROUND_TRUTH:
            start = time.perf_counter()
            result = InferenceDispatcher.predict(model_name=model, question1=q1, question2=q2)
            latencies.append(result.latency_ms)
            confidences.append(result.confidence)
            if result.predicted_label == 1 and expected == 1:
                tp += 1
            elif result.predicted_label == 0 and expected == 0:
                tn += 1
            elif result.predicted_label == 1 and expected == 0:
                fp += 1
            elif result.predicted_label == 0 and expected == 1:
                fn += 1
        accuracy = (tp + tn) / len(GROUND_TRUTH) if GROUND_TRUTH else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        results[model] = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "avg_latency_ms": avg_latency,
            "avg_confidence": avg_confidence,
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
        }
    return results


def test_benchmark_report(benchmark_results):
    print("\n\n" + "=" * 100)
    print(
        f"{'Model':<40} {'Accuracy':>9} {'Precision':>10} {'Recall':>7} {'F1':>7} {'Latency(ms)':>12} {'Confidence':>11}"
    )
    print("=" * 100)
    for model, metrics in sorted(benchmark_results.items()):
        print(
            f"{model:<40} "
            f"{metrics['accuracy']:>9.3f} "
            f"{metrics['precision']:>10.3f} "
            f"{metrics['recall']:>7.3f} "
            f"{metrics['f1']:>7.3f} "
            f"{metrics['avg_latency_ms']:>12.1f} "
            f"{metrics['avg_confidence']:>11.3f}"
        )
    print("=" * 100)
    assert benchmark_results, "No benchmark results collected"
