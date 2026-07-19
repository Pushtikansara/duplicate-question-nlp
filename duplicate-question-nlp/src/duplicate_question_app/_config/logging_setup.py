from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any

from duplicate_question_app._config.loader import get_config, ENV_PREFIX, get_env


_module_loggers: dict[str, logging.Logger] = {}


def configure_logging(config_dir: Path | None = None, project_root: Path | None = None) -> None:
    """Configure the root logger based on configs/logging.yaml + env overrides."""
    log_config = get_config("logging", config_dir, project_root)
    if not log_config:
        _basic_fallback()
        return

    level_name = os.environ.get(f"{ENV_PREFIX}LOG_LEVEL", log_config.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt = log_config.get("format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    datefmt = log_config.get("datefmt", "%Y-%m-%d %H:%M:%S")
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates on reconfiguration
    root_logger.handlers.clear()

    # Console handler
    console_cfg = log_config.get("console", {})
    if console_cfg.get("enabled", True):
        console_level_name = os.environ.get(
            f"{ENV_PREFIX}LOG_LEVEL",
            console_cfg.get("level", "INFO"),
        ).upper()
        console_level = getattr(logging, console_level_name, logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(console_level)
        ch.setFormatter(logging.Formatter(
            console_cfg.get("format", fmt),
            datefmt=datefmt,
        ))
        root_logger.addHandler(ch)

    # File handler
    file_cfg = log_config.get("file", {})
    if file_cfg.get("enabled", False):
        file_path = file_cfg.get("path", "logs/duplicate_question_app.log")
        if not Path(file_path).is_absolute() and project_root:
            file_path = str(project_root / file_path)
        file_level_name = file_cfg.get("level", "DEBUG")
        file_level = getattr(logging, file_level_name, logging.DEBUG)
        max_bytes = file_cfg.get("max_bytes", 10485760)
        backup_count = file_cfg.get("backup_count", 5)
        fh = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=max_bytes, backupCount=backup_count,
        )
        fh.setLevel(file_level)
        fh.setFormatter(logging.Formatter(
            file_cfg.get("format", fmt),
            datefmt=datefmt,
        ))
        root_logger.addHandler(fh)

    # Module-specific levels
    modules_cfg = log_config.get("modules", {})
    for module_name, module_level_name in modules_cfg.items():
        module_level = getattr(logging, module_level_name.upper(), logging.INFO)
        logging.getLogger(module_name).setLevel(module_level)


def _basic_fallback() -> None:
    """Basic logging config if logging.yaml is unavailable."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a module-level logger. Caches to avoid repeated lookups.

    If no logging handlers have been configured yet, sets up basic
    console logging as a fallback.
    """
    if name in _module_loggers:
        return _module_loggers[name]
    if not logging.getLogger().hasHandlers():
        _basic_fallback()
    logger = logging.getLogger(name)
    _module_loggers[name] = logger
    return logger
