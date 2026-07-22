from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

import numpy as np


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class LRUCache:
    def __init__(self, max_size: int = 10000, name: str = ""):
        self.max_size = max_size
        self.name = name
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)
                    self._evictions += 1
            self._cache[key] = value

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            if key not in self._cache:
                raise KeyError(key)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.put(key, value)

    def __delitem__(self, key: str) -> None:
        with self._lock:
            del self._cache[key]

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def remove(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._cache

    def stats(self) -> CacheStats:
        with self._lock:
            return CacheStats(
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                size=len(self._cache),
                max_size=self.max_size,
            )


class CacheManager:
    def __init__(self) -> None:
        self.embedding_cache = LRUCache(max_size=10000, name="embedding")
        self.preprocessing_cache = LRUCache(max_size=5000, name="preprocessing")
        self.semantic_representation_cache = LRUCache(max_size=500, name="semantic_rep")
        self.linguistic_profile_cache = LRUCache(max_size=500, name="linguistic_profile")
        self.perception_cache = LRUCache(max_size=500, name="perception")
        self.sentence_transformer_cache: dict[str, Any] = {}
        self._st_cache_lock = threading.RLock()
        self._model_cache: LRUCache = LRUCache(max_size=50, name="model_services")
        self._model_cache_lock = threading.RLock()

    def get_model(self, key: str) -> Any | None:
        with self._model_cache_lock:
            return self._model_cache.get(key)

    def set_model(self, key: str, value: Any) -> None:
        with self._model_cache_lock:
            self._model_cache.put(key, value)

    def clear_models(self) -> None:
        with self._model_cache_lock:
            self._model_cache.clear()

    def get_st_model(self, model_name: str) -> Any | None:
        with self._st_cache_lock:
            return self.sentence_transformer_cache.get(model_name)

    def set_st_model(self, model_name: str, model: Any) -> None:
        with self._st_cache_lock:
            self.sentence_transformer_cache[model_name] = model

    def clear_st_models(self) -> None:
        with self._st_cache_lock:
            self.sentence_transformer_cache.clear()

    def clear_all(self) -> None:
        self.clear_models()
        self.clear_st_models()
        self.embedding_cache.clear()
        self.preprocessing_cache.clear()
        self.semantic_representation_cache.clear()
        self.linguistic_profile_cache.clear()
        self.perception_cache.clear()

    def stats(self) -> dict[str, CacheStats]:
        return {
            "embedding": self.embedding_cache.stats(),
            "preprocessing": self.preprocessing_cache.stats(),
            "semantic_representation": self.semantic_representation_cache.stats(),
            "linguistic_profile": self.linguistic_profile_cache.stats(),
            "perception": self.perception_cache.stats(),
            "st_models": CacheStats(
                size=len(self.sentence_transformer_cache),
                max_size=0,
            ),
            "model_services": self._model_cache.stats(),
        }


_cache_manager = CacheManager()


def get_cache() -> CacheManager:
    return _cache_manager


def embedding_cache_key(model_name: str, text: str) -> str:
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    return f"{model_name}:{text_hash}"


def cached_embedding(model_name: str, text: str, compute_fn: Callable[[], np.ndarray]) -> np.ndarray:
    cm = get_cache()
    key = embedding_cache_key(model_name, text)
    cached = cm.embedding_cache.get(key)
    if cached is not None:
        return cast(np.ndarray, cached)
    result = compute_fn()
    cm.embedding_cache.put(key, result)
    return result


def cached_preprocessing(text: str, compute_fn: Callable[[], str]) -> str:
    cm = get_cache()
    cached = cm.preprocessing_cache.get(text)
    if cached is not None:
        return str(cached)
    result = compute_fn()
    cm.preprocessing_cache.put(text, result)
    return result


def cached_perception(text: str, compute_fn: Callable) -> Any:
    cm = get_cache()
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    key = f"perception:{text_hash}"
    cached = cm.perception_cache.get(key)
    if cached is not None:
        return cached
    result = compute_fn()
    cm.perception_cache.put(key, result)
    return result


def cached_linguistic_profile(text: str, compute_fn: Callable) -> Any:
    cm = get_cache()
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    key = f"ling_profile:{text_hash}"
    cached = cm.linguistic_profile_cache.get(key)
    if cached is not None:
        return cached
    result = compute_fn()
    cm.linguistic_profile_cache.put(key, result)
    return result


def cached_semantic_representation(text: str, compute_fn: Callable) -> Any:
    cm = get_cache()
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    key = f"sem_rep:{text_hash}"
    cached = cm.semantic_representation_cache.get(key)
    if cached is not None:
        return cached
    result = compute_fn()
    cm.semantic_representation_cache.put(key, result)
    return result
