"""Performance Optimization — caching, batching, and memoization for fast inference.

Features:
- Embedding cache with LRU eviction
- Batch sentence encoding
- Preprocessing memoization
- Model loading optimization
- Concurrent request handling
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from functools import wraps
from typing import Any

import numpy as np

try:
    from sentence_transformers import CrossEncoder, SentenceTransformer

    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False


@dataclass
class CacheStats:
    """Cache performance statistics."""

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
    """Thread-safe LRU cache with size limit."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=max_size)

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._stats.hits += 1
                return self._cache[key]
            self._stats.misses += 1
            return None

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)
                    self._stats.evictions += 1
            self._cache[key] = value
            self._stats.size = len(self._cache)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats(max_size=self.max_size)

    def stats(self) -> CacheStats:
        with self._lock:
            self._stats.size = len(self._cache)
            return self._stats

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._cache


class EmbeddingCache:
    """Specialized cache for sentence embeddings."""

    def __init__(self, max_size: int = 5000):
        self._cache = LRUCache(max_size)
        self._model_cache: dict[str, Any] = {}
        self._model_lock = threading.RLock()

    def _make_key(self, model_name: str, text: str, normalize: bool = True) -> str:
        """Create cache key from model name and text hash."""
        text_hash = hashlib.md5(text.encode()).hexdigest()[:16]
        return f"{model_name}:{text_hash}:{int(normalize)}"

    def get_embedding(
        self,
        model_name: str,
        text: str,
        normalize: bool = True,
    ) -> np.ndarray | None:
        """Get cached embedding if available."""
        key = self._make_key(model_name, text, normalize)
        return self._cache.get(key)

    def put_embedding(
        self,
        model_name: str,
        text: str,
        embedding: np.ndarray,
        normalize: bool = True,
    ) -> None:
        """Cache an embedding."""
        key = self._make_key(model_name, text, normalize)
        # Ensure contiguous array for efficient storage
        self._cache.put(key, np.ascontiguousarray(embedding))

    def get_model(self, model_name: str) -> Any:
        """Get or load a sentence-transformers model."""
        with self._model_lock:
            if model_name not in self._model_cache:
                if not _ST_AVAILABLE:
                    raise RuntimeError("sentence-transformers not installed")
                if "cross-encoder" in model_name.lower() or "nli" in model_name.lower():
                    self._model_cache[model_name] = CrossEncoder(model_name, device="cpu")
                else:
                    self._model_cache[model_name] = SentenceTransformer(model_name, device="cpu")
            return self._model_cache[model_name]

    def encode_batch(
        self,
        model_name: str,
        texts: list[str],
        normalize: bool = True,
        batch_size: int = 32,
    ) -> np.ndarray:
        """Batch encode texts with caching."""
        model = self.get_model(model_name)

        # Check cache for each text
        embeddings = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            cached = self.get_embedding(model_name, text, normalize)
            if cached is not None:
                embeddings.append(cached)
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Encode uncached texts in batch
        if uncached_texts:
            new_embeddings = model.encode(
                uncached_texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=False,
            )

            # Cache and fill in
            for idx, text, emb in zip(uncached_indices, uncached_texts, new_embeddings, strict=False):
                self.put_embedding(model_name, text, emb, normalize)
                embeddings[idx] = emb

        return np.array(embeddings)

    def stats(self) -> CacheStats:
        return self._cache.stats()

    def clear(self) -> None:
        self._cache.clear()


class PreprocessingCache:
    """Cache for preprocessing results."""

    def __init__(self, max_size: int = 10000):
        self._cache = LRUCache(max_size)

    def get(self, text: str, **kwargs) -> str | None:
        """Get cached preprocessing result."""
        key = self._make_key(text, kwargs)
        return self._cache.get(key)

    def put(self, text: str, result: str, **kwargs) -> None:
        """Cache preprocessing result."""
        key = self._make_key(text, kwargs)
        self._cache.put(key, result)

    def _make_key(self, text: str, kwargs: dict) -> str:
        """Create cache key from text and preprocessing options."""
        # Hash text + options
        options_str = "".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        content = f"{text}|{options_str}"
        return hashlib.md5(content.encode()).hexdigest()

    def stats(self) -> CacheStats:
        return self._cache.stats()


class ModelLoader:
    """Optimized model loading with lazy initialization."""

    def __init__(self):
        self._models: dict[str, Any] = {}
        self._load_times: dict[str, float] = {}
        self._lock = threading.RLock()

    def get_model(
        self,
        model_name: str,
        loader_fn: Callable[[], Any],
    ) -> Any:
        """Get model, loading lazily if needed."""
        with self._lock:
            if model_name not in self._models:
                start = time.time()
                self._models[model_name] = loader_fn()
                self._load_times[model_name] = time.time() - start
            return self._models[model_name]

    def preload(self, model_configs: dict[str, Callable]) -> None:
        """Preload multiple models in background."""
        for name, loader in model_configs.items():
            if name not in self._models:
                self.get_model(name, loader)

    def get_load_time(self, model_name: str) -> float:
        return self._load_times.get(model_name, 0.0)

    def unload(self, model_name: str) -> None:
        with self._lock:
            if model_name in self._models:
                del self._models[model_name]
                if model_name in self._load_times:
                    del self._load_times[model_name]


