from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any

from duplicate_question_app._config.loader import ENV_PREFIX, get_config

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
    logging.Formatter(fmt, datefmt=datefmt)

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

        # Allow JSON format
        console_format = console_cfg.get("format", fmt)
        if console_cfg.get("json", False):
            ch.setFormatter(_JsonFormatter(console_format, datefmt=datefmt))
        else:
            ch.setFormatter(
                logging.Formatter(
                    console_format,
                    datefmt=datefmt,
                )
            )
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
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        fh.setLevel(file_level)

        # Allow JSON format for file handler too
        file_format = file_cfg.get("format", fmt)
        if file_cfg.get("json", False):
            fh.setFormatter(_JsonFormatter(file_format, datefmt=datefmt))
        else:
            fh.setFormatter(
                logging.Formatter(
                    file_format,
                    datefmt=datefmt,
                )
            )
        root_logger.addHandler(fh)

    # Module-specific levels
    modules_cfg = log_config.get("modules", {})
    for module_name, module_level_name in modules_cfg.items():
        module_level = getattr(logging, module_level_name.upper(), logging.INFO)
        logging.getLogger(module_name).setLevel(module_level)


class _JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logging.

    Produces machine-parseable JSON log lines:
    {"timestamp": "...", "level": "INFO", "logger": "...", "message": "...", ...}

    Enable in configs/logging.yaml by setting `json: true` on a handler.
    """

    def __init__(self, fmt: str, datefmt: str | None = None):
        super().__init__(fmt, datefmt=datefmt)
        self._fmt = fmt

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }
        if hasattr(record, "context") and record.context:
            log_entry["context"] = record.context
        return json.dumps(log_entry, default=str)


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
