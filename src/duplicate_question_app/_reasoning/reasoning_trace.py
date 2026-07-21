from __future__ import annotations

import time

from duplicate_question_app._reasoning.reasoning_result import ReasoningTrace, ReasoningTraceStep


class TraceRecorder:
    def __init__(self) -> None:
        self._trace = ReasoningTrace()
        self._step = 0

    @property
    def trace(self) -> ReasoningTrace:
        return self._trace

    def record(
        self,
        component: str,
        action: str,
        detail: str = "",
        confidence: float = 1.0,
        elapsed_ms: float = 0.0,
    ) -> None:
        self._step += 1
        self._trace.add(
            ReasoningTraceStep(
                step=self._step,
                component=component,
                action=action,
                detail=detail,
                confidence=confidence,
                elapsed_ms=elapsed_ms,
            )
        )

    def step(self, component: str, action: str) -> _Timer:
        return _Timer(self, component, action)


class _Timer:
    def __init__(self, recorder: TraceRecorder, component: str, action: str) -> None:
        self._recorder = recorder
        self._component = component
        self._action = action
        self._start: float = 0.0

    def __enter__(self) -> _Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        elapsed = (time.perf_counter() - self._start) * 1000
        self._recorder.record(
            component=self._component,
            action=self._action,
            elapsed_ms=elapsed,
        )

    def record_detail(self, detail: str, confidence: float = 1.0) -> None:
        self._recorder.record(
            component=self._component,
            action=self._action,
            detail=detail,
            confidence=confidence,
            elapsed_ms=(time.perf_counter() - self._start) * 1000,
        )
