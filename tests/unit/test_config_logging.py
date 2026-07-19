from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from duplicate_question_app._config.logging_setup import (
    _basic_fallback,
    _module_loggers,
    configure_logging,
    get_logger,
)
from duplicate_question_app._config.loader import clear_config_cache


class TestLoggingSetup:
    def setup_method(self):
        _module_loggers.clear()
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)
        root.handlers = []
        clear_config_cache()

    def test_basic_fallback_configures_root(self):
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)
        _basic_fallback()
        assert root.hasHandlers()
        assert root.level == logging.INFO

    def test_get_logger_returns_logger(self):
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_caches(self):
        l1 = get_logger("cached_test")
        l2 = get_logger("cached_test")
        assert l1 is l2

    def test_get_logger_different_names(self):
        l1 = get_logger("module_a")
        l2 = get_logger("module_b")
        assert l1 is not l2

    def test_get_logger_sets_basic_config_if_no_handlers(self):
        prev_handlers = list(_module_loggers.items())
        _module_loggers.clear()
        root = logging.getLogger()

        root.handlers.clear()
        with patch.object(root, "hasHandlers", return_value=False):
            logger = get_logger("fresh_test")
            assert logger is not None

    def test_configure_logging_from_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            log_cfg = {
                "level": "DEBUG",
                "format": "%(message)s",
                "console": {"enabled": True, "level": "DEBUG"},
            }
            for name in ["app", "paths", "models", "inference", "training", "evaluation", "dataset"]:
                with open(config_dir / f"{name}.yaml", "w") as f:
                    yaml.dump({}, f)
            with open(config_dir / "logging.yaml", "w") as f:
                yaml.dump(log_cfg, f)
            configure_logging(config_dir=config_dir)
            root = logging.getLogger()
            assert root.level == logging.DEBUG

    def test_configure_logging_empty_config_falls_back(self):
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            for name in ["app", "paths", "models", "inference", "training", "evaluation", "dataset", "logging"]:
                with open(config_dir / f"{name}.yaml", "w") as f:
                    yaml.dump({}, f)
            configure_logging(config_dir=config_dir)
            assert root.hasHandlers()

    def test_configure_logging_file_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            log_cfg = {
                "level": "INFO",
                "format": "%(message)s",
                "console": {"enabled": True, "level": "INFO"},
                "file": {
                    "enabled": True,
                    "path": str(Path(tmpdir) / "test.log"),
                    "level": "DEBUG",
                    "max_bytes": 1024,
                    "backup_count": 1,
                },
            }
            for name in ["app", "paths", "models", "inference", "training", "evaluation", "dataset"]:
                with open(config_dir / f"{name}.yaml", "w") as f:
                    yaml.dump({}, f)
            with open(config_dir / "logging.yaml", "w") as f:
                yaml.dump(log_cfg, f)
            configure_logging(config_dir=config_dir)
            root = logging.getLogger()
            handlers = root.handlers
            assert any("RotatingFileHandler" in type(h).__name__ for h in handlers)

    def test_logger_emits_at_correct_level(self, caplog):
        caplog.set_level(logging.DEBUG)
        logger = get_logger("test_emit")
        logger.info("info message")
        logger.debug("debug message")
        logger.warning("warning message")
        assert "info message" in caplog.text
        assert "debug message" in caplog.text
        assert "warning message" in caplog.text

    def test_configure_logging_module_levels(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            log_cfg = {
                "level": "INFO",
                "format": "%(message)s",
                "console": {"enabled": True, "level": "INFO"},
                "modules": {"test_specific_module": "WARNING"},
            }
            for name in ["app", "paths", "models", "inference", "training", "evaluation", "dataset"]:
                with open(config_dir / f"{name}.yaml", "w") as f:
                    yaml.dump({}, f)
            with open(config_dir / "logging.yaml", "w") as f:
                yaml.dump(log_cfg, f)
            configure_logging(config_dir=config_dir)
            module_logger = logging.getLogger("test_specific_module")
            assert module_logger.level == logging.WARNING

    def test_configure_logging_env_override(self):
        import os
        os.environ["DQD_LOG_LEVEL"] = "ERROR"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            log_cfg = {
                "level": "INFO",
                "format": "%(message)s",
                "console": {"enabled": True, "level": "INFO"},
            }
            for name in ["app", "paths", "models", "inference", "training", "evaluation", "dataset"]:
                with open(config_dir / f"{name}.yaml", "w") as f:
                    yaml.dump({}, f)
            with open(config_dir / "logging.yaml", "w") as f:
                yaml.dump(log_cfg, f)
            configure_logging(config_dir=config_dir)
            root = logging.getLogger()
            assert root.level == logging.ERROR
        os.environ.pop("DQD_LOG_LEVEL", None)
