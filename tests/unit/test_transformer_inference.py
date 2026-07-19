from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock


class TestTransformerInference:
    def test_load_model_and_tokenizer_imports(self):
        from duplicate_question_app._inference.transformer import load_model_and_tokenizer

        assert callable(load_model_and_tokenizer)

    def test_duplicate_question_inference_service_imports(self):
        from duplicate_question_app._inference.transformer import DuplicateQuestionInferenceService

        assert DuplicateQuestionInferenceService is not None

    def test_model_metadata_imports(self):
        from duplicate_question_app._inference.transformer import ModelMetadata

        assert ModelMetadata is not None

    def test_model_metadata_fields(self):
        from duplicate_question_app._inference.transformer import ModelMetadata

        meta = ModelMetadata(
            model_dir=Path("/tmp"),
            model_label="test",
            model_version="1.0",
            decision_threshold=0.5,
            threshold_source="config",
            device="cpu",
            fallback_reason=None,
            load_errors=(),
            cache_key="test_key",
        )
        assert meta.model_label == "test"
        assert meta.decision_threshold == 0.5
        assert meta.device == "cpu"

    def _make_mock_model(self):
        import torch

        mock_model = MagicMock()
        logits_tensor = MagicMock(spec=torch.Tensor)
        logits_tensor.to.return_value = logits_tensor
        mock_model.return_value.logits = logits_tensor
        mock_model.config.id2label = {0: "NON_DUPLICATE", 1: "DUPLICATE"}
        return mock_model

    def test_service_creation_and_predict_single(self):
        from duplicate_question_app._inference.transformer import DuplicateQuestionInferenceService, ModelMetadata

        mock_model = self._make_mock_model()
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
        metadata = ModelMetadata(
            model_dir=Path("/tmp"),
            model_label="T",
            model_version="1",
            decision_threshold=0.5,
            threshold_source="config",
            device="cpu",
            fallback_reason=None,
            load_errors=(),
            cache_key="k",
        )
        service = DuplicateQuestionInferenceService(model=mock_model, tokenizer=mock_tokenizer, metadata=metadata)
        result = service.predict_single("Q1", "Q2")
        assert isinstance(result, dict)

    def test_predict_single_has_expected_keys(self):
        from duplicate_question_app._inference.transformer import DuplicateQuestionInferenceService, ModelMetadata

        mock_model = self._make_mock_model()
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
        metadata = ModelMetadata(
            model_dir=Path("/tmp"),
            model_label="T",
            model_version="1",
            decision_threshold=0.5,
            threshold_source="config",
            device="cpu",
            fallback_reason=None,
            load_errors=(),
            cache_key="k",
        )
        service = DuplicateQuestionInferenceService(model=mock_model, tokenizer=mock_tokenizer, metadata=metadata)
        result = service.predict_single("Q1", "Q2")
        assert "predicted_label" in result

    def test_service_predict_batch_returns_dataframe(self):
        import pandas as pd

        from duplicate_question_app._inference.transformer import DuplicateQuestionInferenceService, ModelMetadata

        mock_model = self._make_mock_model()
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
        metadata = ModelMetadata(
            model_dir=Path("/tmp"),
            model_label="T",
            model_version="1",
            decision_threshold=0.5,
            threshold_source="config",
            device="cpu",
            fallback_reason=None,
            load_errors=(),
            cache_key="k",
        )
        service = DuplicateQuestionInferenceService(model=mock_model, tokenizer=mock_tokenizer, metadata=metadata)
        results = service.predict_batch([("Q1", "A1"), ("Q2", "A2")])
        assert isinstance(results, pd.DataFrame)

    def test_deterministic_predicted_label(self):
        from duplicate_question_app._inference.transformer import DuplicateQuestionInferenceService, ModelMetadata

        mock_model = self._make_mock_model()
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
        metadata = ModelMetadata(
            model_dir=Path("/tmp"),
            model_label="T",
            model_version="1",
            decision_threshold=0.5,
            threshold_source="config",
            device="cpu",
            fallback_reason=None,
            load_errors=(),
            cache_key="k",
        )
        service = DuplicateQuestionInferenceService(model=mock_model, tokenizer=mock_tokenizer, metadata=metadata)
        r1 = service.predict_single("Q", "A")
        r2 = service.predict_single("Q", "A")
        assert r1["predicted_label"] == r2["predicted_label"]

    def test_default_max_length_imported(self):
        from duplicate_question_app.inference import DEFAULT_MAX_LENGTH

        assert isinstance(DEFAULT_MAX_LENGTH, int)
        assert DEFAULT_MAX_LENGTH > 0

    def test_inference_stub_reexports(self):
        from duplicate_question_app._inference.transformer import DuplicateQuestionInferenceService as Inner
        from duplicate_question_app.inference import DuplicateQuestionInferenceService

        assert DuplicateQuestionInferenceService is Inner
