from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class PluginStatus(Enum):
    """Runtime status of a plugin."""

    INSTALLED = auto()
    LOADED = auto()
    INITIALIZED = auto()
    ACTIVE = auto()
    DISABLED = auto()
    ERROR = auto()
    UNINSTALLED = auto()


class PluginCapability(Enum):
    """Capability categories a plugin may declare."""

    REASONING = auto()
    MEMORY = auto()
    SEMANTIC = auto()
    REFLECTION = auto()
    PERCEPTION = auto()
    EVALUATION = auto()
    VISUALIZATION = auto()
    ROUTING = auto()
    LOGGING = auto()
    TELEMETRY = auto()
    STORAGE = auto()
    DATASET = auto()
    EXPORT = auto()
    MONITORING = auto()


class HookResult(Enum):
    """Return status from a hook execution."""

    CONTINUE = auto()
    MODIFY = auto()
    CANCEL = auto()
    EMIT = auto()


@dataclass(frozen=True)
class PluginDependency:
    """Declared dependency on another plugin."""

    plugin_id: str
    version_spec: str = "*"
    optional: bool = False


@dataclass
class PluginMetric:
    """Runtime metric snapshot for a plugin."""

    load_time_ms: float = 0.0
    total_hook_time_ms: float = 0.0
    hook_invocations: int = 0
    errors: int = 0
    memory_estimate_bytes: int = 0


@dataclass
class PluginHealth:
    """Health check result for a plugin."""

    healthy: bool = True
    last_check: float = 0.0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
