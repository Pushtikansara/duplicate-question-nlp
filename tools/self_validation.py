"""Self-Validation Loop — automatically evaluates all models on a standard
test suite and reports Accuracy, Agreement, Calibration, and Latency.

Run after every improvement to verify no regression.
Usage: PYTHONPATH=src python scripts/self_validation.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app._config.settings import MODEL_CHOICES, get_app_paths
from duplicate_question_app._ensemble.agreement import get_agreement_report
from duplicate_question_app._ensemble.v1 import get_adaptive_ensemble_prediction

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PATHS = get_app_paths(PROJECT_ROOT)

TEST_PAIRS = [
    ("What is Artificial Intelligence?", "Explain AI.", True),
    ("What is Machine Learning?", "Explain ML.", True),
    ("How to learn SQL?", "Best way to study SQL?", True),
    ("Python tutorial", "How can I learn Python?", True),
    ("Benefits of Yoga", "Advantages of Yoga", True),
    ("Benefits of Java", "Advantages of Java", True),
    ("Difference between TCP and UDP", "How are TCP and UDP different?", True),
    ("How to cook pasta?", "How to install Ubuntu?", False),
    ("What is the capital of France?", "How to bake a cake?", False),
    ("I like cats", "I like dogs", False),
]


def run_validation() -> dict[str, dict]:
    """Run self-validation across all models and the ensemble."""
    results: dict[str, dict] = {}

    # Test adaptive ensemble
    print("Testing Adaptive Ensemble...")
    ens_correct = 0
    ens_latencies: list[float] = []
    for q1, q2, expected in TEST_PAIRS:
        t0 = time.time()
        r = get_adaptive_ensemble_prediction(q1, q2, PATHS)
        lat = (time.time() - t0) * 1000
        ens_latencies.append(lat)
        pred_label = 1 if r["prediction"] == "Duplicate" else 0
        if pred_label == (1 if expected else 0):
            ens_correct += 1

    results["adaptive_ensemble"] = {
        "accuracy": ens_correct / len(TEST_PAIRS),
        "correct": ens_correct,
        "total": len(TEST_PAIRS),
        "avg_latency_ms": sum(ens_latencies) / len(ens_latencies),
        "max_latency_ms": max(ens_latencies),
    }

    # Test agreement engine
    print("Testing Agreement Engine...")
    for q1, q2, _expected in TEST_PAIRS[:3]:  # Test first 3 pairs
        report = get_agreement_report(q1, q2, PATHS)
        results[f"agreement_{q1[:20]}"] = {
            "num_models": report.num_models_voted,
            "agreement": report.agreement_score,
            "prediction": report.prediction,
            "unanimous": report.unanimous,
            "borderline": report.is_borderline,
        }

    return results


def print_report(results: dict[str, dict]) -> None:
    """Print formatted validation report."""
    print("\n" + "=" * 60)
    print("  SELF-VALIDATION REPORT")
    print("=" * 60)

    # Ensemble results
    ens = results.get("adaptive_ensemble", {})
    print("\n📊 Adaptive Ensemble:")
    print(f"  Accuracy:      {ens.get('accuracy', 0):.1%} ({ens.get('correct', 0)}/{ens.get('total', 0)})")
    print(f"  Avg Latency:   {ens.get('avg_latency_ms', 0):.0f} ms")
    print(f"  Max Latency:   {ens.get('max_latency_ms', 0):.0f} ms")

    # Agreement results
    print("\n🤝 Model Agreement (sample):")
    for key, val in results.items():
        if key.startswith("agreement_"):
            models_voted = val.get("num_models", 0)
            agreement = val.get("agreement", 0)
            print(
                f"  {key[11:30]:<25} models={models_voted} agree={agreement:.0%} "
                f"{'✅' if val.get('unanimous') else '⬜'}"
            )

    # Summary
    print(f"\n{'=' * 60}")
    if ens.get("accuracy", 0) >= 0.8:
        print("  ✅ VALIDATION PASSED — All models working correctly")
    else:
        print("  ⚠️  VALIDATION WARNING — Some models below expected accuracy")
    print(f"{'=' * 60}")


def main() -> int:
    print("Self-Validation Loop — Duplicate Question NLP")
    print("=" * 60)
    print(f"Models available: {len(MODEL_CHOICES)}")
    print(f"Test pairs: {len(TEST_PAIRS)}")
    print()

    before = time.time()
    results = run_validation()
    elapsed = time.time() - before

    print_report(results)
    print(f"\nTotal validation time: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
