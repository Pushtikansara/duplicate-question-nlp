from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricEntry:
    name: str
    value: float
    timestamp: float
    tags: dict[str, str] = field(default_factory=dict)


class MetricsRegistry:
    _instance: MetricsRegistry | None = None
    _lock: Lock = Lock()

    def __new__(cls) -> MetricsRegistry:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._entries = []
                    cls._instance._counters: dict[str, int] = {}
                    cls._instance._gauges: dict[str, float] = {}
        return cls._instance

    def increment(self, name: str, amount: int = 1, tags: dict[str, str] | None = None) -> None:
        current = self._counters.get(name, 0)
        self._counters[name] = current + amount
        self._entries.append(MetricEntry(name=name, value=float(amount), timestamp=time.time(), tags=tags or {}))

    def gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        self._gauges[name] = value
        self._entries.append(MetricEntry(name=name, value=value, timestamp=time.time(), tags=tags or {}))

    def counter(self, name: str) -> int:
        return self._counters.get(name, 0)

    def snapshot(self) -> dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "entry_count": len(self._entries),
        }

    def reset(self) -> None:
        self._entries.clear()
        self._counters.clear()
        self._gauges.clear()
