from __future__ import annotations

from collections.abc import Callable

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryPlugin, MemoryType


class MemoryTypeRegistry:
    def __init__(self) -> None:
        self._factories: dict[MemoryType, Callable[..., MemoryEntry]] = {}

    def register(self, memory_type: MemoryType, factory: Callable[..., MemoryEntry]) -> None:
        self._factories[memory_type] = factory

    def get_factory(self, memory_type: MemoryType) -> Callable[..., MemoryEntry] | None:
        return self._factories.get(memory_type)

    def list_types(self) -> list[MemoryType]:
        return list(self._factories.keys())


class MemoryPluginRegistry:
    def __init__(self) -> None:
        self._plugins: list[MemoryPlugin] = []

    def register(self, plugin: MemoryPlugin) -> None:
        self._plugins.append(plugin)

    def get_plugins(self) -> list[MemoryPlugin]:
        return list(self._plugins)

    def process_before_store(self, entry: MemoryEntry) -> MemoryEntry:
        for plugin in self._plugins:
            entry = plugin.process_before_store(entry)
        return entry

    def process_after_retrieve(self, entry: MemoryEntry | None) -> MemoryEntry | None:
        for plugin in self._plugins:
            entry = plugin.process_after_retrieve(entry)
        return entry
