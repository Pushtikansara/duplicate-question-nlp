from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


class CacheEntry:
    def __init__(self, key: str, value: Any, ttl: float) -> None:
        self.key = key
        self.value = value
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class APICache:
    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0) -> None:
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def _make_key(self, prefix: str, data: dict[str, Any]) -> str:
        raw = json.dumps(data, sort_keys=True)
        return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"

    def get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        ttl = ttl or self._default_ttl
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict_oldest()
            self._cache[key] = CacheEntry(key, value, ttl)

    def _evict_oldest(self) -> None:
        if not self._cache:
            return
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].expires_at)
        del self._cache[oldest_key]

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def stats(self) -> dict[str, Any]:
        with self._lock:
            valid = sum(1 for e in self._cache.values() if not e.is_expired())
            return {
                "size": len(self._cache),
                "valid": valid,
                "expired": len(self._cache) - valid,
                "max_size": self._max_size,
            }


_api_cache: APICache | None = None


def get_api_cache() -> APICache:
    global _api_cache
    if _api_cache is None:
        _api_cache = APICache()
    return _api_cache