class BatchProcessor:
    """Process requests in batches for efficiency."""

    def __init__(
        self,
        process_fn: Callable[[list[tuple[str, str]]], list[Any]],
        max_batch_size: int = 32,
        max_wait_ms: int = 50,
    ):
        self.process_fn = process_fn
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self._queue: list[tuple[tuple[str, str], threading.Event, list]] = []
        self._lock = threading.Lock()
        self._worker_thread: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        """Start batch worker thread."""
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def stop(self) -> None:
        """Stop batch worker."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=1.0)

    def process(self, q1: str, q2: str) -> Any:
        """Submit request for batch processing."""
        event = threading.Event()
        result_holder: list[Any] = [None]

        with self._lock:
            self._queue.append(((q1, q2), event, result_holder))
            if len(self._queue) >= self.max_batch_size:
                # Signal worker to process immediately
                pass

        event.wait(timeout=self.max_wait_ms / 1000 + 1.0)
        return result_holder[0]

    def _worker(self) -> None:
        while self._running:
            batch = []
            with self._lock:
                if self._queue:
                    batch = self._queue[: self.max_batch_size]
                    self._queue = self._queue[self.max_batch_size :]

            if batch:
                pairs = [item[0] for item in batch]
                try:
                    results = self.process_fn(pairs)
                    for (_, event, holder), result in zip(batch, results, strict=False):
                        holder[0] = result
                        event.set()
                except Exception as e:
                    for _, event, holder in batch:
                        holder[0] = e
                        event.set()
            else:
                time.sleep(self.max_wait_ms / 1000)


# Global instances
_embedding_cache = EmbeddingCache(max_size=10000)
_preprocessing_cache = PreprocessingCache(max_size=10000)
_model_loader = ModelLoader()
_batch_processors: dict[str, BatchProcessor] = {}


def get_embedding_cache() -> EmbeddingCache:
    return _embedding_cache


def get_preprocessing_cache() -> PreprocessingCache:
    return _preprocessing_cache


def get_model_loader() -> ModelLoader:
    return _model_loader


def cached_normalize(text: str, **kwargs) -> str:
    """Normalize with caching."""
    cached = _preprocessing_cache.get(text, **kwargs)
    if cached is not None:
        return cached

    from duplicate_question_app.preprocessing import normalize_question

    result = normalize_question(text, **kwargs)
    _preprocessing_cache.put(text, result, **kwargs)
    return result


def memoize(maxsize: int = 128):
    """Memoization decorator with LRU cache."""

    def decorator(func: Callable) -> Callable:
        cache = LRUCache(maxsize)

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = hashlib.md5(f"{args}|{kwargs}".encode()).hexdigest()
            cached = cache.get(key)
            if cached is not None:
                return cached
            result = func(*args, **kwargs)
            cache.put(key, result)
            return result

        wrapper.cache = cache
        return wrapper

    return decorator


@contextmanager
def performance_monitor():
    """Context manager for timing operations."""
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start


class InferenceOptimizer:
    """Main class for optimized inference pipeline."""

    def __init__(self, paths: Any = None):
        self.paths = paths
        self.embedding_cache = _embedding_cache
        self.preprocessing_cache = _preprocessing_cache
        self.model_loader = _model_loader

    def predict_single_optimized(
        self,
        q1: str,
        q2: str,
        model_name: str,
    ) -> dict[str, Any]:
        """Optimized single prediction with all caching."""
        start = time.perf_counter()

        # Cached preprocessing
        q1_norm = cached_normalize(q1, expand_abbrevs=True)
        q2_norm = cached_normalize(q2, expand_abbrevs=True)

        preprocess_time = time.perf_counter() - start

        # Get model
        if "cross-encoder" in model_name.lower() or "nli" in model_name.lower():
            model = self.embedding_cache.get_model(model_name)
            scores = model.predict([(q1_norm, q2_norm)], apply_softmax=True)[0]
            # Convert NLI scores to duplicate probability
            if len(scores) >= 3:
                contra, entail = float(scores[0]), float(scores[2])
                prob_dup = entail / (contra + entail) if (contra + entail) > 0.01 else 0.5
            else:
                prob_dup = float(scores[0])
        else:
            model = self.embedding_cache.get_model(model_name)
            # Batch encode both texts
            embeddings = self.embedding_cache.encode_batch(model_name, [q1_norm, q2_norm])
            prob_dup = float(np.dot(embeddings[0], embeddings[1]))

            # Apply model-specific calibration
            prob_dup = self._calibrate_prob(model_name, prob_dup)

        inference_time = time.perf_counter() - start - preprocess_time

        return {
            "question1": q1_norm,
            "question2": q2_norm,
            "prob_duplicate": prob_dup,
            "prob_non_duplicate": 1.0 - prob_dup,
            "predicted_label": 1 if prob_dup >= 0.5 else 0,
            "prediction": "Duplicate" if prob_dup >= 0.5 else "Non-Duplicate",
            "confidence": max(prob_dup, 1.0 - prob_dup),
            "threshold": 0.5,
            "latency_ms": (time.perf_counter() - start) * 1000,
            "preprocess_ms": preprocess_time * 1000,
            "inference_ms": inference_time * 1000,
        }

    def _calibrate_prob(self, model_name: str, prob: float) -> float:
        """Apply model-specific calibration."""
        name = model_name.lower()
        if "e5" in name:
            steepness, midpoint = 18.0, 0.72
        elif "bge" in name:
            steepness, midpoint = 14.0, 0.60
        elif "mpnet" in name:
            steepness, midpoint = 14.0, 0.58
        else:
            steepness, midpoint = 15.0, 0.50
        return 1.0 / (1.0 + np.exp(-steepness * (prob - midpoint)))

    def predict_batch_optimized(
        self,
        pairs: list[tuple[str, str]],
        model_name: str,
        batch_size: int = 32,
    ) -> list[dict[str, Any]]:
        """Optimized batch prediction."""
        start = time.perf_counter()

        # Cached preprocessing
        q1_list = [cached_normalize(q1, expand_abbrevs=True) for q1, _ in pairs]
        q2_list = [cached_normalize(q2, expand_abbrevs=True) for _, q2 in pairs]

        preprocess_time = time.perf_counter() - start

        # Get model
        self.embedding_cache.get_model(model_name)

        # Batch encode all texts
        all_texts = q1_list + q2_list
        embeddings = self.embedding_cache.encode_batch(model_name, all_texts, batch_size=batch_size)

        q1_embs = embeddings[: len(pairs)]
        q2_embs = embeddings[len(pairs) :]

        # Compute similarities
        similarities = np.sum(q1_embs * q2_embs, axis=1)
        probs = np.array([self._calibrate_prob(model_name, s) for s in similarities])

        inference_time = time.perf_counter() - start - preprocess_time

        results = []
        for i, (q1, q2) in enumerate(zip(q1_list, q2_list, strict=False)):
            prob_dup = float(probs[i])
            results.append(
                {
                    "question1": q1,
                    "question2": q2,
                    "prob_duplicate": prob_dup,
                    "prob_non_duplicate": 1.0 - prob_dup,
                    "predicted_label": 1 if prob_dup >= 0.5 else 0,
                    "prediction": "Duplicate" if prob_dup >= 0.5 else "Non-Duplicate",
                    "confidence": max(prob_dup, 1.0 - prob_dup),
                    "threshold": 0.5,
                }
            )

        total_time = (time.perf_counter() - start) * 1000
        for r in results:
            r["latency_ms"] = total_time / len(results)
            r["preprocess_ms"] = (preprocess_time * 1000) / len(results)
            r["inference_ms"] = (inference_time * 1000) / len(results)

        return results

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics."""
        return {
            "embedding_cache": self.embedding_cache.stats().__dict__,
            "preprocessing_cache": self.preprocessing_cache.stats().__dict__,
            "loaded_models": list(self.model_loader._models.keys()),
            "model_load_times": self.model_loader._load_times,
        }


