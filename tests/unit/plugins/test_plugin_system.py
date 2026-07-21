from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import pytest

from ares.plugins import (
    EventBus,
    HookEvent,
    HookPoint,
    HookResult,
    Plugin,
    PluginCapability,
    PluginConfig,
    PluginContext,
    PluginDependency,
    PluginManager,
    PluginMetadata,
    PluginRegistry,
    PluginStatus,
)
from ares.plugins.dependency import build_dependency_graph, resolve_load_order, topological_sort
from ares.plugins.examples import HelloWorldPlugin, LoggerPlugin, MetricsPlugin, TimingPlugin
from ares.plugins.examples.advanced import ReasoningTracePlugin, SemanticSimilarityPlugin
from ares.plugins.exceptions import (
    PluginCycleError,
    PluginDependencyError,
    PluginError,
    PluginNotFoundError,
    PluginValidationError,
)
from ares.plugins.loader import instantiate_plugin, run_hook
from ares.plugins.validation import detect_cycles, validate_dependencies, validate_metadata, validate_no_duplicate_ids

# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def logger() -> logging.Logger:
    return logging.getLogger("test_plugins")


@pytest.fixture
def config() -> PluginConfig:
    return PluginConfig({"enabled": True})


@pytest.fixture
def context(logger: logging.Logger, config: PluginConfig) -> PluginContext:
    return PluginContext(logger=logger, configuration=config)


@pytest.fixture
def registry() -> PluginRegistry:
    return PluginRegistry()


@pytest.fixture
def manager(logger: logging.Logger, config: PluginConfig) -> PluginManager:
    return PluginManager(config=config, logger=logger)


# =========================================================================
# PluginMetadata
# =========================================================================


class TestPluginMetadata:
    def test_valid_metadata(self) -> None:
        meta = PluginMetadata(name="test", author="me", version="1.0.0")
        meta.validate()

    def test_missing_name(self) -> None:
        with pytest.raises(PluginValidationError):
            PluginMetadata(name="", author="me", version="1.0.0").validate()

    def test_missing_author(self) -> None:
        with pytest.raises(PluginValidationError):
            PluginMetadata(name="test", author="", version="1.0.0").validate()

    def test_missing_version(self) -> None:
        with pytest.raises(PluginValidationError):
            PluginMetadata(name="test", author="me", version="").validate()

    def test_invalid_name_chars(self) -> None:
        with pytest.raises(PluginValidationError):
            PluginMetadata(name="test plugin!", author="me", version="1.0.0").validate()

    def test_capabilities(self) -> None:
        meta = PluginMetadata(
            name="test",
            author="me",
            version="1.0.0",
            capabilities=[PluginCapability.REASONING, PluginCapability.MEMORY],
        )
        assert PluginCapability.REASONING in meta.capabilities
        assert PluginCapability.MEMORY in meta.capabilities


# =========================================================================
# PluginContext
# =========================================================================


class TestPluginContext:
    def test_default_context(self) -> None:
        ctx = PluginContext(logger=logging.getLogger("test"))
        assert ctx.logger is not None
        assert isinstance(ctx.configuration, PluginConfig)
        assert ctx.pipeline_state == {}
        assert ctx.metrics == {}

    def test_context_with_services(self) -> None:
        ctx = PluginContext(logger=logging.getLogger("test"), services={"db": "mock"})
        assert ctx.services["db"] == "mock"


# =========================================================================
# PluginConfig
# =========================================================================


class TestPluginConfig:
    def test_from_dict(self) -> None:
        cfg = PluginConfig.from_dict({"key": "val"})
        assert cfg.get("key") == "val"

    def test_from_json(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"a": 1}')
            p = f.name
        try:
            cfg = PluginConfig.from_json(p)
            assert cfg.get("a") == 1
        finally:
            Path(p).unlink()

    def test_from_json_not_found(self) -> None:
        with pytest.raises(PluginError):
            PluginConfig.from_json("/nonexistent/config.json")

    def test_merge(self) -> None:
        a = PluginConfig({"x": 1, "y": 2})
        b = PluginConfig({"y": 3, "z": 4})
        merged = a.merge(b)
        assert merged.get("x") == 1
        assert merged.get("y") == 3
        assert merged.get("z") == 4

    def test_to_dict(self) -> None:
        cfg = PluginConfig({"a": 1})
        assert cfg.to_dict() == {"a": 1}

    def test_contains(self) -> None:
        cfg = PluginConfig({"a": 1})
        assert "a" in cfg
        assert "b" not in cfg


# =========================================================================
# PluginRegistry
# =========================================================================


