from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import pytest

from ares.orchestration import CacheProvider, InMemoryCacheProvider
from ares.orchestration.cache import CacheStats, _is_cacheable
from ares.orchestration.cache_key import build_query_understanding_cache_key
from ares.orchestration.exceptions import CacheError


@dataclass
class FakeAnalysis:
    question1: str = ""
    question2: str = ""


class TestCacheableValues:
    def test_primitives_are_cacheable(self):
        for value in [None, "text", b"bytes", 42, 3.14, True, False]:
            assert _is_cacheable(value) is True

    def test_dataclass_is_cacheable(self):
        assert _is_cacheable(FakeAnalysis(question1="a", question2="b")) is True

    def test_containers_of_cacheable(self):
        assert _is_cacheable({"k": [1, 2, ("a", b"b", None, True)]}) is True
        assert _is_cacheable([FakeAnalysis(), {"nested": {"deep": "v"}}]) is True
        assert _is_cacheable({1, 2, 3}) is True
        assert _is_cacheable(frozenset({"a", "b"})) is True

    def test_unsafe_objects_not_cacheable(self):
        assert _is_cacheable(threading.Lock()) is False
        assert _is_cacheable(x for x in range(3)) is False
        assert _is_cacheable(threading) is False
        assert _is_cacheable({"lock": threading.Lock()}) is False


class TestBasicOperations:
    def test_set_get(self):
        cache = InMemoryCacheProvider()
        cache.set("k", {"value": 1}, ttl=0)
        assert cache.get("k") == {"value": 1}

    def test_get_missing_returns_none(self):
        cache = InMemoryCacheProvider()
        assert cache.get("missing") is None

    def test_get_missing_counts_miss(self):
        cache = InMemoryCacheProvider()
        cache.get("missing")
        stats = cache.stats()
        assert stats.misses == 1
        assert stats.hits == 0

    def test_overwrite(self):
        cache = InMemoryCacheProvider()
        cache.set("k", "first", ttl=0)
        cache.set("k", "second", ttl=0)
        assert cache.get("k") == "second"
        assert len(cache) == 1

    def test_delete(self):
        cache = InMemoryCacheProvider()
        cache.set("k", "v", ttl=0)
        cache.delete("k")
        assert cache.get("k") is None

    def test_delete_missing_is_noop(self):
        cache = InMemoryCacheProvider()
        cache.delete("missing")

    def test_clear(self):
        cache = InMemoryCacheProvider()
        cache.set("a", 1, ttl=0)
        cache.set("b", 2, ttl=0)
        cache.clear()
        assert len(cache) == 0
        assert cache.get("a") is None

    def test_contains(self):
        cache = InMemoryCacheProvider()
        assert cache.contains("k") is False
        cache.set("k", "v", ttl=0)
        assert cache.contains("k") is True
        cache.delete("k")
        assert cache.contains("k") is False

    def test_none_value_contract(self):
        cache = InMemoryCacheProvider()
        cache.set("k", None, ttl=0)
        assert cache.get("k") is None
        assert cache.contains("k") is True

    def test_unicode_and_punctuation_keys(self):
        cache = InMemoryCacheProvider()
        cache.set("qué pasa? 日本", "v", ttl=0)
        cache.set("a!b@c#d", "v2", ttl=0)
        assert cache.get("qué pasa? 日本") == "v"
        assert cache.get("a!b@c#d") == "v2"

    def test_long_string_key_and_value(self):
        cache = InMemoryCacheProvider()
        long_text = "x" * 100_000
        cache.set(long_text, long_text, ttl=0)
        assert cache.get(long_text) == long_text


class TestTtl:
    def test_expiration(self):
        cache = InMemoryCacheProvider()
        cache.set("k", "v", ttl=0.05)
        assert cache.get("k") == "v"
        time.sleep(0.1)
        assert cache.get("k") is None

    def test_expiration_counts_expirations(self):
        cache = InMemoryCacheProvider()
        cache.set("k", "v", ttl=0.05)
        time.sleep(0.1)
        cache.get("k")
        assert cache.stats().expirations == 1

    def test_ttl_zero_never_expires(self):
        cache = InMemoryCacheProvider()
        cache.set("k", "v", ttl=0)
        time.sleep(0.1)
        assert cache.get("k") == "v"
        assert cache.stats().expirations == 0

    def test_ttl_negative_raises(self):
        cache = InMemoryCacheProvider()
        with pytest.raises(CacheError):
            cache.set("k", "v", ttl=-1)

    def test_default_ttl_applies(self):
        cache = InMemoryCacheProvider(default_ttl=0)
        cache.set_default_ttl("k", "v")
        assert cache.get("k") == "v"

    def test_contains_expired(self):
        cache = InMemoryCacheProvider()
        cache.set("k", "v", ttl=0.05)
        time.sleep(0.1)
        assert cache.contains("k") is False

    def test_cleanup_removes_expired(self):
        cache = InMemoryCacheProvider()
        cache.set("expired", "v", ttl=0.05)
        cache.set("alive", "v", ttl=0)
        time.sleep(0.1)
        removed = cache.cleanup()
        assert removed == 1
        assert cache.contains("alive") is True
        assert cache.contains("expired") is False
        assert cache.stats().expirations == 1


