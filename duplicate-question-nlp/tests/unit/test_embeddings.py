from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from duplicate_question_app._models.embeddings import (
    _get_sigmoid_params,
    _get_threshold,
    _resolve_device,
    _result_dict,
)
from duplicate_question_app._config.loader import clear_config_cache


class TestEmbeddingModels:
    def test_get_sigmoid_params_e5(self):
        steepness, midpoint = _get_sigmoid_params("e5-base-v2")
        assert isinstance(steepness, float)
        assert isinstance(midpoint, float)

    def test_get_sigmoid_params_bge(self):
        steepness, midpoint = _get_sigmoid_params("bge-base-en-v1.5")
        assert isinstance(steepness, float)
        assert isinstance(midpoint, float)

    def test_get_sigmoid_params_mpnet(self):
        steepness, midpoint = _get_sigmoid_params("mpnet-base-v2")
        assert isinstance(steepness, float)
        assert isinstance(midpoint, float)

    def test_get_sigmoid_params_default(self):
        steepness, midpoint = _get_sigmoid_params("unknown-model")
        assert isinstance(steepness, float)
        assert isinstance(midpoint, float)

    def test_get_sigmoid_params_case_insensitive(self):
        s1, m1 = _get_sigmoid_params("E5-BASE-V2")
        s2, m2 = _get_sigmoid_params("e5-base-v2")
        assert s1 == s2
        assert m1 == m2

    def test_get_sigmoid_params_deberta(self):
        steepness, midpoint = _get_sigmoid_params("cross-encoder/deberta-v3-base")
        assert isinstance(steepness, float)

    def test_resolve_device_cpu(self):
        device = _resolve_device()
        assert device in ("cpu", "cuda")

    def test_resolve_device_with_env(self):
        import os
        os.environ["DQD_AUTO_DEVICE"] = "false"
        clear_config_cache()
        device = _resolve_device()
        assert device == "cpu"
        os.environ.pop("DQD_AUTO_DEVICE")
        clear_config_cache()

    def test_get_threshold_e5(self):
        threshold = _get_threshold("e5-base-v2")
        assert isinstance(threshold, float)
        assert 0 < threshold < 1

    def test_get_threshold_bge(self):
        threshold = _get_threshold("bge-base-en-v1.5")
        assert isinstance(threshold, float)
        assert 0 < threshold < 1

    def test_get_threshold_mpnet(self):
        threshold = _get_threshold("mpnet-base-v2")
        assert isinstance(threshold, float)
        assert 0 < threshold < 1

    def test_get_threshold_default(self):
        threshold = _get_threshold("unknown-model")
        assert isinstance(threshold, float)
        assert 0 < threshold < 1

    def test_result_dict_structure(self):
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

    def test_result_dict_non_duplicate(self):
        result = _result_dict(
            q1="q1", q2="q2", pred_label=0, prob_dup=0.3, prob_non=0.7,
            threshold=0.5, model_name="BGE", device="cuda", latency_ms=5.0,
        )
        assert result["predicted_label"] == 0
        assert result["prediction"] == "Non-Duplicate"
        assert result["confidence"] == 0.7

    def test_result_dict_confidence_max(self):
        r1 = _result_dict(
            q1="a", q2="b", pred_label=1, prob_dup=0.9, prob_non=0.1,
            threshold=0.5, model_name="M", device="cpu", latency_ms=0,
        )
        assert r1["confidence"] == 0.9
        r2 = _result_dict(
            q1="a", q2="b", pred_label=0, prob_dup=0.2, prob_non=0.8,
            threshold=0.5, model_name="M", device="cpu", latency_ms=0,
        )
        assert r2["confidence"] == 0.8

    def test_result_dict_all_fields_present(self):
        result = _result_dict(
            q1="a", q2="b", pred_label=1, prob_dup=0.75, prob_non=0.25,
            threshold=0.5, model_name="Test", device="cpu", latency_ms=1.0,
        )
        assert "question1" in result
        assert "question2" in result
        assert "predicted_label" in result
        assert "prediction" in result

    def test_predict_batch_imports(self):
        from duplicate_question_app._models.embeddings import predict_batch_sentence_transformer
        assert callable(predict_batch_sentence_transformer)

    def test_sigmoid_all_models_return_values(self):
        for name in ["e5-base-v2", "bge-base-en-v1.5", "mpnet-base-v2", "unknown"]:
            s, m = _get_sigmoid_params(name)
            assert isinstance(s, float)
            assert isinstance(m, float)

    def test_threshold_all_models_return_values(self):
        for name in ["e5-base-v2", "bge-base-en-v1.5", "mpnet-base-v2", "unknown"]:
            t = _get_threshold(name)
            assert isinstance(t, float)
            assert 0 < t < 1