class TestPluginRegistry:
    def test_register_and_get(self, registry: PluginRegistry) -> None:
        plugin = HelloWorldPlugin()
        registry.register(plugin)
        assert registry.get("hello_world") is plugin
        assert registry.count() == 1

    def test_get_not_found(self, registry: PluginRegistry) -> None:
        with pytest.raises(PluginNotFoundError):
            registry.get("nonexistent")

    def test_unregister(self, registry: PluginRegistry) -> None:
        plugin = HelloWorldPlugin()
        registry.register(plugin)
        registry.unregister("hello_world")
        assert registry.count() == 0

    def test_list(self, registry: PluginRegistry) -> None:
        registry.register(HelloWorldPlugin())
        assert len(registry.list()) == 1

    def test_has(self, registry: PluginRegistry) -> None:
        registry.register(HelloWorldPlugin())
        assert registry.has("hello_world")
        assert not registry.has("nonexistent")

    def test_clear(self, registry: PluginRegistry) -> None:
        registry.register(HelloWorldPlugin())
        registry.clear()
        assert registry.count() == 0

    def test_status(self, registry: PluginRegistry) -> None:
        plugin = HelloWorldPlugin()
        registry.register(plugin)
        assert registry.get_status("hello_world") == PluginStatus.INSTALLED
        registry.set_status("hello_world", PluginStatus.ACTIVE)
        assert registry.get_status("hello_world") == PluginStatus.ACTIVE

    def test_list_ids(self, registry: PluginRegistry) -> None:
        registry.register(HelloWorldPlugin())
        assert "hello_world" in registry.list_ids()


# =========================================================================
# EventBus
# =========================================================================


class TestEventBus:
    def test_subscribe_and_emit(self) -> None:
        bus = EventBus()
        results: list[str] = []

        def handler(msg: str) -> None:
            results.append(msg)

        bus.subscribe("test", handler)
        import asyncio

        asyncio.run(bus.emit("test", msg="hello"))
        assert "hello" in results

    def test_unsubscribe(self) -> None:
        bus = EventBus()
        results: list[int] = []

        def handler(val: int) -> None:
            results.append(val)

        bus.subscribe("nums", handler)
        bus.unsubscribe("nums", handler)
        import asyncio

        asyncio.run(bus.emit("nums", val=42))
        assert results == []


# =========================================================================
# Hook execution
# =========================================================================


class TestHookExecution:
    def test_hook_event_created(self, context: PluginContext) -> None:
        event = HookEvent(HookPoint.BEFORE_PIPELINE, context, {"key": "val"})
        assert event.hook_point == HookPoint.BEFORE_PIPELINE
        assert event.data["key"] == "val"

    def test_hook_cancel(self, context: PluginContext) -> None:
        event = HookEvent(HookPoint.BEFORE_PIPELINE, context)
        event.cancel("not ready")
        assert event.cancelled
        assert "not ready" in event.messages

    def test_run_hook_continue(self, context: PluginContext) -> None:
        plugin = HelloWorldPlugin()
        plugin.metadata = PluginMetadata(name="test", author="me", version="1.0.0")
        event = run_hook(plugin, HookPoint.ON_LOAD, context)
        assert not event.cancelled

    def test_run_hook_cancel(self, context: PluginContext) -> None:
        class CancelPlugin(Plugin):
            metadata = PluginMetadata(name="cancel_test", author="me", version="1.0.0")

            def before_pipeline(self, ctx: PluginContext, event: HookEvent) -> HookResult:
                event.cancel("cancelled")
                return HookResult.CANCEL

        plugin = CancelPlugin()
        plugin.metadata = CancelPlugin.metadata
        plugin.status = PluginStatus.ACTIVE
        event = run_hook(plugin, HookPoint.BEFORE_PIPELINE, context)
        assert event.cancelled

    def test_hook_error_isolation(self, context: PluginContext) -> None:
        class ErrorPlugin(Plugin):
            metadata = PluginMetadata(name="error_test", author="me", version="1.0.0")

            def on_load(self, ctx: PluginContext) -> HookResult:
                raise RuntimeError("oops")

        plugin = ErrorPlugin()
        plugin.metadata = ErrorPlugin.metadata
        event = run_hook(plugin, HookPoint.ON_LOAD, context)
        assert len(event.messages) > 0
        assert plugin.metric.errors == 1


# =========================================================================
# Dependency graph
# =========================================================================


