from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ares.plugins.config import PluginConfig


@dataclass
class PluginContext:
    """Context passed to every plugin lifecycle hook.

    Exposes runtime services, configuration, and state.
    No global state is used.
    """

    logger: logging.Logger
    configuration: PluginConfig = field(default_factory=PluginConfig)
    pipeline_state: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    services: dict[str, Any] = field(default_factory=dict)
    runtime: dict[str, Any] = field(default_factory=dict)
    event_bus: Any = None
    plugin_id: str = ""
