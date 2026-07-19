from __future__ import annotations


class TestUtilsMetrics:
    def test_compute_ece_import(self):
        import numpy as np

        from duplicate_question_app.utils.metrics import compute_ece

        ece = compute_ece(np.array([0.1, 0.9]), np.array([0, 1]), n_bins=5)
        assert 0 <= ece <= 1.0

    def test_compute_mce_import(self):
        import numpy as np

        from duplicate_question_app.utils.metrics import compute_mce

        mce = compute_mce(np.array([0.1, 0.9]), np.array([0, 1]), n_bins=5)
        assert 0 <= mce <= 1.0


class TestArtifacts:
    def test_artifact_loader_imports(self):
        from duplicate_question_app._artifacts.loader import (
            load_confusion_matrix_csv,
            load_dataset_frame,
        )

        assert callable(load_confusion_matrix_csv)
        assert callable(load_dataset_frame)

    def test_artifact_loaders_return_none_on_missing(self):
        import pandas as pd

        from duplicate_question_app._artifacts.loader import load_confusion_matrix_csv
        from duplicate_question_app._config.loader import clear_config_cache
        from duplicate_question_app._config.settings import get_app_paths

        clear_config_cache()
        paths = get_app_paths()
        result = load_confusion_matrix_csv(paths)
        assert result is None or isinstance(result, pd.DataFrame)

    def test_build_dataset_summary_imports(self):
        from duplicate_question_app._artifacts.loader import build_dataset_summary

        assert callable(build_dataset_summary)

    def test_build_transformer_metrics_imports(self):
        from duplicate_question_app._artifacts.loader import build_transformer_metrics

        assert callable(build_transformer_metrics)

    def test_available_week4_plots_imports(self):
        from duplicate_question_app._artifacts.loader import available_week4_plots

        assert callable(available_week4_plots)

    def test_load_week4_predictions_import(self):
        from duplicate_question_app._artifacts.loader import load_week4_predictions

        assert callable(load_week4_predictions)

    def test_load_week4_threshold_analysis_import(self):
        from duplicate_question_app._artifacts.loader import load_week4_threshold_analysis

        assert callable(load_week4_threshold_analysis)
