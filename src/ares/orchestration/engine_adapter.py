from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError

from ares._engine import ARES
from ares.orchestration.constants import DEFAULT_TIMEOUT_MS
from ares.orchestration.exceptions import (
    ModelTimeoutError,
    ModelUnavailableError,
    OrchestrationError,
    TaskExecutionError,
)


class ARESPredictionEngine:
    """Adapts the ARES engine to the ``PredictionEngine`` protocol.

    Applies the selected engine configuration (model, threshold, reflection,
    semantic validation) through the ARES fluent builder and enforces the
    per-request timeout by running the prediction in a dedicated worker
    thread. Timeouts surface as ``ModelTimeoutError``; unknown or unavailable
    models surface as ``ModelUnavailableError``; any other engine failure is
    wrapped in ``TaskExecutionError``.
    """

    def __init__(self, engine: ARES | None = None, default_timeout_ms: float = DEFAULT_TIMEOUT_MS) -> None:
        self._engine = engine or ARES()
        self.default_timeout_ms = default_timeout_ms

    def predict(
        self,
        question1: str,
        question2: str,
        *,
        model: str,
        threshold: float | None = None,
        reflect: bool = True,
        semantic_validation: bool = True,
        timeout_ms: float | None = None,
    ) -> object:
        timeout_ms = timeout_ms if timeout_ms is not None else self.default_timeout_ms
        engine = (
            ARES()
            .with_model(model)
            .with_threshold(threshold if threshold is not None else 0.5)
            .with_reflection(reflect)
            .with_semantic_validation(semantic_validation)
        )
        try:
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix="ares-predict") as executor:
                future = executor.submit(engine.predict, question1, question2)
                try:
                    return future.result(timeout=timeout_ms / 1000.0)
                except FutureTimeoutError:
                    future.cancel()
                    raise ModelTimeoutError(
                        f"Prediction timed out after {timeout_ms:.0f}ms for model '{model}'"
                    ) from None
        except OrchestrationError:
            raise
        except (RuntimeError, ValueError) as exc:
            message = str(exc)
            if "No models available" in message or "not in the model registry" in message:
                raise ModelUnavailableError(message) from exc
            raise TaskExecutionError(message) from exc
        except Exception as exc:
            raise TaskExecutionError(f"Prediction failed: {exc}") from exc

    @property
    def engine(self) -> ARES:
        return self._engine
