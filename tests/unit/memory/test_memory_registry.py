from __future__ import annotations

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryPlugin, MemoryType
from duplicate_question_app._memory.memory_registry import MemoryPluginRegistry, MemoryTypeRegistry


class TestMemoryRegistry:
    def test_register_and_get_factory(self) -> None:
        registry = MemoryTypeRegistry()
        from .conftest import create_episodic_memory

        registry.register(MemoryType.EPISODIC, create_episodic_memory)
        factory = registry.get_factory(MemoryType.EPISODIC)
        assert factory is not None
        entry = factory()
        assert entry.memory_type == MemoryType.EPISODIC

    def test_get_factory_nonexistent(self) -> None:
        registry = MemoryTypeRegistry()
        assert registry.get_factory(MemoryType.EPISODIC) is None

    def test_list_types(self) -> None:
        registry = MemoryTypeRegistry()
        from .conftest import create_episodic_memory, create_semantic_memory

        registry.register(MemoryType.EPISODIC, create_episodic_memory)
        registry.register(MemoryType.SEMANTIC, create_semantic_memory)
        types = registry.list_types()
        assert MemoryType.EPISODIC in types
        assert MemoryType.SEMANTIC in types

    def test_register_plugin(self) -> None:
        registry = MemoryPluginRegistry()
        from duplicate_question_app._memory.plugins import DefaultMemoryPlugin

        plugin = DefaultMemoryPlugin()
        registry.register(plugin)
        assert len(registry.get_plugins()) == 1

    def test_plugin_process_before_store(self) -> None:
        registry = MemoryPluginRegistry()
        from duplicate_question_app._memory.plugins import DefaultMemoryPlugin

        registry.register(DefaultMemoryPlugin())
        from .conftest import create_episodic_memory

        entry = create_episodic_memory()
        result = registry.process_before_store(entry)
        assert result is entry

    def test_plugin_process_after_retrieve(self) -> None:
        registry = MemoryPluginRegistry()
        from duplicate_question_app._memory.plugins import DefaultMemoryPlugin

        registry.register(DefaultMemoryPlugin())
        from .conftest import create_episodic_memory

        entry = create_episodic_memory()
        result = registry.process_after_retrieve(entry)
        assert result is entry

    def test_multiple_plugins(self) -> None:
        registry = MemoryPluginRegistry()
        from duplicate_question_app._memory.plugins import DefaultMemoryPlugin

        registry.register(DefaultMemoryPlugin())
        registry.register(DefaultMemoryPlugin())
        assert len(registry.get_plugins()) == 2

    def test_plugin_registry_empty(self) -> None:
        registry = MemoryPluginRegistry()
        assert registry.get_plugins() == []
        from .conftest import create_episodic_memory

        entry = create_episodic_memory()
        assert registry.process_before_store(entry) is entry
        assert registry.process_after_retrieve(entry) is entry

    def test_type_registry_empty(self) -> None:
        registry = MemoryTypeRegistry()
        assert registry.list_types() == []

    def test_plugin_chaining(self) -> None:
        registry = MemoryPluginRegistry()

        class _TestPlugin(MemoryPlugin):
            def process_before_store(self, entry: MemoryEntry) -> MemoryEntry:
                entry.tags.append("plugin-applied")
                return entry

            def process_after_retrieve(self, entry: MemoryEntry | None) -> MemoryEntry | None:
                if entry is not None:
                    entry.metadata["plugin"] = "seen"
                return entry

        registry.register(_TestPlugin())
        from .conftest import create_episodic_memory

        entry = create_episodic_memory()
        result = registry.process_before_store(entry)
        assert "plugin-applied" in result.tags
        result2 = registry.process_after_retrieve(entry)
        assert result2 is not None
        assert result2.metadata.get("plugin") == "seen"
