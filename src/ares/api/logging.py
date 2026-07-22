from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any


class JSONFormatter(logging.Formatter):
    """Structured log formatter that outputs JSON records.

    Each log entry includes timestamp, level, logger name, message, module,
    function, and line number. Exception info and extra keys (e.g.
    ``request_id``) are included when present.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        return json.dumps(log_entry)


def setup_api_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging for the ``ares`` logger hierarchy.

    Removes any existing handlers on the ``ares`` logger and attaches a
    single :class:`JSONFormatter` stream handler writing to stdout. The
    ``ares.api`` child logger is also set to the same level.

    Args:
        level: The logging level as a case-insensitive string
            (e.g. ``"DEBUG"``, ``"INFO"``, ``"WARNING"``). Defaults to
            ``"INFO"``.
    """
    root_logger = logging.getLogger("ares")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.handlers = []
    root_logger.addHandler(handler)
    logging.getLogger("ares.api").setLevel(getattr(logging, level.upper(), logging.INFO))
