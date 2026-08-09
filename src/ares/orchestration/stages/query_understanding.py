from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ares.orchestration.cache_key import build_query_understanding_cache_key
from ares.orchestration.constants import (
    DEFAULT_CACHE_TTL_SECONDS,
    EVENT_CACHE_HIT,
    EVENT_CACHE_MISS,
    STAGE_QUERY_UNDERSTANDING,
)
from ares.orchestration.context import PipelineState, PredictionInput
from ares.orchestration.exceptions import CacheError, QueryUnderstandingError
from ares.orchestration.interfaces import CacheProvider, EventPublisher, PipelineStage
from ares.orchestration.metadata import OrchestrationMetadata
from ares.query_understanding.query_pipeline import QueryPipeline


class QueryUnderstandingStage(PipelineStage):
    """Runs the Query Understanding pipeline for a question pair.

    Results are cached through the injected ``CacheProvider`` (Phase 13.2
    ``InMemoryCacheProvider``) using the deterministic
    ``build_query_understanding_cache_key``. Cache hits skip the analysis and
    mark the run as cache hit in the orchestration metadata. Cache failures
    are fatal only when ``fail_closed`` is set, otherwise analysis proceeds
    without caching.
    """

    name = STAGE_QUERY_UNDERSTANDING

    def __init__(
        self,
        query_pipeline: QueryPipeline,
        cache_provider: CacheProvider | None = None,
        *,
        cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        cache_key_builder: Callable[[PredictionInput], str] | None = None,
        event_publisher: EventPublisher | None = None,
        fail_closed: bool = False,
    ) -> None:
        self._pipeline = query_pipeline
        self._cache_provider = cache_provider
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache_key_builder = cache_key_builder or self._default_key_builder
        self._event_publisher = event_publisher
        self.fail_closed = fail_closed

    def run(
        self,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
    ) -> None:
        if self._cache_provider is not None and not input.request_params.skip_cache:
            cached = self._try_cache_get(input, metadata)
            if cached is not None:
                metadata.cache_hit = True
                state.query_analysis = cached
                self._publish(EVENT_CACHE_HIT, input)
                return
            self._publish(EVENT_CACHE_MISS, input)

        try:
            analysis = self._pipeline.run(input.question1, input.question2)
        except Exception as exc:
            raise QueryUnderstandingError(f"Query understanding failed: {exc}") from exc

        state.query_analysis = analysis
        if self._cache_provider is not None and not input.request_params.skip_cache:
            self._try_cache_set(input, analysis)

    def _try_cache_get(self, input: PredictionInput, metadata: OrchestrationMetadata) -> Any | None:
        provider = self._cache_provider
        if provider is None:
            return None
        try:
            return provider.get(self._cache_key_builder(input))
        except Exception as exc:
            if self.fail_closed:
                raise CacheError(f"Cache read failed: {exc}") from exc
            metadata.cache_hit = False
            return None

    def _try_cache_set(self, input: PredictionInput, analysis: Any) -> None:
        provider = self._cache_provider
        if provider is None:
            return
        try:
            provider.set(
                self._cache_key_builder(input),
                analysis,
                self._cache_ttl_seconds,
            )
        except Exception as exc:
            if self.fail_closed:
                raise CacheError(f"Cache write failed: {exc}") from exc

    def _publish(self, event_type: str, input: PredictionInput) -> None:
        if self._event_publisher is not None:
            self._event_publisher.publish(
                event_type,
                {
                    "question1": input.question1,
                    "question2": input.question2,
                    "skip_cache": input.request_params.skip_cache,
                },
            )

    @staticmethod
    def _default_key_builder(input: PredictionInput) -> str:
        return build_query_understanding_cache_key(input.question1, input.question2)