class TestDependencyGraph:
    def test_simple_graph(self) -> None:
        meta_a = PluginMetadata(name="a", author="me", version="1.0.0")
        meta_b = PluginMetadata(name="b", author="me", version="1.0.0", dependencies=[PluginDependency("a")])
        graph = build_dependency_graph({"a": meta_a, "b": meta_b})
        assert "b" in graph
        assert "a" in graph.get("b", [])

    def test_topological_sort(self) -> None:
        meta_a = PluginMetadata(name="a", author="me", version="1.0.0")
        meta_b = PluginMetadata(name="b", author="me", version="1.0.0", dependencies=[PluginDependency("a")])
        meta_c = PluginMetadata(name="c", author="me", version="1.0.0", dependencies=[PluginDependency("b")])
        order = resolve_load_order({"a": meta_a, "b": meta_b, "c": meta_c})
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_no_dependencies(self) -> None:
        meta = PluginMetadata(name="standalone", author="me", version="1.0.0")
        order = resolve_load_order({"standalone": meta})
        assert order == ["standalone"]

    def test_cyclic_dependency(self) -> None:
        meta_a = PluginMetadata(name="a", author="me", version="1.0.0", dependencies=[PluginDependency("b")])
        meta_b = PluginMetadata(name="b", author="me", version="1.0.0", dependencies=[PluginDependency("a")])
        with pytest.raises(PluginCycleError):
            resolve_load_order({"a": meta_a, "b": meta_b})

    def test_self_cycle(self) -> None:
        meta = PluginMetadata(name="self", author="me", version="1.0.0", dependencies=[PluginDependency("self")])
        with pytest.raises(PluginCycleError):
            resolve_load_order({"self": meta})

    def test_missing_dependency(self) -> None:
        meta = PluginMetadata(name="orphan", author="me", version="1.0.0", dependencies=[PluginDependency("missing")])
        with pytest.raises(PluginDependencyError):
            resolve_load_order({"orphan": meta})

    def test_optional_dependency_allowed(self) -> None:
        meta = PluginMetadata(
            name="main", author="me", version="1.0.0", dependencies=[PluginDependency("opt", optional=True)]
        )
        order = resolve_load_order({"main": meta})
        assert order == ["main"]

    def test_detect_cycles(self) -> None:
        graph = {"a": ["b"], "b": ["c"], "c": ["a"]}
        with pytest.raises(PluginCycleError):
            detect_cycles(graph)


# =========================================================================
# Validation
# =========================================================================


class TestValidation:
    def test_validate_metadata_valid(self) -> None:
        meta = PluginMetadata(name="valid", author="me", version="1.0.0")
        validate_metadata(meta)

    def test_validate_metadata_bad_version(self) -> None:
        meta = PluginMetadata(name="bad", author="me", version="not-semver")
        with pytest.raises(PluginValidationError):
            validate_metadata(meta)

    def test_validate_no_duplicate_ids(self) -> None:
        validate_no_duplicate_ids("new", {"existing"})
        with pytest.raises(PluginValidationError):
            validate_no_duplicate_ids("existing", {"existing"})

    def test_validate_dependencies_ok(self) -> None:
        deps = [PluginDependency("a"), PluginDependency("b")]
        validate_dependencies(deps, {"a", "b"})

    def test_validate_dependencies_missing(self) -> None:
        deps = [PluginDependency("a"), PluginDependency("missing")]
        with pytest.raises(PluginDependencyError):
            validate_dependencies(deps, {"a"})

    def test_validate_dependencies_optional_allowed(self) -> None:
        deps = [PluginDependency("missing", optional=True)]
        validate_dependencies(deps, {"a"})


# =========================================================================
# PluginManager
# =========================================================================


