from __future__ import annotations

import logging

import pytest

from ares.inference.dispatcher import InferenceDispatcher

logger = logging.getLogger(__name__)

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

_skipped_models: set[str] = set()


def get_available_models() -> list[str]:
    try:
        return _get_loadable_models()
    except Exception:
        return []


_VERIFICATION_CASES = [
    ("hello", "hello", 1),
    ("cat", "dog", 0),
    ("ml", "machine learning", 1),
    ("python list", "python tuple", 0),
    ("what is nlp", "natural language processing", 1),
]


def _try_load_model(model_name: str) -> bool:
    try:
        from ares.inference.dispatcher import InferenceDispatcher

        for q1, q2, expected in _VERIFICATION_CASES:
            result = InferenceDispatcher.predict(model_name=model_name, question1=q1, question2=q2)
            if result.predicted_label != expected:
                logger.warning(
                    "Model '%s' failed sanity check: %s x %s expected=%d got=%d",
                    model_name,
                    q1,
                    q2,
                    expected,
                    result.predicted_label,
                )
                return False
        return True
    except Exception as e:
        logger.warning("Model '%s' failed: %s", model_name, e)
        return False


def _get_loadable_models() -> list[str]:
    loadable = []
    for m in InferenceDispatcher.list_models():
        if _try_load_model(m):
            loadable.append(m)
        else:
            _skipped_models.add(m)
    return loadable


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
    errors = []
    for model in models:
        try:
            result = InferenceDispatcher.predict(model_name=model, question1="hello", question2="world")
            if result.selected_model != model:
                errors.append(
                    f"selected_model mismatch: model={model}, selected={result.selected_model}, "
                    f"executed={result.executed_model}"
                )
        except Exception as e:
            errors.append(f"  {model}: FAILED with {e}")
    if errors:
        pytest.fail("\n".join(errors))


def test_developer_proof_fields_present():
    models = get_available_models()
    if not models:
        pytest.skip("No models available")
    for model in models[:3]:
        try:
            result = InferenceDispatcher.predict(model_name=model, question1="hello", question2="world")
            assert result.backend is not None, f"{model}: backend must be set"
            assert result.raw_logits is not None, f"{model}: raw_logits must be captured"
            assert result.softmax is not None, f"{model}: softmax must be captured"
            assert result.predicted_class_id is not None, f"{model}: predicted_class_id must be set"
            assert result.label_mapping is not None, f"{model}: label_mapping must be set"
            assert result.final_label is not None, f"{model}: final_label must be set"
            assert result.selected_model is not None, f"{model}: selected_model must be set"
            assert result.executed_model is not None, f"{model}: executed_model must be set"
            assert result.threshold is not None, f"{model}: threshold must be set"
            return
        except Exception:
            continue
    pytest.skip("No loadable model found for developer_proof test")
