from __future__ import annotations

from ares.orchestration.config import EngineConfiguration
from ares.orchestration.constants import (
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_RETRY_BACKOFF_MS,
    DEFAULT_RETRY_MAX_ATTEMPTS,
    DEFAULT_THRESHOLD,
)
from ares.orchestration.exceptions import (
    CacheError,
    InputValidationError,
    InvalidStageConfigurationError,
    RunCancelledError,
    RunTimeoutError,
    StageDependencyError,
)


class DefaultRetryPolicy:
    """Retry policy backing the Phase 13.1 ``RetryPolicy`` protocol.

    ``max_attempts`` is the total number of attempts (first attempt plus
    retries). Backoff is ``backoff_ms * attempt`` milliseconds of sleep.
    Input validation, cancellation, timeout and configuration errors are
    never retried by default; the retryable set is overridable.
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
        max_attempts: int = DEFAULT_RETRY_MAX_ATTEMPTS,
        backoff_ms: int = DEFAULT_RETRY_BACKOFF_MS,
        retryable_exceptions: tuple[type[Exception], ...] | None = None,
    ) -> None:
        self.enabled = enabled
        self.max_attempts = max_attempts
        self.backoff_ms = backoff_ms
        self.retryable_exceptions = retryable_exceptions or self._default_retryable()

    @staticmethod
    def _default_retryable() -> tuple[type[Exception], ...]:
        return (Exception,)

    @staticmethod
    def _non_retryable() -> tuple[type[Exception], ...]:
        return (
            InputValidationError,
            RunCancelledError,
            RunTimeoutError,
            CacheError,
            InvalidStageConfigurationError,
            StageDependencyError,
        )

    def should_retry(self, attempt: int, error: Exception) -> bool:
        if not self.enabled or attempt >= self.max_attempts:
            return False
        for non_retryable in self._non_retryable():
            if isinstance(error, non_retryable):
                return False
        return isinstance(error, self.retryable_exceptions)

    def get_backoff(self, attempt: int) -> float:
        return (self.backoff_ms * max(attempt, 1)) / 1000.0


class DefaultFallbackPolicy:
    """Fallback policy backing the Phase 13.1 ``FallbackPolicy`` protocol.

    Supplies the engine configuration used when the selected strategy fails
    and ``fallback_enabled`` is set. The fallback model can point to the
    default engine model.
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
        fallback_model: str = DEFAULT_FALLBACK_MODEL,
        threshold: float = DEFAULT_THRESHOLD,
        use_reflection: bool = True,
    ) -> None:
        self.enabled = enabled
        self.fallback_model = fallback_model
        self.threshold = threshold
        self.use_reflection = use_reflection

    def get_fallback_config(self) -> EngineConfiguration:
        return EngineConfiguration(
            model_name=self.fallback_model,
            threshold=self.threshold,
            use_reflection=self.use_reflection,
            use_semantic_validation=True,
        )
