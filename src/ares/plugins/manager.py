from __future__ import annotations

import builtins
import logging
from pathlib import Path
from typing import Any

from ares.plugins.base import Plugin
from ares.plugins.config import PluginConfig
from ares.plugins.context import PluginContext
from ares.plugins.dependency import resolve_load_order
from ares.plugins.discovery import discover_all, discover_from_folder
from ares.plugins.exceptions import (
    PluginDependencyError,
    PluginNotFoundError,
    PluginValidationError,
)
from ares.plugins.hooks import EventBus, HookEvent, HookPoint
from ares.plugins.lifecycle import activate_plugin, shutdown_plugin
from ares.plugins.loader import run_hook
from ares.plugins.metadata import PluginMetadata
from ares.plugins.registry import PluginRegistry
from ares.plugins.types import PluginStatus
from ares.plugins.validation import (
    validate_metadata,
    validate_no_duplicate_ids,
    validate_sdk_compatibility,
)


class PluginManager:
    """Central manager for the ARES plugin ecosystem.

    Handles installation, loading, lifecycle management, dependency
    resolution, and hook execution for all plugins.
    """

    def __init__(
        self,
        config: PluginConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.config = config or PluginConfig()
        self.logger = logger or logging.getLogger("ares.plugins")
        self.registry = PluginRegistry()
        self.event_bus = EventBus()
        self._context: PluginContext | None = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    def _build_context(self) -> PluginContext:
        return PluginContext(
            logger=self.logger,
            configuration=self.config,
            services={"registry": self.registry, "manager": self},
            event_bus=self.event_bus,
        )

    # ------------------------------------------------------------------
    # Discovery & Loading
    # ------------------------------------------------------------------

    def discover(self, folders: list[str | Path] | None = None) -> list[type[Plugin]]:
        """Discover plugin classes from all available sources."""
        return discover_all(folders=folders)

    def load(self, folders: list[str | Path] | None = None) -> list[Plugin]:
        """Load all discovered plugins into the registry.

        Returns plugins in dependency-resolved load order.
        """
        discovered = self.discover(folders)
        if not discovered:
            self._loaded = True
            return []

        existing_ids: set[str] = set(self.registry.list_ids())
        instances: list[Plugin] = []
        metadata_map: dict[str, PluginMetadata] = {}

        for cls in discovered:
            if not hasattr(cls, "metadata"):
                continue
            meta: PluginMetadata = cls.metadata
            try:
                validate_metadata(meta)
                validate_sdk_compatibility(meta)
                validate_no_duplicate_ids(meta.name, existing_ids)
            except PluginValidationError as exc:
                self.logger.warning("Skipping %s: %s", cls.__name__, exc)
                continue

            instance = cls()
            instance.metadata = meta
            instance.status = PluginStatus.INSTALLED
            self.registry.register(instance)
            instances.append(instance)
            existing_ids.add(meta.name)
            metadata_map[meta.name] = meta

        try:
            sorted_ids = resolve_load_order(metadata_map)
        except PluginDependencyError as exc:
            self.logger.error("Dependency resolution failed: %s", exc)
            raise

        sorted_plugins = [self.registry.get(pid) for pid in sorted_ids]
        self._context = self._build_context()

        for plugin in sorted_plugins:
            plugin.status = PluginStatus.LOADED

        self._loaded = True
        self.logger.info("Loaded %d plugin(s)", len(sorted_plugins))
        return sorted_plugins

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def activate_all(self) -> None:
        """Activate all loaded plugins."""
        if not self._context:
            self._context = self._build_context()
        for plugin in self.registry.list():
            if plugin.status in (PluginStatus.LOADED, PluginStatus.INSTALLED):
                activate_plugin(plugin, self._context)

    def shutdown_all(self) -> None:
        """Gracefully shut down all active plugins."""
        for plugin in self.registry.list():
            if plugin.status in (PluginStatus.ACTIVE, PluginStatus.INITIALIZED):
                shutdown_plugin(plugin, self._context or self._build_context())

    # ------------------------------------------------------------------
    # Single plugin operations
    # ------------------------------------------------------------------

    def install(self, plugin_class: type[Plugin]) -> Plugin:
        """Install a single plugin class."""
        meta: PluginMetadata = getattr(plugin_class, "metadata", None)  # type: ignore[assignment]
        if meta is None:
            raise PluginValidationError(f"{plugin_class.__name__} has no metadata")
        validate_metadata(meta)
        validate_sdk_compatibility(meta)
        validate_no_duplicate_ids(meta.name, set(self.registry.list_ids()))

        instance = plugin_class()
        instance.metadata = meta
        instance.status = PluginStatus.INSTALLED
        self.registry.register(instance)

        ctx = self._context or self._build_context()
        instance.context = ctx
        instance.on_install(ctx)
        return instance

    def uninstall(self, plugin_id: str) -> None:
        """Uninstall a plugin by ID."""
        plugin = self.registry.get(plugin_id)
        shutdown_plugin(plugin, self._context or self._build_context())
        self.registry.unregister(plugin_id)

    def enable(self, plugin_id: str) -> None:
        """Enable a disabled plugin."""
        plugin = self.registry.get(plugin_id)
        if plugin.status == PluginStatus.DISABLED:
            plugin.status = PluginStatus.ACTIVE

    def disable(self, plugin_id: str) -> None:
        """Disable an active plugin."""
        plugin = self.registry.get(plugin_id)
        if plugin.status == PluginStatus.ACTIVE:
            plugin.status = PluginStatus.DISABLED

    def reload(self, plugin_id: str) -> Plugin:
        """Reload a single plugin by uninstalling and re-installing."""
        self.uninstall(plugin_id)

        discovered = discover_from_folder(".")  # no-op; subclass must override
        for cls in discovered:
            if hasattr(cls, "metadata") and cls.metadata.name == plugin_id:
                return self.install(cls)
        raise PluginNotFoundError(f"Cannot reload {plugin_id!r}: not found in discovery")

    def get(self, plugin_id: str) -> Plugin:
        return self.registry.get(plugin_id)

    def list(self) -> builtins.list[Plugin]:
        return self.registry.list()

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def run_hook(
        self,
        hook_point: HookPoint,
        event_data: dict[str, Any] | None = None,
    ) -> builtins.list[HookEvent]:
        """Execute a hook across all active plugins."""
        ctx = self._context or self._build_context()
        active_plugins = [
            p for p in self.registry.list() if p.status in (PluginStatus.ACTIVE, PluginStatus.INITIALIZED)
        ]
        sorted_plugins = sorted(active_plugins, key=lambda p: p.metadata.priority)
        events: list[HookEvent] = []
        for plugin in sorted_plugins:
            event = run_hook(plugin, hook_point, ctx, event_data)
            events.append(event)
            if event.cancelled:
                break
        return events

    def run_pipeline_hooks(
        self,
        before_hook: HookPoint,
        after_hook: HookPoint,
        event_data: dict[str, Any] | None = None,
    ) -> tuple[builtins.list[HookEvent], builtins.list[HookEvent]]:
        """Run before/after pair of hooks (e.g., before/after pipeline)."""
        before = self.run_hook(before_hook, event_data)
        after = self.run_hook(after_hook, event_data)
        return before, after
