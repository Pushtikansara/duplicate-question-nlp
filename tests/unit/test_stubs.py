from __future__ import annotations


class TestCanonicalImports:
    def test_package_version(self):
        from duplicate_question_app import __version__

        assert __version__ == "0.2.0"

    def test_top_level_exports(self):
        import duplicate_question_app as dqa

        assert hasattr(dqa, "DuplicateQuestionInferenceService")
        assert hasattr(dqa, "AppPaths")
        assert hasattr(dqa, "MODEL_CHOICES")

    def test_config_canonical(self):
        from duplicate_question_app._config.settings import (
            MODEL_CHOICES,
            AppPaths,
            get_app_paths,
            get_config,
        )

        assert AppPaths is not None
        assert isinstance(MODEL_CHOICES, list)
        assert len(MODEL_CHOICES) > 0
        assert callable(get_config)
        assert callable(get_app_paths)

    def test_preprocessing_canonical(self):
        from duplicate_question_app._preprocessing import normalize_question

        assert callable(normalize_question)

    def test_week2_canonical(self):
        from duplicate_question_app._models.week2 import (
            check_week2_artifacts,
            is_week2_model,
        )

        assert callable(check_week2_artifacts)
        assert callable(is_week2_model)

    def test_embeddings_canonical(self):
        from duplicate_question_app._models.embeddings import (
            _get_sigmoid_params,
            _resolve_device,
        )

        assert callable(_get_sigmoid_params)
        assert callable(_resolve_device)

    def test_ensemble_canonical(self):
        from duplicate_question_app._ensemble.v1 import get_adaptive_ensemble_prediction

        assert callable(get_adaptive_ensemble_prediction)

    def test_inference_transformer_canonical(self):
        from duplicate_question_app._inference.transformer import (
            DuplicateQuestionInferenceService,
        )

        assert DuplicateQuestionInferenceService is not None

    def test_registry_canonical(self):
        from duplicate_question_app._models.registry import build_registry

        assert callable(build_registry)

    def test_dataset_loader_canonical(self):
        from duplicate_question_app._dataset.loader import get_quora_splits, load_quora_data

        assert callable(get_quora_splits)
        assert callable(load_quora_data)

    def test_explainability_canonical(self):
        from duplicate_question_app._explainability.trace import generate_decision_trace

        assert callable(generate_decision_trace)

    def test_evaluation_metrics_canonical(self):
        from duplicate_question_app._evaluation.metrics import generate_evaluation_report

        assert callable(generate_evaluation_report)
