from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryStatus, MemoryStore, MemoryType

logger = logging.getLogger(__name__)


class InMemoryMemoryStore(MemoryStore):
    def __init__(self) -> None:
        self._store: dict[str, MemoryEntry] = {}
        self._lock = threading.Lock()

    def store(self, entry: MemoryEntry) -> str:
        with self._lock:
            if not entry.memory_id:
                entry.memory_id = str(uuid.uuid4())
            if entry.version < 1:
                entry.version = 1
            if entry.timestamp is None:
                entry.timestamp = datetime.now()
            self._store[entry.memory_id] = entry
            logger.debug(
                "Stored memory %s (type=%s, version=%d)", entry.memory_id, entry.memory_type.value, entry.version
            )
            return entry.memory_id

    def retrieve(self, memory_id: str) -> MemoryEntry | None:
        with self._lock:
            entry = self._store.get(memory_id)
            if entry is None:
                logger.debug("Memory %s not found", memory_id)
                return None
            return entry

    def update(self, entry: MemoryEntry) -> str:
        with self._lock:
            existing = self._store.get(entry.memory_id)
            if existing is None:
                raise KeyError(f"Memory {entry.memory_id} not found for update")
            entry.version = existing.version + 1
            entry.timestamp = datetime.now()
            self._store[entry.memory_id] = entry
            logger.debug(
                "Updated memory %s (type=%s, version=%d)", entry.memory_id, entry.memory_type.value, entry.version
            )
            return entry.memory_id

    def delete(self, memory_id: str, soft: bool = True) -> bool:
        with self._lock:
            entry = self._store.get(memory_id)
            if entry is None:
                logger.debug("Memory %s not found for deletion", memory_id)
                return False
            if soft:
                entry.status = MemoryStatus.DELETED
                logger.debug("Soft-deleted memory %s", memory_id)
            else:
                del self._store[memory_id]
                logger.debug("Hard-deleted memory %s", memory_id)
            return True

    def list_by_type(self, memory_type: MemoryType, limit: int = 100, offset: int = 0) -> tuple[list[MemoryEntry], int]:
        with self._lock:
            all_entries = [
                e for e in self._store.values() if e.memory_type == memory_type and e.status != MemoryStatus.DELETED
            ]
            total = len(all_entries)
            return all_entries[offset : offset + limit], total

    def list_all(self, limit: int = 100, offset: int = 0) -> tuple[list[MemoryEntry], int]:
        with self._lock:
            active = [e for e in self._store.values() if e.status != MemoryStatus.DELETED]
            total = len(active)
            return active[offset : offset + limit], total

    def count(self) -> int:
        with self._lock:
            return sum(1 for e in self._store.values() if e.status != MemoryStatus.DELETED)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            logger.debug("Memory store cleared")
