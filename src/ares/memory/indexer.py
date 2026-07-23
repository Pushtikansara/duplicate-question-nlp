from __future__ import annotations

import logging
from collections import defaultdict

from ares.memory.types import MemoryEntry

logger = logging.getLogger(__name__)


class MemoryIndexer:
    def __init__(self) -> None:
        self._key_index: dict[str, set[str]] = defaultdict(set)
        self._agent_index: dict[str, set[str]] = defaultdict(set)
        self._session_index: dict[str, set[str]] = defaultdict(set)
        self._tag_index: dict[str, set[str]] = defaultdict(set)
        self._tier_index: dict[str, set[str]] = defaultdict(set)
        self._domain_index: dict[str, set[str]] = defaultdict(set)

    def index_entry(self, entry: MemoryEntry) -> None:
        self._key_index[entry.key].add(entry.memory_id)
        self._agent_index[entry.agent_id].add(entry.memory_id)
        self._session_index[entry.session_id].add(entry.memory_id)
        self._tier_index[entry.tier.name].add(entry.memory_id)
        self._domain_index[entry.domain.name].add(entry.memory_id)
        for tag in entry.tags:
            self._tag_index[tag].add(entry.memory_id)

    def remove_entry(self, entry: MemoryEntry) -> None:
        self._remove_from_index(self._key_index, entry.key, entry.memory_id)
        self._remove_from_index(self._agent_index, entry.agent_id, entry.memory_id)
        self._remove_from_index(self._session_index, entry.session_id, entry.memory_id)
        self._remove_from_index(self._tier_index, entry.tier.name, entry.memory_id)
        self._remove_from_index(self._domain_index, entry.domain.name, entry.memory_id)
        for tag in entry.tags:
            self._remove_from_index(self._tag_index, tag, entry.memory_id)

    def find_by_key(self, key: str) -> set[str]:
        return set(self._key_index.get(key, set()))

    def find_by_agent(self, agent_id: str) -> set[str]:
        return set(self._agent_index.get(agent_id, set()))

    def find_by_session(self, session_id: str) -> set[str]:
        return set(self._session_index.get(session_id, set()))

    def find_by_tag(self, tag: str) -> set[str]:
        return set(self._tag_index.get(tag, set()))

    def find_by_tier(self, tier: str) -> set[str]:
        return set(self._tier_index.get(tier, set()))

    def find_by_domain(self, domain: str) -> set[str]:
        return set(self._domain_index.get(domain, set()))

    def clear(self) -> None:
        self._key_index.clear()
        self._agent_index.clear()
        self._session_index.clear()
        self._tag_index.clear()
        self._tier_index.clear()
        self._domain_index.clear()

    @staticmethod
    def _remove_from_index(index: dict[str, set[str]], key: str, memory_id: str) -> None:
        ids = index.get(key)
        if ids:
            ids.discard(memory_id)
            if not ids:
                del index[key]
