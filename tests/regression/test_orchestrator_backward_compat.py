from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from ares._result import PredictionResult
from ares.orchestration.exceptions import ModelUnavailableError, OrchestrationError
from ares.orchestration.prediction_service import build_default_prediction_service
from ares.orchestration.strategy_registry import StrategyRegistry, StrategySelector
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.router_models import RoutingDecision


def _result() -> PredictionResult:
    return PredictionResult(
        predicted_label=1,
        prediction="duplicate",
        confidence=0.9,
        prob_duplicate=0.9,
        prob_non_duplicate=0.1,
        model_name="Test Model",
        latency_ms=1.0,
    )


class FakeQueryPipeline:
    """Routes every pair to the fast-lexical strategy (reflection off)."""

    def run(self, question_1: str, question_2: str) -> QueryAnalysis:
        return QueryAnalysis(
            original_question_1=question_1,
            original_question_2=question_2,
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )


class CrossEncoderQueryPipeline:
    """Routes every pair to the cross-encoder strategy (reflection on)."""

    def run(self, question_1: str, question_2: str) -> QueryAnalysis:
        return QueryAnalysis(
            original_question_1=question_1,
            original_question_2=question_2,
            routing_decision=RoutingDecision(selected_strategy="cross_encoder"),
        )


class FakeEngine:
    def __init__(self) -> None:
        self.result: PredictionResult | None = None
        self.error: Exception | None = None
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
        self.calls.append((question1, question2, kwargs))
        if self.error is not None:
            raise self.error
        return self.result


def _new_service(
    engine: FakeEngine,
    pipeline: Any,
) -> Any:
    selector = StrategySelector(StrategyRegistry.with_defaults())
    return build_default_prediction_service(
        engine=engine,
        query_pipeline=pipeline,
        strategy_selector=selector,
        cache_provider=None,
    )


class TestBackwardCompatibility:
    def test_explicit_params_match_between_paths(self) -> None:
        """Explicit model/threshold/reflect must reach the engine identically
        in the old direct-ARES path and the new orchestrator path."""
        with patch("ares.ARES") as MockARES:
            engine = MagicMock()
            engine.predict.return_value = _result()
            engine.with_model.return_value = engine
            engine.with_threshold.return_value = engine
            engine.with_reflection.return_value = engine
            MockARES.return_value = engine
            from ares import ARES

            ares_engine = ARES().with_model("TF-IDF + Linear SVM (Week 2)").with_threshold(0.7).with_reflection(False)
            ares_engine.predict("q1", "q2")
            assert engine.with_model.call_args.args == ("TF-IDF + Linear SVM (Week 2)",)
            assert engine.with_threshold.call_args.args == (0.7,)
            assert engine.with_reflection.call_args.args == (False,)

        fake_engine = FakeEngine()
        fake_engine.result = _result()
        service = _new_service(fake_engine, FakeQueryPipeline())
        service.predict("q1", "q2", model="TF-IDF + Linear SVM (Week 2)", threshold=0.7, reflect=False)
        _, _, kwargs = fake_engine.calls[0]
        assert kwargs["model"] == "TF-IDF + Linear SVM (Week 2)"
        assert kwargs["threshold"] == 0.7
        assert kwargs["reflect"] is False

    def test_reflect_none_keeps_strategy_default(self) -> None:
        """reflect=None is NOT turned into an unconditional with_reflection(True):
        the strategy configuration (Phase 13.2) decides the default."""
        fake_engine = FakeEngine()
        fake_engine.result = _result()
        service = _new_service(fake_engine, FakeQueryPipeline())
        service.predict("q1", "q2")
        _, _, kwargs = fake_engine.calls[0]
        assert kwargs["reflect"] is False  # fast_lexical strategy default

    def test_cross_encoder_strategy_preserves_reflection_true_default(self) -> None:
        """For strategies whose default reflection is True (e.g. cross encoder)
        the behavior matches the legacy ARES default of reflection enabled."""
        fake_engine = FakeEngine()
        fake_engine.result = _result()
        service = _new_service(fake_engine, CrossEncoderQueryPipeline())
        service.predict("q1", "q2")
        _, _, kwargs = fake_engine.calls[0]
        assert kwargs["reflect"] is True
        assert kwargs["model"] == "Cross-Encoder-Quora (Trained)"

    def test_threshold_default_unchanged(self) -> None:
        fake_engine = FakeEngine()
        fake_engine.result = _result()
        service = _new_service(fake_engine, FakeQueryPipeline())
        service.predict("q1", "q2")
        _, _, kwargs = fake_engine.calls[0]
        assert kwargs["threshold"] == 0.5

    def test_prediction_fields_identical_between_paths(self) -> None:
        """The same engine output surfaces unchanged through both paths:
        prediction, label, score, confidence and model name."""
        with patch("ares.ARES") as MockARES:
            engine = MagicMock()
            engine.predict.return_value = _result()
            MockARES.return_value = engine
            from ares import ARES

            old_result = ARES().predict("q1", "q2")

        fake_engine = FakeEngine()
        fake_engine.result = _result()
        service = _new_service(fake_engine, FakeQueryPipeline())
        new_result = service.predict("q1", "q2")

        assert new_result.predicted_label == old_result.predicted_label
        assert new_result.prediction == old_result.prediction
        assert new_result.confidence == old_result.confidence
        assert new_result.prob_duplicate == old_result.prob_duplicate
        assert new_result.model_name == old_result.model_name

    def test_engine_errors_surface_as_orchestration_errors(self) -> None:
        """The new path wraps engine failures in orchestration errors instead
        of leaking raw engine exceptions to callers."""
        fake_engine = FakeEngine()
        fake_engine.error = RuntimeError("model exploded")
        service = _new_service(fake_engine, FakeQueryPipeline())
        try:
            service.predict("q1", "q2")
            raise AssertionError("expected an orchestration error")
        except OrchestrationError as exc:
            assert isinstance(exc, ModelUnavailableError) or "failed" in str(exc)
