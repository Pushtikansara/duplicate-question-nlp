from __future__ import annotations

import time
from collections import OrderedDict
from threading import Lock
from typing import Any


class SharedCache:
    def __init__(self, capacity: int = 1000, default_ttl_seconds: float = 300.0) -> None:
        self._capacity = capacity
        self._default_ttl = default_ttl_seconds
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = _CacheEntry(
                value=value,
                expires_at=time.time() + (ttl_seconds or self._default_ttl),
            )
            self._evict_if_needed()

    def has(self, key: str) -> bool:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                del self._cache[key]
                return False
            return True

    def delete(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def _evict_if_needed(self) -> None:
        while len(self._cache) > self._capacity:
            self._cache.popitem(last=False)

    def sweep_expired(self) -> int:
        now = time.time()
        expired_keys = [k for k, v in self._cache.items() if v.expires_at <= now]
        for k in expired_keys:
            self._cache.pop(k, None)
        return len(expired_keys)

    def size(self) -> int:
        return len(self._cache)

    def stats(self) -> dict[str, Any]:
        return {
            "capacity": self._capacity,
            "size": len(self._cache),
            "default_ttl_seconds": self._default_ttl,
        }


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, expires_at: float) -> None:
        self.value = value
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        return time.time() > self.expires_at
