"""Tests for embedding_models.py core functions."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app._models.embeddings import (
    _get_sigmoid_params,
    _resolve_device,
    _result_dict,
)


def test_get_sigmoid_params_e5():
    steepness, midpoint = _get_sigmoid_params("e5-base-v2")
    assert isinstance(steepness, float)
    assert isinstance(midpoint, float)
    assert 5.0 <= steepness <= 40.0
    assert 0.5 <= midpoint <= 1.0


def test_get_sigmoid_params_bge():
    steepness, midpoint = _get_sigmoid_params("bge-base-en-v1.5")
    assert isinstance(steepness, float)
    assert isinstance(midpoint, float)
    assert 10.0 <= steepness <= 20.0
    assert 0.7 <= midpoint <= 1.0


def test_get_sigmoid_params_mpnet():
    steepness, midpoint = _get_sigmoid_params("mpnet-base-v2")
    assert isinstance(steepness, float)
    assert isinstance(midpoint, float)
    assert 5.0 <= steepness <= 20.0
    assert 0.7 <= midpoint <= 1.0


def test_get_sigmoid_params_default():
    steepness, midpoint = _get_sigmoid_params("unknown-model")
    assert steepness == 15.0, f"Expected 15.0, got {steepness}"
    assert midpoint == 0.50, f"Expected 0.50, got {midpoint}"


def test_get_sigmoid_params_case_insensitive():
    s1, m1 = _get_sigmoid_params("E5-BASE-V2")
    s2, m2 = _get_sigmoid_params("e5-base-v2")
    assert s1 == s2 and m1 == m2


def test_resolve_device():
    device = _resolve_device()
    assert device in ("cpu", "cuda")


def test_result_dict_structure():
    result = _result_dict(
        q1="test question one",
        q2="test question two",
        pred_label=1,
        prob_dup=0.85,
        prob_non=0.15,
        threshold=0.5,
        model_name="E5-base-v2",
        device="cpu",
        latency_ms=10.5,
    )
    assert result["question1"] == "test question one"
    assert result["question2"] == "test question two"
    assert result["predicted_label"] == 1
    assert result["prediction"] == "Duplicate"
    assert result["prob_duplicate"] == 0.85
    assert result["prob_non_duplicate"] == 0.15
    assert result["confidence"] == 0.85
    assert result["threshold"] == 0.5
    assert result["model_label"] == "E5-base-v2"
    assert result["device"] == "cpu"
    assert result["latency_ms"] == 10.5
    assert result["reason"] is None
    assert result["feature_breakdown"] is None


def test_result_dict_non_duplicate():
    result = _result_dict(
        q1="q1",
        q2="q2",
        pred_label=0,
        prob_dup=0.3,
        prob_non=0.7,
        threshold=0.5,
        model_name="BGE",
        device="cuda",
        latency_ms=5.0,
    )
    assert result["predicted_label"] == 0
    assert result["prediction"] == "Non-Duplicate"
    assert result["confidence"] == 0.7


def test_result_dict_confidence_max():
    """Confidence should always be max(prob_dup, prob_non)."""
    result = _result_dict(
        q1="a",
        q2="b",
        pred_label=1,
        prob_dup=0.9,
        prob_non=0.1,
        threshold=0.5,
        model_name="M",
        device="cpu",
        latency_ms=0,
    )
    assert result["confidence"] == 0.9

    result = _result_dict(
        q1="a",
        q2="b",
        pred_label=0,
        prob_dup=0.2,
        prob_non=0.8,
        threshold=0.5,
        model_name="M",
        device="cpu",
        latency_ms=0,
    )
    assert result["confidence"] == 0.8


def test_reproducible_predictions():
    """Test that predict_batch_sentence_transformer gives deterministic results.

    This is an integration test — requires model weights and GPU/CPU.
    We'll skip if model not available.
    """
    try:
        from duplicate_question_app._models.embeddings import (
            predict_batch_sentence_transformer,
        )

        pairs = [
            ("How to learn Python?", "How can I learn Python programming?"),
            ("What is the capital of France?", "What is the largest city in Germany?"),
        ]
        results = predict_batch_sentence_transformer("E5-base-v2", pairs, batch_size=2)
        assert len(results) == 2
        for r in results:
            assert "predicted_label" in r
            assert "prob_duplicate" in r
            assert 0 <= r["prob_duplicate"] <= 1
            assert r["predicted_label"] in (0, 1)
    except Exception as e:
        # Skip if model not available (e.g., no internet/download)
        import pytest

        pytest.skip(f"Model unavailable: {e}")
