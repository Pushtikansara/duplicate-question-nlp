from __future__ import annotations

import pytest


class TestBackwardCompatStubs:
    def test_config_stub_exports_app_paths(self):
        from duplicate_question_app.config import AppPaths
        assert AppPaths is not None

    def test_config_stub_exports_model_choices(self):
        from duplicate_question_app.config import MODEL_CHOICES
        assert isinstance(MODEL_CHOICES, list)
        assert len(MODEL_CHOICES) > 0

    def test_config_stub_exports_get_config(self):
        from duplicate_question_app.config import get_config
        cfg = get_config("app")
        assert isinstance(cfg, dict)

    def test_config_stub_exports_get_env(self):
        from duplicate_question_app.config import get_env
        env = get_env()
        assert isinstance(env, str)

    def test_config_stub_exports_clear_cache(self):
        from duplicate_question_app.config import clear_config_cache
        clear_config_cache()

    def test_config_stub_exports_exceptions(self):
        from duplicate_question_app.config import DuplicateQuestionAppError, ConfigurationError
        assert issubclass(ConfigurationError, DuplicateQuestionAppError)

    def test_config_stub_exports_model_status(self):
        from duplicate_question_app.config import ModelDirectoryStatus, ModelResolution
        assert ModelDirectoryStatus is not None
        assert ModelResolution is not None

    def test_embedding_models_stub_exports(self):
        from duplicate_question_app.embedding_models import _get_sigmoid_params, _resolve_device
        assert callable(_get_sigmoid_params)
        assert callable(_resolve_device)

    def test_inference_stub_exports(self):
        from duplicate_question_app.inference import (
            DuplicateQuestionInferenceService,
            ModelMetadata,
        )
        assert DuplicateQuestionInferenceService is not None

    def test_data_loader_stub_exports(self):
        from duplicate_question_app.data_loader import get_quora_splits, load_quora_data
        assert callable(get_quora_splits)
        assert callable(load_quora_data)

    def test_preprocessing_stub_exports(self):
        from duplicate_question_app.preprocessing import normalize_question
        assert callable(normalize_question)

    def test_model_registry_stub_exports(self):
        from duplicate_question_app.model_registry import ModelRegistryEntry, build_registry
        assert callable(build_registry)

    def test_confidence_calibration_stub_exports(self):
        from duplicate_question_app.confidence_calibration import (
            calibrate_duplicate_probs,
            calibrate_model_prediction,
            temperature_scale,
            platt_scale,
        )
        assert callable(calibrate_duplicate_probs)

    def test_confidence_calibration_v2_stub_exports(self):
        from duplicate_question_app.confidence_calibration_v2 import (
            compute_brier_score,
            compute_nll,
            select_best_calibration,
            isotonic_regression,
        )
        assert callable(compute_brier_score)

    def test_intelligent_ensemble_stub_exports(self):
        from duplicate_question_app.intelligent_ensemble import (
            compute_adaptive_weights,
            get_adaptive_ensemble_prediction,
        )
        assert callable(get_adaptive_ensemble_prediction)

    def test_adaptive_ensemble_v2_stub_exports(self):
        from duplicate_question_app.adaptive_ensemble_v2 import adaptive_ensemble_predict
        assert callable(adaptive_ensemble_predict)

    def test_evaluation_stub_exports(self):
        from duplicate_question_app.evaluation import (
            EvaluationMetrics,
            generate_evaluation_report,
            compare_models,
        )
        assert callable(generate_evaluation_report)

    def test_explainability_stub_exports(self):
        from duplicate_question_app.explainability import DecisionTrace, generate_decision_trace
        assert callable(generate_decision_trace)

    def test_explainer_stub_exports(self):
        from duplicate_question_app.explainer import ExplanationResult, generate_explanation
        assert callable(generate_explanation)

    def test_error_analyzer_stub_exports(self):
        from duplicate_question_app.error_analyzer import ErrorCategory, categorize_error
        assert callable(categorize_error)

    def test_hard_negative_mining_stub_exports(self):
        from duplicate_question_app.hard_negative_mining import mine_hard_negatives_embedding
        assert callable(mine_hard_negatives_embedding)

    def test_error_logger_stub_exports(self):
        from duplicate_question_app.error_logger import (
            ErrorLogger, get_error_logger, log_prediction_error,
        )
        assert callable(get_error_logger)
        assert callable(log_prediction_error)

    def test_hard_test_generator_stub_exports(self):
        from duplicate_question_app.hard_test_generator import generate_hard_dataset
        assert callable(generate_hard_dataset)

    def test_config_module_re_exports(self):
        from duplicate_question_app._config import get_config, get_env, configure_logging, get_logger
        assert callable(get_config)
        assert callable(configure_logging)

    def test_package_version(self):
        from duplicate_question_app import __version__
        assert __version__ == "0.2.0"

    def test_top_level_exports(self):
        import duplicate_question_app as dqa
        assert hasattr(dqa, "DuplicateQuestionInferenceService")
        assert hasattr(dqa, "AppPaths")
        assert hasattr(dqa, "MODEL_CHOICES")
