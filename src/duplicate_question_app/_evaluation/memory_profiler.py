from __future__ import annotations

import sys
import threading
from dataclasses import dataclass
from typing import Any


@dataclass
class MemorySnapshot:
    module: str
    bytes_used: int
    delta_bytes: int


class MemoryProfiler:
    def __init__(self) -> None:
        self._snapshots: list[MemorySnapshot] = []
        self._baseline: int = 0
        self._lock = threading.Lock()

    def start(self) -> None:
        self._snapshots.clear()
        self._baseline = self._get_current_memory()

    def snapshot(self, module_name: str) -> int:
        current = self._get_current_memory()
        delta = current - self._baseline
        with self._lock:
            self._snapshots.append(
                MemorySnapshot(
                    module=module_name,
                    bytes_used=current,
                    delta_bytes=delta,
                )
            )
        return delta

    def get_module_memory(self, module_name: str) -> int:
        for s in self._snapshots:
            if s.module == module_name:
                return s.delta_bytes
        return 0

    def get_total_memory(self) -> int:
        if not self._snapshots:
            return 0
        return sum(s.delta_bytes for s in self._snapshots)

    def get_summary(self) -> dict[str, Any]:
        module_totals: dict[str, int] = {}
        for s in self._snapshots:
            module_totals[s.module] = module_totals.get(s.module, 0) + s.delta_bytes
        return {
            "total_bytes": self.get_total_memory(),
            "modules": module_totals,
            "num_snapshots": len(self._snapshots),
        }

    def clear(self) -> None:
        self._snapshots.clear()

    @staticmethod
    def _get_current_memory() -> int:
        if hasattr(sys, "getsizeof"):
            return sys.getsizeof(object())
        return 0

    @property
    def snapshots(self) -> list[MemorySnapshot]:
        return list(self._snapshots)


def estimate_object_size(obj: Any, seen: set | None = None) -> int:
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(estimate_object_size(k, seen) + estimate_object_size(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set)):
        size += sum(estimate_object_size(i, seen) for i in obj)
    elif hasattr(obj, "__dict__"):
        size += estimate_object_size(obj.__dict__, seen)
    return size
