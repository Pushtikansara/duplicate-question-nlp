from __future__ import annotations

from dataclasses import dataclass, field

from ares.orchestration.constants import (
    DEFAULT_BATCH_MAX_PAIRS,
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_EXECUTION_MODE,
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_RETRY_BACKOFF_MS,
    DEFAULT_RETRY_MAX_ATTEMPTS,
    DEFAULT_THRESHOLD,
)


@dataclass(frozen=True)
class EngineConfiguration:
    model_name: str
    threshold: float = DEFAULT_THRESHOLD
    use_reflection: bool = True
    use_semantic_validation: bool = True


@dataclass(frozen=True)
class OrchestrationConfiguration:
    cache_enabled: bool = True
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS
    cache_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES
    retry_enabled: bool = True
    retry_max_attempts: int = DEFAULT_RETRY_MAX_ATTEMPTS
    retry_backoff_ms: int = DEFAULT_RETRY_BACKOFF_MS
    fallback_enabled: bool = True
    fallback_model: str = DEFAULT_FALLBACK_MODEL
    execution_mode: str = DEFAULT_EXECUTION_MODE
    fail_on_hook_error: bool = False
    enable_pre_hooks: bool = True
    enable_post_hooks: bool = True
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY
    batch_max_pairs: int = DEFAULT_BATCH_MAX_PAIRS
    default_strategies: tuple[str, ...] = field(
        default_factory=lambda: (
            "fast_lexical",
            "baseline_classifier",
            "cross_encoder",
            "ensemble",
            "fallback",
        )
    )
