from __future__ import annotations

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryPlugin


class DefaultMemoryPlugin(MemoryPlugin):
    def process_before_store(self, entry: MemoryEntry) -> MemoryEntry:
        return entry

    def process_after_retrieve(self, entry: MemoryEntry | None) -> MemoryEntry | None:
        return entry
