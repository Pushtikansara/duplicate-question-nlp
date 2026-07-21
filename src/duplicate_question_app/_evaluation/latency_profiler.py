from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


@dataclass
class LatencySnapshot:
    module: str
    elapsed_ms: float
    timestamp: float


class LatencyProfiler:
    def __init__(self) -> None:
        self._snapshots: list[LatencySnapshot] = []
        self._start_time: float = 0.0
        self._lock = threading.Lock()

    @contextmanager
    def measure(self, module_name: str) -> Any:
        t0 = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - t0) * 1000
            with self._lock:
                self._snapshots.append(
                    LatencySnapshot(
                        module=module_name,
                        elapsed_ms=elapsed,
                        timestamp=time.time(),
                    )
                )

    def start(self) -> None:
        self._snapshots.clear()
        self._start_time = time.perf_counter()

    def snapshot(self, module_name: str) -> float:
        elapsed = (time.perf_counter() - self._start_time) * 1000
        with self._lock:
            self._snapshots.append(
                LatencySnapshot(
                    module=module_name,
                    elapsed_ms=elapsed,
                    timestamp=time.time(),
                )
            )
        return elapsed

    def get_module_latency(self, module_name: str) -> float:
        total = 0.0
        for s in self._snapshots:
            if s.module == module_name:
                total += s.elapsed_ms
        return total

    def get_total_latency(self) -> float:
        if not self._snapshots:
            return 0.0
        return sum(s.elapsed_ms for s in self._snapshots)

    def get_summary(self) -> dict[str, Any]:
        module_totals: dict[str, float] = {}
        for s in self._snapshots:
            module_totals[s.module] = module_totals.get(s.module, 0.0) + s.elapsed_ms
        return {
            "total_ms": self.get_total_latency(),
            "modules": module_totals,
            "num_snapshots": len(self._snapshots),
        }

    def clear(self) -> None:
        self._snapshots.clear()

    @property
    def snapshots(self) -> list[LatencySnapshot]:
        return list(self._snapshots)
