from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from ares.orchestration.cancellation import CancellationToken
from ares.orchestration.constants import (
    DEFAULT_BATCH_MAX_PAIRS,
    DEFAULT_MAX_CONCURRENCY,
    EVENT_ORCHESTRATION_COMPLETE,
    EVENT_ORCHESTRATION_FAILED,
    EVENT_ORCHESTRATION_STARTED,
)
from ares.orchestration.context import PipelineState, PredictionInput, RequestParams
from ares.orchestration.exceptions import OrchestrationError, PipelineAbortedError
from ares.orchestration.interfaces import (
    EventPublisher,
    FallbackPolicy,
    MetricsCollector,
    RetryPolicy,
)
from ares.orchestration.metadata import ExecutionMetadata, OrchestrationMetadata
from ares.orchestration.pipeline import Pipeline
from ares.orchestration.stage_registry import StageRegistry


class PredictionOrchestrator:
    """Thin controller that wires the stage registry, pipeline and policies.

    ``run`` executes a single question pair through the pipeline and returns
    the prediction result with the orchestration trace attached.
    ``run_batch`` executes pairs with bounded concurrency (results are
    returned in input order, failures are isolated per pair). No hardcoded
    stage list lives here: the stage set comes entirely from the injected
    ``StageRegistry``.
    """

    def __init__(
        self,
        registry: StageRegistry,
        *,
        retry_policy: RetryPolicy | None = None,
        fallback_policy: FallbackPolicy | None = None,
        event_publisher: EventPublisher | None = None,
        metrics: MetricsCollector | None = None,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        batch_max_pairs: int = DEFAULT_BATCH_MAX_PAIRS,
    ) -> None:
        self.registry = registry
        self._retry_policy = retry_policy
        self._fallback_policy = fallback_policy
        self._event_publisher = event_publisher
        self._metrics = metrics
        self.max_concurrency = max_concurrency
        self.batch_max_pairs = batch_max_pairs
        self._lock = threading.Lock()
        self._pipeline: Pipeline | None = None

    def run(
        self,
        question1: str,
        question2: str,
        *,
        model: str | None = None,
        threshold: float | None = None,
        reflect: bool | None = None,
        skip_cache: bool = False,
        timeout_ms: float | None = None,
        cancellation_token: CancellationToken | None = None,
        request_id: str | None = None,
    ) -> Any:
        request_params = RequestParams(
            model=model,
            threshold=threshold,
            reflect=reflect,
            skip_cache=skip_cache,
            timeout_ms=timeout_ms,
        )
        input = PredictionInput(question1=question1, question2=question2, request_params=request_params)
        metadata = OrchestrationMetadata(start_time=time.time())
        execution_metadata = ExecutionMetadata(
            request_id=request_id or self._new_request_id(),
            model_name=model or "",
            strategy="",
        )
        state = PipelineState(execution_metadata=execution_metadata)

        self._publish(EVENT_ORCHESTRATION_STARTED, {"request_id": execution_metadata.request_id})
        try:
            self._pipeline_instance().execute(input, state, metadata, cancellation_token)
            result = state.prediction_result
            if result is None:
                raise PipelineAbortedError("Pipeline completed without a prediction result")
            execution_metadata.strategy = self._selected_strategy(state, execution_metadata)
            if result is not None and hasattr(result, "orchestration_trace"):
                trace = result.orchestration_trace
                if isinstance(trace, dict):
                    trace["strategy"] = execution_metadata.strategy
            self._publish(
                EVENT_ORCHESTRATION_COMPLETE,
                {"request_id": execution_metadata.request_id, "strategy": execution_metadata.strategy},
            )
            return result
        except Exception as exc:
            execution_metadata.error = str(exc)
            self._publish(EVENT_ORCHESTRATION_FAILED, {"request_id": execution_metadata.request_id, "error": str(exc)})
            if isinstance(exc, OrchestrationError):
                raise
            raise PipelineAbortedError(f"Orchestration failed: {exc}") from exc

    def run_batch(
        self,
        pairs: list[tuple[str, str]],
        *,
        model: str | None = None,
        threshold: float | None = None,
        reflect: bool | None = None,
        skip_cache: bool = False,
        timeout_ms: float | None = None,
        max_concurrency: int | None = None,
        request_id: str | None = None,
    ) -> list[Any]:
        if not pairs:
            return []
        if len(pairs) > self.batch_max_pairs:
            raise ValueError(f"Batch size {len(pairs)} exceeds configured maximum of {self.batch_max_pairs} pairs")
        concurrency = max(1, min(max_concurrency or self.max_concurrency, self.max_concurrency))
        results: list[Any] = [None] * len(pairs)

        def run_pair(index: int, pair: tuple[str, str]) -> tuple[int, Any]:
            try:
                result = self.run(
                    pair[0],
                    pair[1],
                    model=model,
                    threshold=threshold,
                    reflect=reflect,
                    skip_cache=skip_cache,
                    timeout_ms=timeout_ms,
                    request_id=request_id,
                )
                return index, result
            except Exception as exc:
                return index, exc

        with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="ares-orchestrator") as executor:
            futures = {executor.submit(run_pair, index, pair): index for index, pair in enumerate(pairs)}
            for future in as_completed(futures):
                index, outcome = future.result()
                results[index] = outcome

        return results

    def _pipeline_instance(self) -> Pipeline:
        with self._lock:
            if self._pipeline is None:
                self._pipeline = Pipeline(
                    self.registry,
                    retry_policy=self._retry_policy,
                    fallback_policy=self._fallback_policy,
                    event_publisher=self._event_publisher,
                    metrics=self._metrics,
                )
            return self._pipeline

    @staticmethod
    def _selected_strategy(state: PipelineState, execution_metadata: ExecutionMetadata) -> str:
        strategy: str = execution_metadata.strategy
        if strategy:
            return strategy
        analysis = state.query_analysis
        if analysis is not None:
            routing_decision = getattr(analysis, "routing_decision", None)
            if routing_decision is not None:
                selected: str = getattr(routing_decision, "selected_strategy", "") or ""
                return selected
        return ""

    @staticmethod
    def _new_request_id() -> str:
        return uuid.uuid4().hex[:16]

    def _publish(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        if self._event_publisher is not None:
            self._event_publisher.publish(event_type, payload)
