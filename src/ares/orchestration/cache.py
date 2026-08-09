from __future__ import annotations

import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ares.orchestration.constants import DEFAULT_CACHE_MAX_ENTRIES, DEFAULT_CACHE_TTL_SECONDS
from ares.orchestration.exceptions import CacheError

#: Result of a cache read. ``None`` is an ambiguous but documented value:
#: it is cacheable, so use ``contains()`` when presence must be distinguished
#: from "no value".
CacheableValue = Any


def _is_cacheable(value: Any, _seen: set[int] | None = None) -> bool:
    """Determine whether a value is safe to cache.

    A value is cacheable when it is:

    - ``None`` (documented contract),
    - a primitive (``str``, ``bytes``, ``int``, ``float``, ``bool``),
    - a dataclass instance (e.g. ``QueryAnalysis``, ``PredictionResult``),
    - a ``list``/``tuple``/``dict``/``set``/``frozenset`` whose contents are
      themselves cacheable.

    Arbitrary objects (locks, generators, modules, sockets, ...) are rejected
    because they carry unsafe non-deterministic state and are typically
    process-local. Custom checkers can be supplied via the
    ``value_checker`` constructor argument.
    """
    if value is None or isinstance(value, (str, bytes, int, float, bool)):
        return True
    if hasattr(value, "__dataclass_fields__"):
        return True
    if isinstance(value, (list, tuple, set, frozenset)):
        return all(_is_cacheable(item) for item in value)
    if isinstance(value, dict):
        return all(_is_cacheable(key) and _is_cacheable(item) for key, item in value.items())
    return False


@dataclass(frozen=True)
class CacheEntry:
    value: CacheableValue
    expires_at: float | None


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate,
        }


class InMemoryCacheProvider:
    """Deterministic, thread-safe, bounded LRU + TTL cache.

    Implements the ``ares.orchestration.interfaces.CacheProvider`` protocol.

    Semantics:

    - **TTL**: ``ttl > 0`` expires the entry after ``ttl`` seconds
      (``time.monotonic``); ``ttl == 0`` keeps the entry until evicted or
      cleared; ``ttl < 0`` raises ``CacheError``.
    - **Capacity**: ``max_size > 0`` enables bounded LRU eviction (the least
      recently used entry is evicted on insert); ``max_size <= 0`` means an
      unbounded cache (no eviction ever).
    - **Recency**: ``get()`` and ``set()`` on an existing key move the entry
      to the most-recently-used end.
    - **Expiry**: expired entries are removed lazily on ``get``/``contains``
      and eagerly by ``cleanup()``.
    - **Values**: only cacheable values are accepted (see ``_is_cacheable``);
      anything else raises ``CacheError``.

    This is intentionally the extension point for a future Redis-backed
    provider; orchestration code should depend on ``CacheProvider``.
    """

    def __init__(
        self,
        max_size: int = DEFAULT_CACHE_MAX_ENTRIES,
        *,
        default_ttl: int = DEFAULT_CACHE_TTL_SECONDS,
        value_checker: Callable[[Any], bool] | None = None,
    ) -> None:
        if isinstance(max_size, bool):
            raise TypeError("max_size must be an integer, not bool")
        self._max_size = int(max_size)
        self._default_ttl = default_ttl
        self._value_checker = value_checker or _is_cacheable
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def default_ttl(self) -> int:
        return self._default_ttl

    def get(self, key: str) -> CacheableValue | None:
        """Return the value for ``key`` or ``None`` when absent/expired.

        A hit updates recency. An expired entry is removed and counted as an
        expiration (the call is reported as a miss).
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return None
            if self._is_expired(entry):
                del self._entries[key]
                self._expirations += 1
                self._misses += 1
                return None
            self._entries.move_to_end(key)
            self._hits += 1
            return entry.value

    def set(self, key: str, value: CacheableValue, ttl: int = DEFAULT_CACHE_TTL_SECONDS) -> None:
        """Store ``value`` under ``key``.

        Overwrites an existing entry. Evicts the least recently used entry
        when at capacity (bounded mode only).
        """
        with self._lock:
            if ttl < 0:
                raise CacheError(f"Cannot store cache entry with negative ttl={ttl}")
            if not self._value_checker(value):
                raise CacheError("Value is not cacheable; cache only primitives, dataclasses, or containers of those")
            expires_at = time.monotonic() + ttl if ttl > 0 else None
            if key in self._entries:
                self._entries[key] = CacheEntry(value=value, expires_at=expires_at)
                self._entries.move_to_end(key)
                return
            if self._bounded() and len(self._entries) >= self._max_size:
                self._entries.popitem(last=False)
                self._evictions += 1
            self._entries[key] = CacheEntry(value=value, expires_at=expires_at)

    def set_default_ttl(self, key: str, value: CacheableValue) -> None:
        """Store ``value`` using the provider-level ``default_ttl``."""
        self.set(key, value, ttl=self._default_ttl)

    def delete(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def contains(self, key: str) -> bool:
        """Return whether ``key`` holds a live (non-expired) entry.

        Does not update recency or stats. Expired entries are removed lazily.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return False
            if self._is_expired(entry):
                del self._entries[key]
                self._expirations += 1
                return False
            return True

    def cleanup(self) -> int:
        """Remove all expired entries; return the number removed."""
        with self._lock:
            now = time.monotonic()
            expired = [
                key for key, entry in self._entries.items() if entry.expires_at is not None and entry.expires_at <= now
            ]
            for key in expired:
                del self._entries[key]
            self._expirations += len(expired)
            return len(expired)

    def stats(self) -> CacheStats:
        with self._lock:
            return CacheStats(
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                expirations=self._expirations,
                size=len(self._entries),
                max_size=self._max_size,
            )

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def _is_expired(self, entry: CacheEntry) -> bool:
        return entry.expires_at is not None and entry.expires_at <= time.monotonic()

    def _bounded(self) -> bool:
        return self._max_size > 0
