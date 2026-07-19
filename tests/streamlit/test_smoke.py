from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from duplicate_question_app._config.logging_setup import get_logger


class TestStreamlitSmoke:
    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_app_module_imports(self):
        import importlib
        import app.app as app_module
        importlib.reload(app_module)
        assert app_module is not None

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_app_page_imports(self):
        from app.pages import home
        assert home is not None

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_all_app_pages_import(self):
        page_names = [
            "home", "overview", "models", "prediction", "dataset",
            "evaluation_suite", "batch_prediction", "pipeline",
            "explainability", "advanced_explainability", "error_analysis",
            "error_explorer", "error_logger", "calibration",
            "advanced_calibration", "adaptive_ensemble", "agreement_dashboard",
            "model_agreement", "model_comparison", "performance",
            "performance_optimizer", "model_manager",
            "contradiction_detection", "entity_detection", "intent_detection",
            "negation_detection", "lexical_penalty", "hard_test_generator",
        ]
        for name in page_names:
            module_name = f"app.pages.{name}"
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_app_services_import(self):
        from app.services import runtime, data, builder
        assert runtime is not None
        assert data is not None
        assert builder is not None

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_app_components_import(self):
        from app.components import footer, helpers, metric_cards, sidebar
        assert footer is not None
        assert metric_cards is not None
        assert sidebar is not None

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_app_utils_import(self):
        from app.utils import constants
        assert constants is not None

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_runtime_service_get_runtime_context(self):
        from app.services.runtime import get_runtime_context
        ctx = get_runtime_context()
        assert isinstance(ctx, tuple)
        assert len(ctx) == 3

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_runtime_service_resolve_model_selection(self):
        from app.services.runtime import resolve_model_selection
        from app.utils.constants import get_app_paths
        paths = get_app_paths()
        resolution = resolve_model_selection(paths)
        assert resolution is not None

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_data_service_imports(self):
        from app.services.data import (
            get_dataset,
            get_dataset_summary,
        )
        assert callable(get_dataset)
        assert callable(get_dataset_summary)

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_builder_service_imports(self):
        from app.services.builder import build_model_status_table, build_model_comparison_table
        assert callable(build_model_status_table)

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_session_state_keys(self):
        from app.utils.constants import get_app_paths
        paths = get_app_paths()
        assert paths is not None

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_home_page_renders_without_error(self):
        with patch("streamlit.set_page_config") as mock_config:
            with patch("streamlit.title"):
                with patch("streamlit.markdown"):
                    with patch("streamlit.columns") as mock_cols:
                        mock_cols.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
                        with patch("streamlit.metric"):
                            with patch("streamlit.checkbox", return_value=False):
                                with patch("streamlit.selectbox", return_value="E5-base-v2"):
                                    with patch("streamlit.slider", return_value=0.5):
                                        with patch("streamlit.button", return_value=False):
                                            with patch("streamlit.info"):
                                                with patch("streamlit.warning"):
                                                    with patch("streamlit.subheader"):
                                                        with patch("streamlit.dataframe"):
                                                            with patch("streamlit.json"):
                                                                from app.pages.home import render
                                                                render()

    @pytest.mark.streamlit
    @pytest.mark.smoke
    def test_app_creation_with_mock(self):
        with patch("streamlit.set_page_config"):
            with patch("streamlit.sidebar"):
                with patch("streamlit.title"):
                    with patch("streamlit.markdown"):
                        with patch("streamlit.selectbox", return_value="Home"):
                            with patch("streamlit.info"):
                                import app.app
                                assert app.app is not None
