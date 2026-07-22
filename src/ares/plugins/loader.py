from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from ares.plugins.base import Plugin
from ares.plugins.config import PluginConfig
from ares.plugins.context import PluginContext
from ares.plugins.dependency import resolve_load_order
from ares.plugins.discovery import discover_all
from ares.plugins.exceptions import PluginLoadError, PluginValidationError
from ares.plugins.hooks import HookEvent, HookPoint
from ares.plugins.metadata import PluginMetadata
from ares.plugins.registry import PluginRegistry
from ares.plugins.types import HookResult, PluginStatus
from ares.plugins.validation import validate_metadata, validate_sdk_compatibility


def instantiate_plugin(plugin_class: type[Plugin], config: PluginConfig | None = None) -> Plugin:
    """Create a plugin instance from its class.

    Validates metadata and packages the instance with a default context.
    """
    if not hasattr(plugin_class, "metadata"):
        raise PluginValidationError(f"Plugin class {plugin_class.__name__} has no metadata")

    meta: PluginMetadata = plugin_class.metadata
    validate_metadata(meta)
    validate_sdk_compatibility(meta)

    instance = plugin_class()
    instance.metadata = meta
    instance.status = PluginStatus.INSTALLED
    return instance


def load_plugins(
    registry: PluginRegistry,
    folders: list[str | Path] | None = None,
    config: PluginConfig | None = None,
) -> list[Plugin]:
    """Full plugin loading pipeline: discover, validate, order, instantiate, register."""
    cfg = config or PluginConfig()
    discovered = discover_all(folders=folders)
    if not discovered:
        return []

    instances: list[Plugin] = []
    for cls in discovered:
        instance = instantiate_plugin(cls, cfg)
        try:
            registry.register(instance)
            instances.append(instance)
        except Exception as exc:
            raise PluginLoadError(f"Failed to register {cls.__name__}: {exc}") from exc

    metadata_map: dict[str, PluginMetadata] = {}
    for inst in instances:
        metadata_map[inst.plugin_id] = inst.metadata

    sorted_ids = resolve_load_order(metadata_map)
    sorted_plugins = [registry.get(pid) for pid in sorted_ids]

    for plugin in sorted_plugins:
        plugin.status = PluginStatus.LOADED

    return sorted_plugins


def run_hook(
    plugin: Plugin,
    hook_point: HookPoint,
    context: PluginContext,
    event_data: dict[str, Any] | None = None,
) -> HookEvent:
    """Execute a single hook on a single plugin with timing and error isolation."""
    import time

    method_name = hook_point.name.lower()
    method = getattr(plugin, method_name, None)
    if method is None:
        event = HookEvent(hook_point, context, event_data)
        return event

    event = HookEvent(hook_point, context, event_data)
    t0 = time.perf_counter()

    try:
        sig = inspect.signature(method)
        param_count = len(sig.parameters)
        result = method(context) if param_count <= 1 else method(context, event)
        elapsed = (time.perf_counter() - t0) * 1000
        plugin.metric.total_hook_time_ms += elapsed
        plugin.metric.hook_invocations += 1
        if result == HookResult.CANCEL:
            event.cancel()
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        plugin.metric.errors += 1
        plugin.metric.total_hook_time_ms += elapsed
        plugin.metric.hook_invocations += 1
        event.messages.append(f"Error: {exc}")

    return event


def run_hooks(
    plugins: list[Plugin],
    hook_point: HookPoint,
    context: PluginContext,
    event_data: dict[str, Any] | None = None,
) -> list[HookEvent]:
    """Execute a hook across all active plugins, ordered by priority."""
    sorted_plugins = sorted(plugins, key=lambda p: p.metadata.priority)
    events: list[HookEvent] = []
    for plugin in sorted_plugins:
        if plugin.status not in (PluginStatus.ACTIVE, PluginStatus.INITIALIZED):
            continue
        event = run_hook(plugin, hook_point, context, event_data)
        events.append(event)
        if event.cancelled:
            break
    return events