class TestLru:
    def test_eviction_at_capacity(self):
        cache = InMemoryCacheProvider(max_size=2)
        cache.set("a", 1, ttl=0)
        cache.set("b", 2, ttl=0)
        cache.set("c", 3, ttl=0)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_get_updates_recency(self):
        cache = InMemoryCacheProvider(max_size=2)
        cache.set("a", 1, ttl=0)
        cache.set("b", 2, ttl=0)
        cache.get("a")
        cache.set("c", 3, ttl=0)
        assert cache.get("b") is None
        assert cache.get("a") == 1

    def test_overwrite_does_not_grow(self):
        cache = InMemoryCacheProvider(max_size=1)
        cache.set("a", 1, ttl=0)
        cache.set("a", 2, ttl=0)
        assert len(cache) == 1
        assert cache.get("a") == 2

    def test_evictions_counted(self):
        cache = InMemoryCacheProvider(max_size=2)
        cache.set("a", 1, ttl=0)
        cache.set("b", 2, ttl=0)
        cache.set("c", 3, ttl=0)
        assert cache.stats().evictions == 1

    def test_zero_capacity_unbounded(self):
        cache = InMemoryCacheProvider(max_size=0)
        for i in range(100):
            cache.set(f"k{i}", i, ttl=0)
        assert len(cache) == 100
        assert cache.stats().evictions == 0

    def test_negative_capacity_unbounded(self):
        cache = InMemoryCacheProvider(max_size=-5)
        for i in range(10):
            cache.set(f"k{i}", i, ttl=0)
        assert len(cache) == 10


class TestStats:
    def test_hit_rate(self):
        cache = InMemoryCacheProvider()
        cache.set("k", "v", ttl=0)
        cache.get("k")
        cache.get("missing")
        stats = cache.stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.hit_rate == 0.5
        assert stats.size == 1
        assert stats.max_size == 1000

    def test_empty_stats(self):
        cache = InMemoryCacheProvider()
        stats = cache.stats()
        assert stats == CacheStats(hits=0, misses=0, evictions=0, expirations=0, size=0, max_size=1000)
        assert stats.hit_rate == 0.0

    def test_to_dict(self):
        cache = InMemoryCacheProvider(max_size=7)
        cache.set("k", "v", ttl=0)
        data = cache.stats().to_dict()
        assert data["size"] == 1
        assert data["max_size"] == 7
        assert "hit_rate" in data


class TestUnsafeValues:
    def test_lock_rejected(self):
        cache = InMemoryCacheProvider()
        with pytest.raises(CacheError):
            cache.set("k", threading.Lock(), ttl=0)

    def test_generator_rejected(self):
        cache = InMemoryCacheProvider()
        with pytest.raises(CacheError):
            cache.set("k", (i for i in range(3)), ttl=0)

    def test_unsafe_nested_rejected(self):
        cache = InMemoryCacheProvider()
        with pytest.raises(CacheError):
            cache.set("k", {"nested": [1, threading.Lock()]}, ttl=0)

    def test_custom_value_checker(self):
        cache = InMemoryCacheProvider(value_checker=lambda value: value != "forbidden")
        cache.set("ok", "value", ttl=0)
        with pytest.raises(CacheError):
            cache.set("bad", "forbidden", ttl=0)


class TestProtocol:
    def test_implements_cache_provider_protocol(self):
        cache = InMemoryCacheProvider()
        assert isinstance(cache, CacheProvider)


class TestThreadSafety:
    def test_concurrent_set_get_delete(self):
        cache = InMemoryCacheProvider(max_size=32)
        errors: list[Exception] = []

        def worker(worker_id: int) -> None:
            try:
                for i in range(200):
                    key = f"w{worker_id}-{i}"
                    cache.set(key, i, ttl=0)
                    cache.get(key)
                    if i % 3 == 0:
                        cache.delete(key)
            except Exception as exc:  # pragma: no cover - failure probe
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(worker, range(8)))

        assert errors == []
        assert len(cache) <= 32

    def test_concurrent_eviction(self):
        cache = InMemoryCacheProvider(max_size=16)
        errors: list[Exception] = []

        def worker(worker_id: int) -> None:
            try:
                for i in range(300):
                    cache.set(f"{worker_id}-{i}", i, ttl=0)
            except Exception as exc:  # pragma: no cover - failure probe
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(worker, range(8)))

        assert errors == []
        assert len(cache) == 16
        assert cache.stats().evictions > 0

    def test_concurrent_clear(self):
        cache = InMemoryCacheProvider(max_size=64)
        errors: list[Exception] = []

        def writer(worker_id: int) -> None:
            try:
                for i in range(100):
                    cache.set(f"w{worker_id}-{i}", i, ttl=0)
            except Exception as exc:  # pragma: no cover - failure probe
                errors.append(exc)

        def clearer() -> None:
            try:
                for _ in range(50):
                    cache.clear()
            except Exception as exc:  # pragma: no cover - failure probe
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=9) as executor:
            futures = [executor.submit(writer, i) for i in range(8)]
            futures.append(executor.submit(clearer))
            for f in futures:
                f.result()

        assert errors == []
        assert len(cache) <= 64

    def test_concurrent_get_stats(self):
        cache = InMemoryCacheProvider()
        cache.set("k", "v", ttl=0)

        def worker(_: int) -> None:
            for _ in range(500):
                cache.get("k")

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(worker, range(8)))

        assert cache.stats().hits == 4000


class TestIntegrationWithKeyBuilder:
    def test_cache_hit_after_miss(self):
        cache = InMemoryCacheProvider()
        key = build_query_understanding_cache_key("What is Python?", "What is python?")
        analysis = FakeAnalysis(question1="What is Python?", question2="What is python?")

        assert cache.get(key) is None
        cache.set(key, analysis, ttl=60)
        assert cache.get(key) == analysis
        assert cache.stats().hits == 1
        assert cache.stats().misses == 1

    def test_normalized_inputs_share_entry(self):
        cache = InMemoryCacheProvider()
        key1 = build_query_understanding_cache_key("What is  Python?", "  what is python  ")
        key2 = build_query_understanding_cache_key("What is Python?", "what is python")
        assert key1 == key2
        cache.set(key1, "cached", ttl=60)
        assert cache.get(key2) == "cached"