class TestPluginManager:
    def test_create_manager(self, manager: PluginManager) -> None:
        assert manager.registry.count() == 0

    def test_install_plugin(self, manager: PluginManager) -> None:
        plugin = manager.install(HelloWorldPlugin)
        assert manager.registry.count() == 1
        assert manager.registry.get("hello_world") is plugin

    def test_install_duplicate_fails(self, manager: PluginManager) -> None:
        manager.install(HelloWorldPlugin)
        with pytest.raises(PluginValidationError):
            manager.install(HelloWorldPlugin)

    def test_get_plugin(self, manager: PluginManager) -> None:
        manager.install(HelloWorldPlugin)
        plugin = manager.get("hello_world")
        assert plugin.plugin_id == "hello_world"

    def test_get_nonexistent(self, manager: PluginManager) -> None:
        with pytest.raises(PluginNotFoundError):
            manager.get("nonexistent")

    def test_list_plugins(self, manager: PluginManager) -> None:
        manager.install(HelloWorldPlugin)
        manager.install(LoggerPlugin)
        assert len(manager.list()) == 2

    def test_enable_disable(self, manager: PluginManager) -> None:
        manager.install(HelloWorldPlugin)
        manager.activate_all()
        assert manager.get("hello_world").status == PluginStatus.ACTIVE
        manager.disable("hello_world")
        assert manager.get("hello_world").status == PluginStatus.DISABLED
        manager.enable("hello_world")
        assert manager.get("hello_world").status == PluginStatus.ACTIVE

    def test_uninstall(self, manager: PluginManager) -> None:
        manager.install(HelloWorldPlugin)
        manager.uninstall("hello_world")
        assert manager.registry.count() == 0

    def test_activate_all(self, manager: PluginManager) -> None:
        manager.install(HelloWorldPlugin)
        manager.activate_all()
        assert manager.get("hello_world").status == PluginStatus.ACTIVE

    def test_shutdown_all(self, manager: PluginManager) -> None:
        manager.install(HelloWorldPlugin)
        manager.activate_all()
        manager.shutdown_all()
        assert manager.get("hello_world").status == PluginStatus.UNINSTALLED

    def test_run_hook(self, manager: PluginManager) -> None:
        manager.install(HelloWorldPlugin)
        manager.activate_all()
        events = manager.run_hook(HookPoint.ON_LOAD)
        assert len(events) > 0

    def test_run_hook_no_active_plugins(self, manager: PluginManager) -> None:
        events = manager.run_hook(HookPoint.BEFORE_PIPELINE)
        assert events == []

    def test_pipeline_hooks(self, manager: PluginManager) -> None:
        manager.install(HelloWorldPlugin)
        manager.activate_all()
        before, after = manager.run_pipeline_hooks(HookPoint.BEFORE_PIPELINE, HookPoint.AFTER_PIPELINE)
        assert len(before) > 0
        assert len(after) > 0

    def test_priority_ordering(self, manager: PluginManager) -> None:
        class HighPriorityPlugin(Plugin):
            metadata = PluginMetadata(name="high", author="me", version="1.0.0", priority=10)

            def before_pipeline(self, ctx: PluginContext, event: HookEvent) -> HookResult:
                ctx.pipeline_state["order"] = ctx.pipeline_state.get("order", []) + ["high"]
                return HookResult.CONTINUE

        class LowPriorityPlugin(Plugin):
            metadata = PluginMetadata(name="low", author="me", version="1.0.0", priority=100)

            def before_pipeline(self, ctx: PluginContext, event: HookEvent) -> HookResult:
                ctx.pipeline_state["order"] = ctx.pipeline_state.get("order", []) + ["low"]
                return HookResult.CONTINUE

        manager.install(LowPriorityPlugin)
        manager.install(HighPriorityPlugin)
        manager.activate_all()
        manager.run_hook(HookPoint.BEFORE_PIPELINE)
        ctx = manager._context
        assert ctx is not None
        order = ctx.pipeline_state.get("order", [])
        assert order == ["high", "low"], f"Expected high before low, got {order}"


# =========================================================================
# Plugin loader
# =========================================================================


class TestPluginLoader:
    def test_instantiate_plugin(self) -> None:
        plugin = instantiate_plugin(HelloWorldPlugin)
        assert plugin.plugin_id == "hello_world"
        assert plugin.status == PluginStatus.INSTALLED

    def test_instantiate_missing_metadata(self) -> None:
        class BadPlugin(Plugin):
            pass

        with pytest.raises(PluginValidationError):
            instantiate_plugin(BadPlugin)


# =========================================================================
# Example plugins
# =========================================================================


