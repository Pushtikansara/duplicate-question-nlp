from __future__ import annotations

import builtins
import time

from ares.plugins.base import Plugin
from ares.plugins.exceptions import PluginNotFoundError
from ares.plugins.types import PluginHealth, PluginMetric, PluginStatus


class PluginRegistry:
    """Central registry storing all loaded plugins and their runtime state."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._statuses: dict[str, PluginStatus] = {}
        self._load_times: dict[str, float] = {}
        self._metrics: dict[str, PluginMetric] = {}
        self._health: dict[str, PluginHealth] = {}

    def register(self, plugin: Plugin) -> None:
        """Register a plugin instance."""
        pid = plugin.plugin_id
        self._plugins[pid] = plugin
        self._statuses[pid] = PluginStatus.INSTALLED
        self._load_times[pid] = time.time()
        self._metrics[pid] = PluginMetric()
        self._health[pid] = PluginHealth()

    def unregister(self, plugin_id: str) -> None:
        """Remove a plugin from the registry."""
        self._plugins.pop(plugin_id, None)
        self._statuses.pop(plugin_id, None)
        self._load_times.pop(plugin_id, None)
        self._metrics.pop(plugin_id, None)
        self._health.pop(plugin_id, None)

    def get(self, plugin_id: str) -> Plugin:
        if plugin_id not in self._plugins:
            raise PluginNotFoundError(f"Plugin not found: {plugin_id!r}")
        return self._plugins[plugin_id]

    def get_status(self, plugin_id: str) -> PluginStatus:
        return self._statuses.get(plugin_id, PluginStatus.UNINSTALLED)

    def set_status(self, plugin_id: str, status: PluginStatus) -> None:
        if plugin_id in self._statuses:
            self._statuses[plugin_id] = status

    def get_metric(self, plugin_id: str) -> PluginMetric:
        return self._metrics.get(plugin_id, PluginMetric())

    def get_health(self, plugin_id: str) -> PluginHealth:
        return self._health.get(plugin_id, PluginHealth())

    def list(self) -> builtins.list[Plugin]:
        return list(self._plugins.values())

    def list_ids(self) -> builtins.list[str]:
        return list(self._plugins.keys())

    def count(self) -> int:
        return len(self._plugins)

    def has(self, plugin_id: str) -> bool:
        return plugin_id in self._plugins

    def clear(self) -> None:
        self._plugins.clear()
        self._statuses.clear()
        self._load_times.clear()
        self._metrics.clear()
        self._health.clear()
