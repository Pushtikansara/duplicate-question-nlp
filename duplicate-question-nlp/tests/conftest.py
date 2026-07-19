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


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "gpu" in item.keywords:
            continue
        has_any = any(
            m in item.keywords
            for m in ("slow", "integration", "regression", "streamlit", "cli", "smoke")
        )
        if not has_any:
            item.add_marker(pytest.mark.fast)