class TestExamplePlugins:
    def test_hello_world(self, context: PluginContext) -> None:
        plugin = HelloWorldPlugin()
        plugin.metadata = HelloWorldPlugin.metadata
        assert plugin.on_load(context) == HookResult.CONTINUE
        assert plugin.on_initialize(context) == HookResult.CONTINUE

    def test_logger_plugin(self, context: PluginContext) -> None:
        plugin = LoggerPlugin()
        plugin.metadata = LoggerPlugin.metadata
        event = HookEvent(HookPoint.BEFORE_PIPELINE, context)
        assert plugin.before_pipeline(context, event) == HookResult.CONTINUE

    def test_metrics_plugin(self, context: PluginContext) -> None:
        plugin = MetricsPlugin()
        plugin.metadata = MetricsPlugin.metadata
        event = HookEvent(HookPoint.AFTER_PIPELINE, context)
        plugin.after_pipeline(context, event)
        assert context.metrics.get("hook_count") == 1

    def test_timing_plugin(self, context: PluginContext) -> None:
        plugin = TimingPlugin()
        plugin.metadata = TimingPlugin.metadata
        event = HookEvent(HookPoint.BEFORE_PIPELINE, context)
        plugin.before_pipeline(context, event)
        assert "pipeline_start" in context.runtime
        plugin.after_pipeline(context, event)
        assert "pipeline_total_ms" in context.metrics

    def test_reasoning_trace(self, context: PluginContext) -> None:
        plugin = ReasoningTracePlugin()
        plugin.metadata = ReasoningTracePlugin.metadata
        before_event = HookEvent(HookPoint.BEFORE_REASONING, context, {"q": "test"})
        plugin.before_reasoning(context, before_event)
        assert "reasoning_input" in context.runtime
        after_event = HookEvent(HookPoint.AFTER_REASONING, context)
        plugin.after_reasoning(context, after_event)
        assert len(context.metrics.get("reasoning_traces", [])) == 1

    def test_semantic_similarity(self, context: PluginContext) -> None:
        plugin = SemanticSimilarityPlugin()
        plugin.metadata = SemanticSimilarityPlugin.metadata
        event = HookEvent(HookPoint.AFTER_SEMANTICS, context)
        plugin.after_semantics(context, event)
        assert context.pipeline_state.get("semantic_similarity_score") == 0.85

    def test_memory_statistics(self, context: PluginContext) -> None:
        from ares.plugins.examples import MemoryStatisticsPlugin

        plugin = MemoryStatisticsPlugin()
        plugin.metadata = MemoryStatisticsPlugin.metadata
        event = HookEvent(HookPoint.AFTER_PIPELINE, context, {"size": 100})
        plugin.after_pipeline(context, event)
        samples = context.metrics.get("memory_samples", [])
        assert len(samples) == 1


# =========================================================================
# Lifecycle
# =========================================================================


class TestLifecycle:
    def test_plugin_lifecycle(self, manager: PluginManager) -> None:
        from ares.plugins.lifecycle import activate_plugin, shutdown_plugin

        ctx = PluginContext(logger=logging.getLogger("test"))
        plugin = manager.install(HelloWorldPlugin)
        activate_plugin(plugin, ctx)
        assert plugin.status == PluginStatus.ACTIVE
        shutdown_plugin(plugin, ctx)
        assert plugin.status == PluginStatus.UNINSTALLED

    def test_run_lifecycle_hook(self, context: PluginContext) -> None:
        from ares.plugins.lifecycle import run_lifecycle_hook

        plugin = HelloWorldPlugin()
        plugin.metadata = HelloWorldPlugin.metadata
        plugin.status = PluginStatus.ACTIVE
        event = run_lifecycle_hook(plugin, HookPoint.ON_LOAD, context)
        assert not event.cancelled


# =========================================================================
# Edge cases
# =========================================================================


class TestEdgeCases:
    def test_no_plugins_found(self, manager: PluginManager) -> None:
        plugins = manager.load()
        assert plugins == []

    def test_plugin_to_dict(self) -> None:
        plugin = HelloWorldPlugin()
        plugin.metadata = HelloWorldPlugin.metadata
        d = plugin.to_dict()
        assert d["plugin_id"] == "hello_world"
        assert d["version"] == "1.0.0"
        assert d["status"] == PluginStatus.INSTALLED.name

    def test_plugin_repr(self) -> None:
        plugin = HelloWorldPlugin()
        plugin.metadata = HelloWorldPlugin.metadata
        r = repr(plugin)
        assert "hello_world" in r
        assert "1.0.0" in r

    def test_build_dependency_graph_empty(self) -> None:
        graph = build_dependency_graph({})
        assert graph == {}

    def test_topological_sort_empty(self) -> None:
        assert topological_sort({}) == []

    def test_discovery_from_nonexistent_folder(self) -> None:
        from ares.plugins.discovery import discover_from_folder

        plugins = discover_from_folder("/nonexistent/plugins")
        assert plugins == []

    def test_config_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ARES_PLUGIN_ENABLED", "true")
        cfg = PluginConfig.from_env()
        assert cfg.get("enabled") == "true"

    def test_parse_semver(self) -> None:
        from ares.plugins.utils import parse_semver

        assert parse_semver("1.2.3") == (1, 2, 3)
        with pytest.raises(ValueError):
            parse_semver("invalid")

    def test_normalize_plugin_id(self) -> None:
        from ares.plugins.utils import normalize_plugin_id

        assert normalize_plugin_id("My Plugin!") == "my_plugin_"
        assert normalize_plugin_id("simple") == "simple"
