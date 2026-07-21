from __future__ import annotations

import contextlib
import inspect
from typing import Any

from ares.plugins.base import Plugin
from ares.plugins.context import PluginContext
from ares.plugins.hooks import HookEvent, HookPoint
from ares.plugins.types import PluginStatus


def install_plugin(plugin: Plugin, context: PluginContext) -> None:
    """Run the installation lifecycle for a plugin."""
    plugin.status = PluginStatus.INSTALLED
    plugin.context = context
    plugin.on_install(context)


def load_plugin(plugin: Plugin, context: PluginContext) -> None:
    """Run the load lifecycle for a plugin."""
    plugin.status = PluginStatus.LOADED
    plugin.context = context
    plugin.on_load(context)


def initialize_plugin(plugin: Plugin, context: PluginContext) -> None:
    """Run the initialization lifecycle for a plugin."""
    plugin.status = PluginStatus.INITIALIZED
    plugin.context = context
    plugin.on_initialize(context)


def activate_plugin(plugin: Plugin, context: PluginContext) -> None:
    """Activate a plugin so it receives hooks."""
    initialize_plugin(plugin, context)
    plugin.status = PluginStatus.ACTIVE


def shutdown_plugin(plugin: Plugin, context: PluginContext) -> None:
    """Shut down a plugin gracefully."""
    with contextlib.suppress(Exception):
        plugin.on_shutdown(context)
    plugin.status = PluginStatus.UNINSTALLED
    plugin.context = None


def run_lifecycle_hook(
    plugin: Plugin,
    hook_point: HookPoint,
    context: PluginContext,
    event_data: dict[str, Any] | None = None,
) -> HookEvent:
    """Run a single lifecycle hook on one plugin with error isolation."""
    method_name = hook_point.name.lower()
    method = getattr(plugin, method_name, None)
    event = HookEvent(hook_point, context, event_data)
    if method is None:
        return event
    try:
        sig = inspect.signature(method)
        param_count = len(sig.parameters)
        result = method(context) if param_count <= 1 else method(context, event)
        if result is not None and hasattr(result, "value") and result.value == "cancel":
            event.cancel()
    except Exception as exc:
        event.messages.append(f"{plugin.plugin_id}: {exc}")
    return event


def run_lifecycle_hooks(
    plugins: list[Plugin],
    hook_point: HookPoint,
    context: PluginContext,
    event_data: dict[str, Any] | None = None,
) -> list[HookEvent]:
    """Run a lifecycle hook across all plugins ordered by priority."""
    sorted_plugins = sorted(plugins, key=lambda p: p.metadata.priority)
    events: list[HookEvent] = []
    for plugin in sorted_plugins:
        if plugin.status not in (PluginStatus.ACTIVE, PluginStatus.INITIALIZED):
            continue
        event = run_lifecycle_hook(plugin, hook_point, context, event_data)
        events.append(event)
        if event.cancelled:
            break
    return events
