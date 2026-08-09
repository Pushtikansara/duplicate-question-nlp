from __future__ import annotations

import pytest

from ares.orchestration.config import EngineConfiguration
from ares.orchestration.exceptions import (
    CacheError,
    InputValidationError,
    ModelTimeoutError,
    ModelUnavailableError,
    RunCancelledError,
    TaskExecutionError,
)
from ares.orchestration.policies import DefaultFallbackPolicy, DefaultRetryPolicy


class TestDefaultRetryPolicy:
    def test_retries_transient_errors(self) -> None:
        policy = DefaultRetryPolicy(max_attempts=3, backoff_ms=0)
        assert policy.should_retry(1, TaskExecutionError("boom")) is True
        assert policy.should_retry(2, ModelUnavailableError("unavailable")) is True
        assert policy.should_retry(3, ModelTimeoutError("timeout")) is False

    def test_retries_plain_exceptions(self) -> None:
        policy = DefaultRetryPolicy(max_attempts=2, backoff_ms=0)
        assert policy.should_retry(1, ValueError("boom")) is True

    def test_non_retryable_errors(self) -> None:
        policy = DefaultRetryPolicy(max_attempts=3, backoff_ms=0)
        assert policy.should_retry(1, InputValidationError("bad")) is False
        assert policy.should_retry(1, RunCancelledError("cancelled")) is False
        assert policy.should_retry(1, CacheError("cache down")) is False

    def test_disabled_policy_never_retries(self) -> None:
        policy = DefaultRetryPolicy(enabled=False, max_attempts=3, backoff_ms=0)
        assert policy.should_retry(1, TaskExecutionError("boom")) is False

    def test_backoff_scales_with_attempt(self) -> None:
        policy = DefaultRetryPolicy(max_attempts=3, backoff_ms=100)
        assert policy.get_backoff(1) == pytest.approx(0.1)
        assert policy.get_backoff(2) == pytest.approx(0.2)

    def test_zero_backoff_when_zero_ms(self) -> None:
        policy = DefaultRetryPolicy(max_attempts=2, backoff_ms=0)
        assert policy.get_backoff(1) == 0.0

    def test_custom_retryable_set(self) -> None:
        policy = DefaultRetryPolicy(
            max_attempts=3,
            backoff_ms=0,
            retryable_exceptions=(ModelUnavailableError,),
        )
        assert policy.should_retry(1, ModelUnavailableError("unavailable")) is True
        assert policy.should_retry(1, ValueError("other")) is False


class TestDefaultFallbackPolicy:
    def test_returns_fallback_config(self) -> None:
        policy = DefaultFallbackPolicy(
            enabled=True,
            fallback_model="Improved DistilBERT (Week 4)",
            threshold=0.6,
            use_reflection=False,
        )
        config = policy.get_fallback_config()
        assert isinstance(config, EngineConfiguration)
        assert config.model_name == "Improved DistilBERT (Week 4)"
        assert config.threshold == 0.6
        assert config.use_reflection is False
        assert config.use_semantic_validation is True

    def test_default_config(self) -> None:
        policy = DefaultFallbackPolicy()
        config = policy.get_fallback_config()
        assert config.model_name == "Improved DistilBERT (Week 4)"
        assert config.threshold == 0.5
