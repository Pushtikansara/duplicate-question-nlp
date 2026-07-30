from __future__ import annotations

from abc import ABC
from typing import Any, Protocol

import pytest

from ares.orchestration.config import EngineConfiguration
from ares.orchestration.context import PipelineState, PredictionInput
from ares.orchestration.interfaces import (
    CacheProvider,
    EventPublisher,
    FallbackPolicy,
    MetricsCollector,
    PipelineStage,
    RetryPolicy,
    StrategyProvider,
)
from ares.orchestration.metadata import OrchestrationMetadata


class TestPipelineStage:
    def test_is_abc(self):
        assert issubclass(PipelineStage, ABC)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            PipelineStage()

    def test_concrete_implementation(self):
        class ValidStage(PipelineStage):
            @property
            def name(self) -> str:
                return "test_stage"

            def run(
                self,
                input: PredictionInput,
                state: PipelineState,
                metadata: OrchestrationMetadata,
            ) -> None:
                state.error = "ran"

        stage = ValidStage()
        assert stage.name == "test_stage"
        inp = PredictionInput(question1="q1", question2="q2")
        state = PipelineState()
        meta = OrchestrationMetadata()
        stage.run(inp, state, meta)
        assert state.error == "ran"

    def test_abstract_methods_required(self):
        class MissingRun(PipelineStage):
            @property
            def name(self) -> str:
                return "missing"

        with pytest.raises(TypeError):
            MissingRun()

        class MissingName(PipelineStage):
            def run(
                self,
                input: PredictionInput,
                state: PipelineState,
                metadata: OrchestrationMetadata,
            ) -> None:
                pass

        with pytest.raises(TypeError):
            MissingName()


class TestCacheProvider:
    def test_is_protocol(self):
        assert issubclass(CacheProvider, Protocol) and CacheProvider is not Protocol

    def test_runtime_checkable(self):
        class Impl:
            def get(self, key: str) -> Any | None:
                return None

            def set(self, key: str, value: Any, ttl: int) -> None:
                pass

            def delete(self, key: str) -> None:
                pass

            def clear(self) -> None:
                pass

        assert isinstance(Impl(), CacheProvider)

    def test_missing_method(self):
        class Partial:
            def get(self, key: str) -> Any | None:
                return None

        assert not isinstance(Partial(), CacheProvider)


class TestStrategyProvider:
    def test_is_protocol(self):
        assert issubclass(StrategyProvider, Protocol) and StrategyProvider is not Protocol

    def test_runtime_checkable(self):
        class Impl:
            def resolve(self, name: str) -> EngineConfiguration:
                return EngineConfiguration(model_name="test")

            def list_strategies(self) -> list[str]:
                return ["test"]

        assert isinstance(Impl(), StrategyProvider)

    def test_resolve_returns_engine_config(self):
        class Impl:
            def resolve(self, name: str) -> EngineConfiguration:
                return EngineConfiguration(model_name=name, threshold=0.8)

            def list_strategies(self) -> list[str]:
                return ["test"]

        result = Impl().resolve("cross_encoder")
        assert isinstance(result, EngineConfiguration)
        assert result.model_name == "cross_encoder"
        assert result.threshold == 0.8


class TestRetryPolicy:
    def test_is_protocol(self):
        assert issubclass(RetryPolicy, Protocol) and RetryPolicy is not Protocol

    def test_runtime_checkable(self):
        class Impl:
            def should_retry(self, attempt: int, error: Exception) -> bool:
                return attempt < 2

            def get_backoff(self, attempt: int) -> float:
                return 0.1

        assert isinstance(Impl(), RetryPolicy)

    def test_should_retry_contract(self):
        class Impl:
            def should_retry(self, attempt: int, error: Exception) -> bool:
                return attempt < 2

            def get_backoff(self, attempt: int) -> float:
                return float(attempt * 100) / 1000.0

        policy = Impl()
        assert policy.should_retry(0, ValueError("test")) is True
        assert policy.should_retry(2, ValueError("test")) is False
        assert policy.get_backoff(1) == 0.1
        assert policy.get_backoff(2) == 0.2


class TestFallbackPolicy:
    def test_is_protocol(self):
        assert issubclass(FallbackPolicy, Protocol) and FallbackPolicy is not Protocol

    def test_runtime_checkable(self):
        class Impl:
            def get_fallback_config(self) -> EngineConfiguration:
                return EngineConfiguration(model_name="fallback", threshold=0.5)

        assert isinstance(Impl(), FallbackPolicy)

    def test_get_fallback_config_returns_engine_config(self):
        class Impl:
            def get_fallback_config(self) -> EngineConfiguration:
                return EngineConfiguration(model_name="fallback_model", threshold=0.3, use_reflection=False)

        config = Impl().get_fallback_config()
        assert isinstance(config, EngineConfiguration)
        assert config.model_name == "fallback_model"
        assert config.threshold == 0.3
        assert config.use_reflection is False


class TestMetricsCollector:
    def test_is_protocol(self):
        assert issubclass(MetricsCollector, Protocol) and MetricsCollector is not Protocol

    def test_runtime_checkable(self):
        class Impl:
            def increment(self, metric: str, tags: dict[str, str] | None = None) -> None:
                pass

            def gauge(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None:
                pass

            def timing(self, metric: str, duration_ms: float, tags: dict[str, str] | None = None) -> None:
                pass

        assert isinstance(Impl(), MetricsCollector)

    def test_missing_method_not_checkable(self):
        class Partial:
            def increment(self, metric: str, tags: dict[str, str] | None = None) -> None:
                pass

        assert not isinstance(Partial(), MetricsCollector)


class TestEventPublisher:
    def test_is_protocol(self):
        assert issubclass(EventPublisher, Protocol) and EventPublisher is not Protocol

    def test_runtime_checkable(self):
        class Impl:
            def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
                pass

        assert isinstance(Impl(), EventPublisher)

    def test_missing_method(self):
        class Partial:
            pass

        assert not isinstance(Partial(), EventPublisher)


class TestProtocolConformance:
    def test_all_protocols_are_runtime_checkable(self):
        protocols = [CacheProvider, StrategyProvider, RetryPolicy, FallbackPolicy, MetricsCollector, EventPublisher]
        for p in protocols:
            assert issubclass(p, Protocol) and p is not Protocol, f"{p} is not a Protocol"


class TestPublicApi:
    def test_all_interfaces_exported(self):
        from ares.orchestration import (
            CacheProvider,
            EventPublisher,
            FallbackPolicy,
            MetricsCollector,
            PipelineStage,
            RetryPolicy,
            StrategyProvider,
        )

        assert CacheProvider is not None
        assert StrategyProvider is not None
        assert RetryPolicy is not None
        assert FallbackPolicy is not None
        assert MetricsCollector is not None
        assert EventPublisher is not None
        assert PipelineStage is not None
