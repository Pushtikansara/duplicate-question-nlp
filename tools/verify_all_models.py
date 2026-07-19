"""Verification script for all models in the Duplicate Question NLP project.

Tests every model with identical sample questions and reports results.
Usage: PYTHONPATH=src python scripts/verify_all_models.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Add src to path
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app.config import (
    MODEL_CHOICES,
    get_app_paths,
)
from duplicate_question_app.week2_inference import Week2InferenceService, is_week2_model, check_week2_artifacts
from duplicate_question_app.inference import load_model_and_tokenizer, DuplicateQuestionInferenceService
from duplicate_question_app.embedding_models import (
    predict_with_sentence_transformer,
    get_ensemble_prediction,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PATHS = get_app_paths(PROJECT_ROOT)

SAMPLE_QUESTIONS = [
    ("How to learn Python?", "How can I learn Python programming?"),
    ("What is the capital of France?", "What is the largest city in France?"),
    ("How do I lose weight?", "What's the best way to lose weight fast?"),
    ("What is machine learning?", "What is artificial intelligence?"),
    ("Who is the president of the USA?", "Who is the current US president?"),
]


def verify_sentence_transformer_model(model_name: str) -> bool:
    """Test a sentence-transformer based model."""
    try:
        q1, q2 = SAMPLE_QUESTIONS[0]
        start = time.time()
        result = predict_with_sentence_transformer(model_name, q1, q2)
        elapsed = time.time() - start
        print(f"  ✅ Loaded and predicted: {result['prediction']} (conf={result['confidence']:.4f}, {elapsed*1000:.1f}ms)")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def verify_ensemble() -> bool:
    """Test the semantic ensemble."""
    try:
        q1, q2 = SAMPLE_QUESTIONS[0]
        start = time.time()
        result = get_ensemble_prediction(q1, q2, PATHS)
        elapsed = time.time() - start
        print(f"  ✅ Ensemble predicted: {result['prediction']} (conf={result['confidence']:.4f}, {elapsed*1000:.1f}ms, models={len(result.get('feature_breakdown', {}))})")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main() -> None:
    passed = 0
    failed = 0
    results: list[str] = []

    print("=" * 60)
    print("  VERIFICATION: Duplicate Question NLP Models")
    print("=" * 60)

    # === Week 2 Models ===
    print("\n📊 Week 2 Models (TF-IDF + LR/SVM)")
    print("-" * 40)
    arts = check_week2_artifacts(PATHS)
    week2_ready = all(arts.values())
    if week2_ready:
        service = Week2InferenceService(PATHS)
        for model_name in ["TF-IDF + Logistic Regression (Week 2)", "TF-IDF + Linear SVM (Week 2)"]:
            try:
                q1, q2 = SAMPLE_QUESTIONS[0]
                start = time.time()
                result = service.predict_single(q1, q2, model_name)
                elapsed = time.time() - start
                print(f"  ✅ {model_name}: {result['prediction']} (conf={result['confidence']:.4f}, {elapsed*1000:.1f}ms)")
                passed += 1
                results.append(f"{model_name}: PASS")
            except Exception as e:
                print(f"  ❌ {model_name}: {e}")
                failed += 1
                results.append(f"{model_name}: FAIL - {e}")
    else:
        print(f"  ❌ Week 2 artifacts missing: {arts}")
        failed += 1
        results.append("Week 2 models: FAIL - artifacts missing")

    # === Week 3 Model ===
    print("\n🧠 Week 3: DistilBERT")
    print("-" * 40)
    try:
        model, tokenizer, metadata = load_model_and_tokenizer(PATHS, model_version="DistilBERT (Week 3)")
        service = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)
        q1, q2 = SAMPLE_QUESTIONS[0]
        start = time.time()
        result = service.predict_single(q1, q2)
        elapsed = time.time() - start
        print(f"  ✅ DistilBERT (Week 3): {result['prediction']} (conf={result['confidence']:.4f}, {elapsed*1000:.1f}ms)")
        print(f"     Device: {metadata.device}")
        passed += 1
        results.append("DistilBERT (Week 3): PASS")
    except Exception as e:
        print(f"  ❌ DistilBERT (Week 3): {e}")
        failed += 1
        results.append(f"DistilBERT (Week 3): FAIL - {e}")

    # === Week 4 Model ===
    print("\n⚡ Week 4: Improved DistilBERT")
    print("-" * 40)
    try:
        model, tokenizer, metadata = load_model_and_tokenizer(PATHS, model_version="Improved DistilBERT (Week 4)")
        service = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)
        q1, q2 = SAMPLE_QUESTIONS[0]
        start = time.time()
        result = service.predict_single(q1, q2)
        elapsed = time.time() - start
        print(f"  ✅ Improved DistilBERT (Week 4): {result['prediction']} (conf={result['confidence']:.4f}, {elapsed*1000:.1f}ms)")
        print(f"     Device: {metadata.device}")
        passed += 1
        results.append("Improved DistilBERT (Week 4): PASS")
    except Exception as e:
        print(f"  ❌ Improved DistilBERT (Week 4): {e}")
        failed += 1
        results.append(f"Improved DistilBERT (Week 4): FAIL - {e}")

    # === Phase 2: Sentence Transformer Models ===
    print("\n🔬 Phase 2: Sentence Embedding Models")
    print("-" * 40)
    for model_name in ["BGE-base-en-v1.5", "E5-base-v2", "MPNet-base-v2"]:
        try:
            status = verify_sentence_transformer_model(model_name)
            if status:
                passed += 1
                results.append(f"{model_name}: PASS")
            else:
                failed += 1
                results.append(f"{model_name}: FAIL")
        except Exception as e:
            print(f"  ❌ {model_name}: {e}")
            failed += 1
            results.append(f"{model_name}: FAIL - {e}")

    # === DeBERTa Cross-Encoder ===
    print("\n🔄 DeBERTa-v3 Cross-Encoder")
    print("-" * 40)
    try:
        status = verify_sentence_transformer_model("DeBERTa-v3 Cross-Encoder")
        if status:
            passed += 1
            results.append("DeBERTa-v3 Cross-Encoder: PASS")
        else:
            failed += 1
            results.append("DeBERTa-v3 Cross-Encoder: FAIL")
    except Exception as e:
        print(f"  ❌ DeBERTa-v3 Cross-Encoder: {e}")
        failed += 1
        results.append(f"DeBERTa-v3 Cross-Encoder: FAIL - {e}")

    # === Semantic Ensemble ===
    print("\n🤝 Semantic Ensemble")
    print("-" * 40)
    try:
        status = verify_ensemble()
        if status:
            passed += 1
            results.append("Semantic Ensemble: PASS")
        else:
            failed += 1
            results.append("Semantic Ensemble: FAIL")
    except Exception as e:
        print(f"  ❌ Semantic Ensemble: {e}")
        failed += 1
        results.append(f"Semantic Ensemble: FAIL - {e}")

    # === Summary ===
    print("\n" + "=" * 60)
    print("  VERIFICATION SUMMARY")
    print("=" * 60)
    for r in results:
        status_sym = "✅" if "PASS" in r else "❌"
        print(f"  {status_sym} {r}")
    print()
    print(f"  Total: {passed + failed}  |  Passed: {passed}  |  Failed: {failed}")
    if failed > 0:
        print("  ⚠️  Some models failed verification!")
    else:
        print("  🎉 All models passed verification!")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
