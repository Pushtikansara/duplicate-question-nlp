from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any


class ModuleState(IntEnum):
    UNAVAILABLE = auto()
    AVAILABLE = auto()
    INITIALIZED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class ModuleStatus:
    name: str
    state: ModuleState = ModuleState.UNAVAILABLE
    latency_ms: float = 0.0
    error: str | None = None
    output: Any = None


class LifecycleManager:
    def __init__(self) -> None:
        self._modules: dict[str, ModuleStatus] = {}

    def register(self, name: str) -> None:
        self._modules[name] = ModuleStatus(name=name, state=ModuleState.AVAILABLE)

    def set_state(self, name: str, state: ModuleState) -> None:
        if name in self._modules:
            self._modules[name].state = state

    def set_latency(self, name: str, latency_ms: float) -> None:
        if name in self._modules:
            self._modules[name].latency_ms = latency_ms

    def set_error(self, name: str, error: str) -> None:
        if name in self._modules:
            self._modules[name].state = ModuleState.FAILED
            self._modules[name].error = error

    def set_output(self, name: str, output: Any) -> None:
        if name in self._modules:
            self._modules[name].output = output

    def get_status(self, name: str) -> ModuleStatus | None:
        return self._modules.get(name)

    def get_all_statuses(self) -> dict[str, ModuleStatus]:
        return dict(self._modules)

    def summary(self) -> dict[str, Any]:
        return {
            name: {
                "state": ms.state.name,
                "latency_ms": ms.latency_ms,
                "error": ms.error,
            }
            for name, ms in self._modules.items()
        }
