from ares.plugins.base import Plugin
from ares.plugins.context import PluginContext
from ares.plugins.hooks import HookEvent
from ares.plugins.metadata import PluginMetadata
from ares.plugins.types import HookResult


class ReasoningTracePlugin(Plugin):
    """Captures reasoning result snapshots during pipeline execution."""

    metadata = PluginMetadata(
        name="reasoning_trace",
        author="ARES Team",
        version="1.0.0",
        description="Captures reasoning trace data for debugging",
        tags=["reasoning", "trace", "debug"],
        category="reasoning",
    )

    def before_reasoning(self, context: PluginContext, event: HookEvent) -> HookResult:
        context.runtime["reasoning_input"] = dict(event.data)
        return HookResult.CONTINUE

    def after_reasoning(self, context: PluginContext, event: HookEvent) -> HookResult:
        traces = context.metrics.get("reasoning_traces", [])
        traces.append(
            {
                "input": context.runtime.get("reasoning_input", {}),
                "output": dict(event.modified_data),
            }
        )
        context.metrics["reasoning_traces"] = traces
        return HookResult.CONTINUE


class SemanticSimilarityPlugin(Plugin):
    """Injects a semantic similarity score into pipeline state."""

    metadata = PluginMetadata(
        name="semantic_similarity",
        author="ARES Team",
        version="1.0.0",
        description="Computes and injects a semantic similarity score",
        tags=["semantic", "similarity"],
        category="semantic",
    )

    def after_semantics(self, context: PluginContext, event: HookEvent) -> HookResult:
        context.pipeline_state["semantic_similarity_score"] = 0.85
        return HookResult.CONTINUE
