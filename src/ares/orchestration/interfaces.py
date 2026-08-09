from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from ares.orchestration.config import EngineConfiguration
from ares.orchestration.context import PipelineState, PredictionInput
from ares.orchestration.metadata import OrchestrationMetadata


class PipelineStage(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def run(
        self,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
    ) -> None: ...


@runtime_checkable
class CacheProvider(Protocol):
    def get(self, key: str) -> Any | None: ...

    def set(self, key: str, value: Any, ttl: int) -> None: ...

    def delete(self, key: str) -> None: ...

    def clear(self) -> None: ...


@runtime_checkable
class StrategyProvider(Protocol):
    def resolve(self, name: str) -> EngineConfiguration: ...

    def list_strategies(self) -> list[str]: ...


@runtime_checkable
class RetryPolicy(Protocol):
    def should_retry(self, attempt: int, error: Exception) -> bool: ...

    def get_backoff(self, attempt: int) -> float: ...


@runtime_checkable
class FallbackPolicy(Protocol):
    def get_fallback_config(self) -> EngineConfiguration: ...


@runtime_checkable
class MetricsCollector(Protocol):
    def increment(self, metric: str, tags: dict[str, str] | None = None) -> None: ...

    def gauge(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None: ...

    def timing(self, metric: str, duration_ms: float, tags: dict[str, str] | None = None) -> None: ...


@runtime_checkable
class EventPublisher(Protocol):
    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> None: ...


@runtime_checkable
class PredictionEngine(Protocol):
    def predict(self, question1: str, question2: str, **kwargs: Any) -> Any: ...
