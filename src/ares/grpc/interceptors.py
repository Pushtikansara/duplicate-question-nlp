from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class LoggingInterceptor:
    def __init__(self, service: Any) -> None:
        self._service = service

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._service, name)
        if callable(attr):

            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.time()
                try:
                    result = attr(*args, **kwargs)
                    elapsed = (time.time() - start) * 1000
                    logger.debug("gRPC call %s completed in %.2fms", name, elapsed)
                    return result
                except Exception as e:
                    elapsed = (time.time() - start) * 1000
                    logger.error("gRPC call %s failed after %.2fms: %s", name, elapsed, e)
                    raise

            return wrapper
        return attr
