from __future__ import annotations

import pytest


class TestCrossModule:
    @pytest.mark.integration
    def test_config_to_settings_flow(self):
        from duplicate_question_app._config.loader import get_config
        from duplicate_question_app._config.settings import get_app_paths

        cfg = get_config("app")
        assert "default_model" in cfg

        paths = get_app_paths()
        assert paths.project_root is not None

    @pytest.mark.integration
    def test_model_registry_to_settings_consistency(self):
        from duplicate_question_app._config.settings import MODEL_CHOICES
        from duplicate_question_app._models.registry import build_registry

        registry = build_registry()
        registry_names = {e.display_name for e in registry}
        assert registry_names.issubset(set(MODEL_CHOICES)), (
            f"Registry contains models not in MODEL_CHOICES: {registry_names - set(MODEL_CHOICES)}"
        )

    @pytest.mark.integration
    def test_preprocessing_to_linguistics_flow(self):
        from duplicate_question_app._linguistics.lexical import compute_lexical_penalty
        from duplicate_question_app._preprocessing.text import normalize_question

        q1 = normalize_question("How to learn Python?")
        q2 = normalize_question("How can I learn Python?")
        penalty = compute_lexical_penalty(q1, q2)
        assert hasattr(penalty, "total_penalty")
        assert isinstance(penalty.total_penalty, (int, float))

    @pytest.mark.integration
    def test_exception_propagation(self):
        from duplicate_question_app._config.exceptions import (
            ConfigurationError,
            DataError,
            DatasetNotFoundError,
            DuplicateQuestionAppError,
        )

        try:
            try:
                raise DatasetNotFoundError("inner")
            except DataError:
                raise ConfigurationError("outer") from None
        except DuplicateQuestionAppError:
            pass

    @pytest.mark.integration
    def test_logging_and_config_interaction(self):
        from duplicate_question_app._config.loader import get_config
        from duplicate_question_app._config.logging_setup import get_logger

        cfg = get_config("logging")
        logger = get_logger("integration_test")
        assert logger is not None
        assert isinstance(cfg, dict)

    @pytest.mark.integration
    def test_embeddings_to_evaluation_flow(self):
        from duplicate_question_app._evaluation.error_analysis import categorize_error
        from duplicate_question_app._models.embeddings import _result_dict

        result = _result_dict(
            q1="a",
            q2="b",
            pred_label=1,
            prob_dup=0.8,
            prob_non=0.2,
            threshold=0.5,
            model_name="E5",
            device="cpu",
            latency_ms=10,
        )
        errors = categorize_error(
            q1="a",
            q2="b",
            predicted_label=result["predicted_label"],
            true_label=result["predicted_label"],
            prob_duplicate=result["prob_duplicate"],
        )
        assert isinstance(errors, list)
        assert all(hasattr(e, "name") for e in errors)
