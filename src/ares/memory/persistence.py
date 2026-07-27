from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime
from typing import Any

import numpy as np

from ares.memory.types import MemoryDomain, MemoryEntry, MemoryTier

logger = logging.getLogger(__name__)


class _JSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _entry_to_dict(entry: MemoryEntry) -> dict[str, Any]:
    return {
        "memory_id": entry.memory_id,
        "key": entry.key,
        "value": entry.value,
        "tier": entry.tier.name,
        "domain": entry.domain.name,
        "timestamp": entry.timestamp.isoformat(),
        "ttl_seconds": entry.ttl_seconds,
        "metadata": entry.metadata,
        "agent_id": entry.agent_id,
        "session_id": entry.session_id,
        "score": entry.score,
        "access_count": entry.access_count,
        "version": entry.version,
        "tags": list(entry.tags),
    }


def _dict_to_entry(d: dict[str, Any]) -> MemoryEntry:
    return MemoryEntry(
        memory_id=d["memory_id"],
        key=d["key"],
        value=d["value"],
        tier=MemoryTier[d["tier"]],
        domain=MemoryDomain[d["domain"]],
        timestamp=datetime.fromisoformat(d["timestamp"]),
        ttl_seconds=d.get("ttl_seconds"),
        metadata=d.get("metadata", {}),
        agent_id=d.get("agent_id", ""),
        session_id=d.get("session_id", ""),
        score=d.get("score", 1.0),
        access_count=d.get("access_count", 0),
        version=d.get("version", 1),
        tags=d.get("tags", []),
    )


class MemoryPersistence:
    def __init__(self, base_path: str = "") -> None:
        self._base_path = base_path or os.path.join(os.getcwd(), ".ares_memory")
        self._lock = threading.Lock()

    @property
    def base_path(self) -> str:
        return self._base_path

    def save_entry(self, entry: MemoryEntry) -> str:
        tier_dir = self._tier_path(entry.tier)
        return self._write_entry(tier_dir, entry)

    def save_entries(self, entries: list[MemoryEntry]) -> list[str]:
        return [self.save_entry(e) for e in entries]

    def load_entry(self, memory_id: str, tier: MemoryTier) -> MemoryEntry | None:
        path = os.path.join(self._tier_path(tier), f"{memory_id}.json")
        return self._read_entry(path)

    def load_entries(self, tier: MemoryTier) -> list[MemoryEntry]:
        tier_dir = self._tier_path(tier)
        return self._load_directory(tier_dir, tier)

    def load_all(self) -> dict[MemoryTier, list[MemoryEntry]]:
        return {tier: self.load_entries(tier) for tier in MemoryTier}

    def delete_entry(self, memory_id: str, tier: MemoryTier) -> bool:
        path = os.path.join(self._tier_path(tier), f"{memory_id}.json")
        with self._lock:
            if os.path.isfile(path):
                os.remove(path)
                return True
            return False

    def clear_tier(self, tier: MemoryTier) -> int:
        tier_dir = self._tier_path(tier)
        return self._clear_directory(tier_dir)

    def clear_all(self) -> dict[str, int]:
        return {tier.name: self.clear_tier(tier) for tier in MemoryTier}

    def entry_exists(self, memory_id: str, tier: MemoryTier) -> bool:
        path = os.path.join(self._tier_path(tier), f"{memory_id}.json")
        return os.path.isfile(path)

    def count_entries(self, tier: MemoryTier) -> int:
        tier_dir = self._tier_path(tier)
        with self._lock:
            if not os.path.isdir(tier_dir):
                return 0
            return len([f for f in os.listdir(tier_dir) if f.endswith(".json")])

    def _tier_path(self, tier: MemoryTier) -> str:
        path = os.path.join(self._base_path, tier.name.lower())
        os.makedirs(path, exist_ok=True)
        return path

    def _write_entry(self, directory: str, entry: MemoryEntry) -> str:
        path = os.path.join(directory, f"{entry.memory_id}.json")
        with self._lock:
            with open(path, "w") as f:
                json.dump(_entry_to_dict(entry), f, indent=2, cls=_JSONEncoder)
        logger.debug("Saved memory entry '%s' to %s", entry.memory_id, path)
        return path

    def _read_entry(self, path: str) -> MemoryEntry | None:
        with self._lock:
            if not os.path.isfile(path):
                return None
            try:
                with open(path) as f:
                    data = json.load(f)
                return _dict_to_entry(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.error("Failed to read memory entry from %s: %s", path, e)
                return None

    def _load_directory(self, directory: str, tier: MemoryTier) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        with self._lock:
            if not os.path.isdir(directory):
                return entries
            for filename in sorted(os.listdir(directory)):
                if not filename.endswith(".json"):
                    continue
                path = os.path.join(directory, filename)
                try:
                    with open(path) as f:
                        data = json.load(f)
                    entry = _dict_to_entry(data)
                    entries.append(entry)
                except Exception as e:
                    logger.warning("Skipping corrupted file %s: %s", filename, e)
        return entries

    def _clear_directory(self, directory: str) -> int:
        count = 0
        with self._lock:
            if not os.path.isdir(directory):
                return 0
            for filename in os.listdir(directory):
                if filename.endswith(".json"):
                    os.remove(os.path.join(directory, filename))
                    count += 1
        return count
