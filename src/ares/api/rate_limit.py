from __future__ import annotations

import logging
import time
from collections import defaultdict
from threading import Lock
from typing import Any

from ares.api.config import APIConfig
from ares.api.exceptions import RateLimitError

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self) -> None:
        self._config = APIConfig.get()
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()
        self._max_requests = self._config.rate_limit_requests
        self._window_seconds = self._config.rate_limit_window_seconds
        self._burst = self._config.rate_limit_burst

    def check(self, key: str) -> dict[str, Any]:
        if not self._config.rate_limit_enabled:
            return {"allowed": True, "remaining": self._max_requests, "reset": int(time.time()) + self._window_seconds}
        now = time.time()
        with self._lock:
            window_start = now - self._window_seconds
            self._windows[key] = [t for t in self._windows[key] if t > window_start]
            current_count = len(self._windows[key])
            if current_count >= self._burst:
                reset_time = int(self._windows[key][0] + self._window_seconds)
                raise RateLimitError(detail=f"Rate limit exceeded. Retry after {reset_time - int(now)} seconds")
            self._windows[key].append(now)
            remaining = max(0, self._max_requests - current_count - 1)
            return {
                "allowed": True,
                "remaining": remaining,
                "reset": int(now) + self._window_seconds,
            }

    def get_remaining(self, key: str) -> int:
        now = time.time()
        with self._lock:
            window_start = now - self._window_seconds
            self._windows[key] = [t for t in self._windows[key] if t > window_start]
            return max(0, self._max_requests - len(self._windows[key]))
