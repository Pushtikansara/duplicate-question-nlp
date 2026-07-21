from __future__ import annotations

import pytest

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryPlugin
from duplicate_question_app._memory.memory_registry import MemoryPluginRegistry
from duplicate_question_app._memory.plugins import DefaultMemoryPlugin

from .conftest import (
    MemoryEngine,
    create_episodic_memory,
)


class TestPlugins:
    def test_default_plugin_before_store(self) -> None:
        plugin = DefaultMemoryPlugin()
        entry = create_episodic_memory()
        result = plugin.process_before_store(entry)
        assert result is entry

    def test_default_plugin_after_retrieve(self) -> None:
        plugin = DefaultMemoryPlugin()
        entry = create_episodic_memory()
        result = plugin.process_after_retrieve(entry)
        assert result is entry

    def test_default_plugin_passthrough(self) -> None:
        plugin = DefaultMemoryPlugin()
        assert plugin.process_after_retrieve(None) is None

    def test_custom_plugin(self) -> None:
        class _CustomPlugin(MemoryPlugin):
            def process_before_store(self, entry: MemoryEntry) -> MemoryEntry:
                entry.metadata["custom"] = True
                return entry

            def process_after_retrieve(self, entry: MemoryEntry | None) -> MemoryEntry | None:
                if entry is not None:
                    entry.metadata["retrieved"] = True
                return entry

        plugin = _CustomPlugin()
        entry = create_episodic_memory()
        result = plugin.process_before_store(entry)
        assert result.metadata.get("custom") is True
        result2 = plugin.process_after_retrieve(entry)
        assert result2 is not None
        assert result2.metadata.get("retrieved") is True

    def test_plugin_in_engine(self) -> None:
        class _TrackingPlugin(MemoryPlugin):
            def __init__(self) -> None:
                self.before_called = False
                self.after_called = False

            def process_before_store(self, entry: MemoryEntry) -> MemoryEntry:
                self.before_called = True
                return entry

            def process_after_retrieve(self, entry: MemoryEntry | None) -> MemoryEntry | None:
                self.after_called = True
                return entry

        plugin = _TrackingPlugin()
        engine = MemoryEngine(plugins=[plugin])
        entry = create_episodic_memory()
        result = engine.store_entry(entry)
        assert plugin.before_called is True
        engine.retrieve(result.memory_id)
        assert plugin.after_called is True

    def test_plugin_modifies_entry(self) -> None:
        class _MutatorPlugin(MemoryPlugin):
            def process_before_store(self, entry: MemoryEntry) -> MemoryEntry:
                entry.tags.append("mutated")
                return entry

            def process_after_retrieve(self, entry: MemoryEntry | None) -> MemoryEntry | None:
                if entry is not None:
                    entry.metadata["post"] = True
                return entry

        engine = MemoryEngine(plugins=[_MutatorPlugin()])
        entry = create_episodic_memory()
        result = engine.store_entry(entry)
        retrieved = engine.retrieve(result.memory_id)
        assert retrieved is not None
        assert retrieved.metadata.get("post") is True

    def test_plugin_chain_execution(self) -> None:
        class _ChainPlugin(MemoryPlugin):
            def __init__(self, marker: str) -> None:
                self.marker = marker

            def process_before_store(self, entry: MemoryEntry) -> MemoryEntry:
                entry.tags.append(self.marker)
                return entry

            def process_after_retrieve(self, entry: MemoryEntry | None) -> MemoryEntry | None:
                if entry is not None:
                    entry.tags.append(f"after-{self.marker}")
                return entry

        engine = MemoryEngine(plugins=[_ChainPlugin("p1"), _ChainPlugin("p2")])
        entry = create_episodic_memory()
        result = engine.store_entry(entry)
        retrieved = engine.retrieve(result.memory_id)
        assert retrieved is not None

    def test_plugin_does_not_break_on_none(self) -> None:
        plugin = DefaultMemoryPlugin()
        assert plugin.process_after_retrieve(None) is None

    def test_plugin_registration(self) -> None:
        registry = MemoryPluginRegistry()
        plugin = DefaultMemoryPlugin()
        registry.register(plugin)
        assert plugin in registry.get_plugins()

    def test_plugin_error_handling(self) -> None:
        class _FailingPlugin(MemoryPlugin):
            def process_before_store(self, entry: MemoryEntry) -> MemoryEntry:
                msg = "plugin failed"
                raise RuntimeError(msg)

            def process_after_retrieve(self, entry: MemoryEntry | None) -> MemoryEntry | None:
                msg = "plugin failed"
                raise RuntimeError(msg)

        registry = MemoryPluginRegistry()
        registry.register(_FailingPlugin())
        entry = create_episodic_memory()
        with pytest.raises(RuntimeError):
            registry.process_before_store(entry)