def clear_all_caches():
    """Clear all global caches."""
    _embedding_cache.clear()
    _preprocessing_cache.clear()
    _model_loader._models.clear()
    _model_loader._load_times.clear()


def warmup_caches(
    sample_pairs: list[tuple[str, str]],
    model_names: list[str],
) -> None:
    """Warm up caches with sample data."""
    optimizer = InferenceOptimizer()

    # Preload models
    for model_name in model_names:
        if "cross-encoder" in model_name.lower() or "nli" in model_name.lower():
            _model_loader.get_model(model_name, lambda m=model_name: CrossEncoder(m, device="cpu"))
        else:
            _model_loader.get_model(model_name, lambda m=model_name: SentenceTransformer(m, device="cpu"))

    # Run sample predictions to populate caches
    for q1, q2 in sample_pairs[:10]:
        for model_name in model_names:
            with suppress(Exception):
                optimizer.predict_single_optimized(q1, q2, model_name)


def benchmark_inference(
    pairs: list[tuple[str, str]],
    model_names: list[str],
    iterations: int = 3,
) -> dict[str, dict[str, float]]:
    """Benchmark inference performance."""
    optimizer = InferenceOptimizer()
    results = {}

    for model_name in model_names:
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            for q1, q2 in pairs:
                optimizer.predict_single_optimized(q1, q2, model_name)
            times.append(time.perf_counter() - start)

        results[model_name] = {
            "mean_ms": np.mean(times) * 1000,
            "std_ms": np.std(times) * 1000,
            "min_ms": np.min(times) * 1000,
            "max_ms": np.max(times) * 1000,
            "per_pair_ms": np.mean(times) * 1000 / len(pairs),
        }

    return results
