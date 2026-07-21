from ares.plugins.base import Plugin
from ares.plugins.context import PluginContext
from ares.plugins.hooks import HookEvent
from ares.plugins.metadata import PluginMetadata
from ares.plugins.types import HookResult


class HelloWorldPlugin(Plugin):
    """Minimal plugin that logs a greeting on load and initialize."""

    metadata = PluginMetadata(
        name="hello_world",
        author="ARES Team",
        version="1.0.0",
        description="Demonstration plugin that logs hello world messages",
        tags=["example", "demo"],
        category="example",
    )

    def on_load(self, context: PluginContext) -> HookResult:
        context.logger.info("Hello from HelloWorldPlugin!")
        return HookResult.CONTINUE

    def on_initialize(self, context: PluginContext) -> HookResult:
        context.logger.info("HelloWorldPlugin initialized")
        return HookResult.CONTINUE


class LoggerPlugin(Plugin):
    """Logs every pipeline stage for debugging."""

    metadata = PluginMetadata(
        name="logger",
        author="ARES Team",
        version="1.0.0",
        description="Logs every pipeline stage event",
        tags=["logging", "debug"],
        category="logging",
        capabilities=[],
    )

    def _log(self, context: PluginContext, event: HookEvent, stage: str) -> HookResult:
        context.logger.debug("[%s] stage=%s data=%s", self.plugin_id, stage, event.data)
        return HookResult.CONTINUE

    def before_pipeline(self, context: PluginContext, event: HookEvent) -> HookResult:
        return self._log(context, event, "before_pipeline")

    def after_pipeline(self, context: PluginContext, event: HookEvent) -> HookResult:
        return self._log(context, event, "after_pipeline")

    def before_perception(self, context: PluginContext, event: HookEvent) -> HookResult:
        return self._log(context, event, "before_perception")

    def after_perception(self, context: PluginContext, event: HookEvent) -> HookResult:
        return self._log(context, event, "after_perception")

    def before_reasoning(self, context: PluginContext, event: HookEvent) -> HookResult:
        return self._log(context, event, "before_reasoning")

    def after_reasoning(self, context: PluginContext, event: HookEvent) -> HookResult:
        return self._log(context, event, "after_reasoning")


class MetricsPlugin(Plugin):
    """Exposes runtime metrics through the context."""

    metadata = PluginMetadata(
        name="metrics",
        author="ARES Team",
        version="1.0.0",
        description="Collects and exposes runtime metrics",
        tags=["metrics", "telemetry"],
        category="telemetry",
    )

    def after_pipeline(self, context: PluginContext, event: HookEvent) -> HookResult:
        hook_count = context.metrics.get("hook_count", 0) + 1
        context.metrics["hook_count"] = hook_count
        return HookResult.CONTINUE


class TimingPlugin(Plugin):
    """Measures execution time for each pipeline stage."""

    metadata = PluginMetadata(
        name="timing",
        author="ARES Team",
        version="1.0.0",
        description="Measures and records execution times per stage",
        tags=["timing", "profiling"],
        category="monitoring",
    )

    def __init__(self) -> None:
        super().__init__()
        self._timings: dict[str, float] = {}

    def before_pipeline(self, context: PluginContext, event: HookEvent) -> HookResult:
        import time

        context.runtime["pipeline_start"] = time.perf_counter()
        return HookResult.CONTINUE

    def after_pipeline(self, context: PluginContext, event: HookEvent) -> HookResult:
        import time

        start = context.runtime.pop("pipeline_start", None)
        if start is not None:
            elapsed = (time.perf_counter() - start) * 1000
            context.metrics["pipeline_total_ms"] = elapsed
        return HookResult.CONTINUE


class MemoryStatisticsPlugin(Plugin):
    """Exposes memory usage statistics after each pipeline run."""

    metadata = PluginMetadata(
        name="memory_statistics",
        author="ARES Team",
        version="1.0.0",
        description="Records memory statistics after pipeline execution",
        tags=["memory", "statistics"],
        category="memory",
    )

    def after_pipeline(self, context: PluginContext, event: HookEvent) -> HookResult:
        import sys

        context.metrics["memory_samples"] = context.metrics.get("memory_samples", [])
        context.metrics["memory_samples"].append(sys.getsizeof(event.data))
        return HookResult.CONTINUE
