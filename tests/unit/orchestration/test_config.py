from __future__ import annotations

import dataclasses

import pytest

from ares.orchestration.config import EngineConfiguration, OrchestrationConfiguration
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


class TestEngineConfiguration:
    def test_required_fields(self):
        config = EngineConfiguration(model_name="test_model")
        assert config.model_name == "test_model"

    def test_defaults(self):
        config = EngineConfiguration(model_name="test")
        assert config.threshold == DEFAULT_THRESHOLD
        assert config.use_reflection is True
        assert config.use_semantic_validation is True

    def test_custom_values(self):
        config = EngineConfiguration(
            model_name="custom",
            threshold=0.9,
            use_reflection=False,
            use_semantic_validation=False,
        )
        assert config.model_name == "custom"
        assert config.threshold == 0.9
        assert config.use_reflection is False
        assert config.use_semantic_validation is False

    def test_immutable(self):
        config = EngineConfiguration(model_name="test")
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.model_name = "new_name"

    def test_equality(self):
        c1 = EngineConfiguration(model_name="a", threshold=0.5)
        c2 = EngineConfiguration(model_name="a", threshold=0.5)
        assert c1 == c2

    def test_hashable(self):
        c1 = EngineConfiguration(model_name="a")
        s = {c1}
        c2 = EngineConfiguration(model_name="a")
        s.add(c2)
        assert len(s) == 1
        c3 = EngineConfiguration(model_name="b")
        s.add(c3)
        assert len(s) == 2


class TestOrchestrationConfiguration:
    def test_defaults(self):
        config = OrchestrationConfiguration()
        assert config.cache_enabled is True
        assert config.cache_ttl_seconds == DEFAULT_CACHE_TTL_SECONDS
        assert config.cache_max_entries == DEFAULT_CACHE_MAX_ENTRIES
        assert config.retry_enabled is True
        assert config.retry_max_attempts == DEFAULT_RETRY_MAX_ATTEMPTS
        assert config.retry_backoff_ms == DEFAULT_RETRY_BACKOFF_MS
        assert config.fallback_enabled is True
        assert config.fallback_model == DEFAULT_FALLBACK_MODEL
        assert config.execution_mode == DEFAULT_EXECUTION_MODE
        assert config.fail_on_hook_error is False
        assert config.enable_pre_hooks is True
        assert config.enable_post_hooks is True
        assert config.max_concurrency == DEFAULT_MAX_CONCURRENCY
        assert config.batch_max_pairs == DEFAULT_BATCH_MAX_PAIRS
        assert len(config.default_strategies) == 5

    def test_custom_values(self):
        config = OrchestrationConfiguration(
            cache_enabled=False,
            cache_ttl_seconds=600,
            retry_enabled=False,
            fallback_model="custom_model",
            execution_mode="async",
            fail_on_hook_error=True,
            max_concurrency=8,
            batch_max_pairs=100,
        )
        assert config.cache_enabled is False
        assert config.cache_ttl_seconds == 600
        assert config.retry_enabled is False
        assert config.fallback_model == "custom_model"
        assert config.execution_mode == "async"
        assert config.fail_on_hook_error is True
        assert config.max_concurrency == 8
        assert config.batch_max_pairs == 100

    def test_immutable(self):
        config = OrchestrationConfiguration()
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.cache_enabled = False

    def test_strategy_defaults_are_tuple(self):
        config = OrchestrationConfiguration()
        assert isinstance(config.default_strategies, tuple)
        assert "fast_lexical" in config.default_strategies
        assert "fallback" in config.default_strategies

    def test_disabled_retry(self):
        config = OrchestrationConfiguration(retry_enabled=False, retry_max_attempts=0)
        assert config.retry_enabled is False
        assert config.retry_max_attempts == 0

    def test_disabled_fallback(self):
        config = OrchestrationConfiguration(fallback_enabled=False)
        assert config.fallback_enabled is False


class TestConfigValidation:
    def test_engine_config_no_model_raises(self):
        with pytest.raises(TypeError):
            EngineConfiguration()

    def test_orchestration_config_no_args_ok(self):
        config = OrchestrationConfiguration()
        assert isinstance(config, OrchestrationConfiguration)

    def test_all_fields_typed(self):
        fields = dataclasses.fields(OrchestrationConfiguration)
        for f in fields:
            assert f.type is not None, f"Field {f.name} has no type annotation"


class TestPublicApi:
    def test_config_classes_exported(self):
        from ares.orchestration import EngineConfiguration, OrchestrationConfiguration

        assert EngineConfiguration is not None
        assert OrchestrationConfiguration is not None
