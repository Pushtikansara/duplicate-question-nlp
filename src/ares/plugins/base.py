from __future__ import annotations

from typing import Any

from ares.plugins.context import PluginContext
from ares.plugins.hooks import HookEvent, HookPoint
from ares.plugins.metadata import PluginMetadata
from ares.plugins.types import HookResult, PluginHealth, PluginMetric, PluginStatus


class Plugin:
    """Abstract base class for all ARES plugins.

    Subclass this to create a plugin. Override the desired lifecycle hook
    methods. Every hook receives a ``PluginContext`` and returns a ``HookResult``.
    """

    metadata: PluginMetadata
    context: PluginContext | None = None
    status: PluginStatus = PluginStatus.INSTALLED
    metric: PluginMetric
    health: PluginHealth

    def __init__(self) -> None:
        self.metric = PluginMetric()
        self.health = PluginHealth()

    @property
    def plugin_id(self) -> str:
        return self.metadata.name

    @property
    def version(self) -> str:
        return self.metadata.version

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def on_install(self, context: PluginContext) -> HookResult:
        """Called once when the plugin is first installed."""
        return HookResult.CONTINUE

    def on_load(self, context: PluginContext) -> HookResult:
        """Called when the plugin is loaded into memory."""
        return HookResult.CONTINUE

    def on_initialize(self, context: PluginContext) -> HookResult:
        """Called after all plugins are loaded to perform initialisation."""
        return HookResult.CONTINUE

    def before_pipeline(self, context: PluginContext, event: HookEvent) -> HookResult:
        """Called before the cognitive pipeline runs."""
        return HookResult.CONTINUE

    def after_pipeline(self, context: PluginContext, event: HookEvent) -> HookResult:
        """Called after the cognitive pipeline completes."""
        return HookResult.CONTINUE

    def before_perception(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def after_perception(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def before_semantics(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def after_semantics(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def before_memory(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def after_memory(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def before_reasoning(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def after_reasoning(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def before_reflection(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def after_reflection(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def before_output(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def after_output(self, context: PluginContext, event: HookEvent) -> HookResult:
        return HookResult.CONTINUE

    def on_shutdown(self, context: PluginContext) -> HookResult:
        """Called when the system is shutting down."""
        return HookResult.CONTINUE

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_hook_handlers(self) -> dict[HookPoint, HookResult]:
        """Return a mapping of hook points this plugin overrides."""
        handlers: dict[HookPoint, HookResult] = {}
        for hp in HookPoint:
            method_name = hp.name.lower()
            method = getattr(self, method_name, None)
            if method is None:
                continue
            impl_class = getattr(method, "__self__", None)
            if impl_class is self:
                handlers[hp] = HookResult.CONTINUE
        return handlers

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "version": self.version,
            "status": self.status.name,
            "healthy": self.health.healthy,
            "metadata": self.metadata.__dict__ if hasattr(self.metadata, "__dict__") else {},
        }

    def __repr__(self) -> str:
        return f"<Plugin {self.plugin_id!r} v{self.version} [{self.status.name}]>"
