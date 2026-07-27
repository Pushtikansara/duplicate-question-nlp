"""Semantic Regression Test Suite for Phase 10.6.6.

Tests that the InferenceDispatcher correctly classifies semantic duplicates
across all registered models.
"""

from __future__ import annotations

import pytest

from ares.inference.dispatcher import InferenceDispatcher

SEMANTIC_REGRESSION_CASES = [
    ("what is ai", "what is ai", 1, "Duplicate", "identical text"),
    ("what is ai", "what is artificial intelligence", 1, "Duplicate", "abbreviation expansion"),
    ("dbms", "database management system", 1, "Duplicate", "abbreviation expansion"),
    ("ml", "machine learning", 1, "Duplicate", "abbreviation expansion"),
    ("cnn", "convolutional neural network", 1, "Duplicate", "abbreviation expansion"),
    ("nlp", "natural language processing", 1, "Duplicate", "abbreviation expansion"),
    ("cat", "dog", 0, "Non-Duplicate", "different concepts"),
    ("python list", "python tuple", 0, "Non-Duplicate", "different python types"),
    ("hello", "hello", 1, "Duplicate", "identical text"),
    ("what is ai", "what is ml", 0, "Non-Duplicate", "different topics"),
    ("what is nlp", "natural language processing", 1, "Duplicate", "abbreviation vs full form"),
    ("oop", "object oriented programming", 1, "Duplicate", "abbreviation expansion"),
    ("lstm", "long short term memory", 1, "Duplicate", "abbreviation expansion"),
    ("bert", "bidirectional encoder representations from transformers", 1, "Duplicate", "abbreviation expansion"),
    ("gpt", "generative pretrained transformer", 1, "Duplicate", "abbreviation expansion"),
]


def get_available_models() -> list[str]:
    try:
        return InferenceDispatcher.list_models()
    except Exception:
        return []


@pytest.mark.parametrize("q1,q2,expected_label,expected_prediction,desc", SEMANTIC_REGRESSION_CASES)
def test_semantic_regression_on_all_models(q1, q2, expected_label, expected_prediction, desc):
    models = get_available_models()
    if not models:
        pytest.skip("No models available for testing")
    errors = []
    for model in models:
        try:
            result = InferenceDispatcher.predict(model_name=model, question1=q1, question2=q2)
            if result.predicted_label != expected_label or result.prediction != expected_prediction:
                errors.append(
                    f"  {model}: got '{result.prediction}' (label={result.predicted_label}, "
                    f"conf={result.confidence:.3f}), expected '{expected_prediction}' (label={expected_label})"
                )
        except Exception as e:
            errors.append(f"  {model}: FAILED with {e}")
    if errors:
        msg = f"\nFAILURES for case '{q1}' x '{q2}' ({desc}):\n" + "\n".join(errors)
        pytest.fail(msg)


def test_selected_model_equals_executed_model():
    models = get_available_models()
    if not models:
        pytest.skip("No models available")
    for model in models:
        result = InferenceDispatcher.predict(model_name=model, question1="hello", question2="world")
        assert result.selected_model == model, (
            f"selected_model mismatch: selected={result.selected_model}, executed={result.executed_model}"
        )


def test_developer_proof_fields_present():
    models = get_available_models()
    if not models:
        pytest.skip("No models available")
    result = InferenceDispatcher.predict(model_name=models[0], question1="hello", question2="world")
    assert result.backend is not None, "backend must be set"
    assert result.raw_logits is not None, "raw_logits must be captured"
    assert result.softmax is not None, "softmax must be captured"
    assert result.predicted_class_id is not None, "predicted_class_id must be set"
    assert result.label_mapping is not None, "label_mapping must be set"
    assert result.final_label is not None, "final_label must be set"
    assert result.selected_model is not None, "selected_model must be set"
    assert result.executed_model is not None, "executed_model must be set"
    assert result.threshold is not None, "threshold must be set"
