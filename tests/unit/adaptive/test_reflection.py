from __future__ import annotations

from ares._result import PredictionResult
from ares.adaptive.reflection import AdaptiveReflection


def result(
    confidence: float = 0.8,
    prob_duplicate: float = 0.8,
    label: int = 1,
    latency_ms: float = 10.0,
) -> PredictionResult:
    return PredictionResult(
        predicted_label=label,
        prediction="Duplicate" if label else "Non-Duplicate",
        confidence=confidence,
        prob_duplicate=prob_duplicate,
        prob_non_duplicate=round(1.0 - prob_duplicate, 6),
        model_name="test-model",
        latency_ms=latency_ms,
    )


def reflector(cfg=None) -> AdaptiveReflection:
    return AdaptiveReflection(cfg)


class TestSkipped:
    def test_not_requested_skips_execution(self):
        rec = reflector().reflect(
            result(),
            "q1",
            "q2",
            requested=False,
            skipped_reason="no trigger",
        )
        assert rec.requested is False
        assert rec.executed is False
        assert rec.skipped_reason == "no trigger"

    def test_no_trigger_recorded_cleanly(self):
        rec = reflector().reflect(
            result(),
            "q1",
            "q2",
            requested=False,
            skipped_reason="difficulty not hard",
        )
        assert rec.skipped_reason == "difficulty not hard"
        assert rec.recommendations == []


class TestExecuted:
    def test_execution_updates_result(self):
        r = result(confidence=0.8)
        rec = reflector().reflect(r, "A", "B", requested=True, skipped_reason=None)
        assert rec.requested is True
        assert rec.executed is True
        # confidence may be adjusted; trust/risk are computed
        assert r.trust_score is not None
        assert r.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert rec.human_review_required is not None

    def test_execution_surfaces_recommendations_when_untrusted(self):
        r = result(confidence=0.3, prob_duplicate=0.3, label=0)
        rec = reflector().reflect(r, "A", "B", requested=True, skipped_reason=None)
        assert rec.recommendations

    def test_latency_recorded(self):
        rec = reflector().reflect(result(), "A", "B", requested=True, skipped_reason=None)
        assert rec.latency_ms >= 0.0

    def test_agreement_and_uncertainty_are_accepted(self):
        rec = reflector().reflect(
            result(),
            "A",
            "B",
            requested=True,
            skipped_reason=None,
            agreement=0.9,
            uncertainty=0.1,
            model_count=2,
            mode="fusion",
        )
        assert rec.executed is True
