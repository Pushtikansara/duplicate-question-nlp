"""Unified Cache Manager — re-exports from canonical location.

Consolidates all caching concerns into a single source of truth.
The canonical implementation lives in src/duplicate_question_app/_inference/cache.py.
"""

from duplicate_question_app._inference.cache import (  # noqa: F401
    CacheManager,
    CacheStats,
    LRUCache,
    cached_embedding,
    cached_preprocessing,
    embedding_cache_key,
    get_cache,
)
