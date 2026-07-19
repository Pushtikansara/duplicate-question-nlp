from __future__ import annotations

import os
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

os.environ["DQD_ENV"] = "development"

import pytest

from duplicate_question_app._config.loader import clear_config_cache
from duplicate_question_app._config.logging_setup import _module_loggers
from duplicate_question_app._config.settings import get_app_paths, model_dir_has_artifacts


def _model_artifacts_available() -> bool:
    """Check whether trained model artifacts exist on disk.

    Returns True if at least one transformer model directory is complete.
    Used to skip model-dependent tests in CI where artifacts are absent.
    """
    try:
        paths = get_app_paths()
        return model_dir_has_artifacts(paths.week4_model_dir) or model_dir_has_artifacts(paths.week3_model_dir)
    except (FileNotFoundError, OSError):
        return False


@pytest.fixture(autouse=True)
def reset_config_cache():
    clear_config_cache()
    _module_loggers.clear()
    yield
    clear_config_cache()
    _module_loggers.clear()


def pytest_configure(config):
    config.addinivalue_line("markers", "fast: Quick unit tests (default)")
    config.addinivalue_line("markers", "slow: Tests that may take longer to run")
    config.addinivalue_line("markers", "gpu: Tests requiring GPU hardware")
    config.addinivalue_line("markers", "integration: Tests that cross module boundaries")
    config.addinivalue_line("markers", "smoke: Lightweight smoke/sanity checks")
    config.addinivalue_line("markers", "regression: Golden-output regression tests")
    config.addinivalue_line("markers", "streamlit: Streamlit-specific smoke tests")
    config.addinivalue_line("markers", "cli: Command-line interface tests")
    config.addinivalue_line("markers", "needs_model: Requires actual model artifacts on disk (skipped in CI)")


def pytest_collection_modifyitems(config, items):
    model_deps_available = _model_artifacts_available()
    for item in items:
        if "gpu" in item.keywords:
            continue
        has_any = any(m in item.keywords for m in ("slow", "integration", "regression", "streamlit", "cli", "smoke"))
        if not has_any:
            item.add_marker(pytest.mark.fast)

    if not model_deps_available:
        needs_model = [item for item in items if item.get_closest_marker("needs_model")]
        if needs_model:
            skip_reason = "Skipping model-dependent tests: model artifacts not found on disk"
            for item in needs_model:
                item.add_marker(pytest.mark.skip(reason=skip_reason))
