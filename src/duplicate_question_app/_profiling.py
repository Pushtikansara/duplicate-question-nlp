from __future__ import annotations

import functools
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class ProfileEntry:
    name: str
    total_time_ms: float = 0.0
    call_count: int = 0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    avg_time_ms: float = 0.0

    def record(self, elapsed_ms: float) -> None:
        self.total_time_ms += elapsed_ms
        self.call_count += 1
        self.min_time_ms = min(self.min_time_ms, elapsed_ms)
        self.max_time_ms = max(self.max_time_ms, elapsed_ms)
        self.avg_time_ms = self.total_time_ms / self.call_count


class Profiler:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._entries = {}
                    cls._instance._disabled = False
        return cls._instance

    def disable(self) -> None:
        self._disabled = True

    def enable(self) -> None:
        self._disabled = False

    def record(self, name: str, elapsed_ms: float) -> None:
        if self._disabled:
            return
        with self._lock:
            if name not in self._entries:
                self._entries[name] = ProfileEntry(name=name)
            self._entries[name].record(elapsed_ms)

    def get_stats(self) -> dict[str, ProfileEntry]:
        with self._lock:
            return dict(self._entries)

    def get_report(self) -> list[dict[str, Any]]:
        with self._lock:
            report = []
            for name, entry in sorted(self._entries.items()):
                report.append(
                    {
                        "name": name,
                        "total_ms": round(entry.total_time_ms, 2),
                        "call_count": entry.call_count,
                        "avg_ms": round(entry.avg_time_ms, 2),
                        "min_ms": round(entry.min_time_ms, 2) if entry.min_time_ms != float("inf") else 0,
                        "max_ms": round(entry.max_time_ms, 2),
                    }
                )
            return report

    def reset(self) -> None:
        with self._lock:
            self._entries.clear()

    def summary(self) -> str:
        report = self.get_report()
        if not report:
            return "No profiling data collected."
        lines = [
            "Profile Report:",
            "-" * 80,
            f"{'Name':<40} {'Count':>6} {'Total(ms)':>10} {'Avg(ms)':>10} {'Min(ms)':>8} {'Max(ms)':>8}",
            "-" * 80,
        ]
        for r in report:
            lines.append(
                f"{r['name']:<40} {r['call_count']:>6} {r['total_ms']:>10.1f} {r['avg_ms']:>10.2f} {r['min_ms']:>8.2f} {r['max_ms']:>8.2f}"
            )
        return "\n".join(lines)


_profiler = Profiler()


def get_profiler() -> Profiler:
    return _profiler


def profile(name: str | None = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            p = get_profiler()
            profile_name = name or func.__qualname__
            t0 = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - t0) * 1000
                p.record(profile_name, elapsed)

        return wrapper

    return decorator


class TimerContext:
    def __init__(self, name: str):
        self.name = name
        self.elapsed_ms = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
        get_profiler().record(self.name, self.elapsed_ms)
