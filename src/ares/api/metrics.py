from __future__ import annotations

import logging
import time
from typing import Any

from ares.api.config import APIConfig

logger = logging.getLogger(__name__)


class APIMetricsCollector:
    def __init__(self) -> None:
        self._config = APIConfig.get()
        self._prefix = self._config.metrics_prefix
        self._counters: dict[str, int] = {}
        self._latencies: dict[str, list[float]] = {}
        self._start_time = time.time()

    def increment(self, metric: str, value: int = 1) -> None:
        key = f"{self._prefix}{metric}"
        self._counters[key] = self._counters.get(key, 0) + value

    def record_latency(self, metric: str, elapsed_ms: float) -> None:
        key = f"{self._prefix}{metric}_latency_ms"
        if key not in self._latencies:
            self._latencies[key] = []
        self._latencies[key].append(elapsed_ms)
        if len(self._latencies[key]) > 1000:
            self._latencies[key] = self._latencies[key][-1000:]

    def get_metrics(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in self._counters.items():
            result[key] = value
        for key, values in self._latencies.items():
            if values:
                result[f"{key}_avg"] = sum(values) / len(values)
                result[f"{key}_min"] = min(values)
                result[f"{key}_max"] = max(values)
                result[f"{key}_count"] = len(values)
        result[f"{self._prefix}uptime_seconds"] = time.time() - self._start_time
        return result

    def reset(self) -> None:
        self._counters.clear()
        self._latencies.clear()
        self._start_time = time.time()


_metrics_collector: APIMetricsCollector | None = None


def get_metrics_collector() -> APIMetricsCollector:
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = APIMetricsCollector()
    return _metrics_collector
