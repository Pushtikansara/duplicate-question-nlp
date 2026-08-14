from __future__ import annotations

from ares.adaptive.models import (
    ComputeBudget,
    DifficultyAssessment,
    ModelEvidence,
    RoutingPlan,
)
from ares.adaptive.trace import build_adaptive_trace


def make_assessment(**kw) -> DifficultyAssessment:
    defaults = dict(
        difficulty_level="easy",
        difficulty_score=0.2,
        uncertainty_score=0.1,
        risk_level="low",
    )
    defaults.update(kw)
    return DifficultyAssessment(**defaults)


def make_budget(**kw) -> ComputeBudget:
    defaults = dict(
        name="low",
        max_model_calls=2,
        max_escalation_level=1,
        max_latency_ms=3000,
        reflection_allowed=False,
        fusion_min_models=2,
    )
    defaults.update(kw)
    return ComputeBudget(**defaults)


def make_plan(**kw) -> RoutingPlan:
    defaults = dict(
        initial_strategy="fast_lexical",
        initial_model="TF-IDF + Logistic Regression (Week 2)",
        escalation_ladder=["cross_encoder"],
        early_exit_eligible=False,
        explanation="initial strategy",
    )
    defaults.update(kw)
    return RoutingPlan(**defaults)


def make_evidence(**kw) -> ModelEvidence:
    defaults = dict(
        model_name="TF-IDF + Logistic Regression (Week 2)",
        strategy="fast_lexical",
        predicted_label=1,
        prediction="Duplicate",
        confidence=0.9,
        prob_duplicate=0.9,
        latency_ms=5.0,
    )
    defaults.update(kw)
    return ModelEvidence(**defaults)


def build(**kw) -> dict:
    base = dict(
        assessment=make_assessment(),
        plan=make_plan(),
        budget=make_budget(),
        evidences=[make_evidence()],
        disagreement=None,
        escalation_count=0,
        escalation_reasons=[],
        early_exit=True,
        early_exit_reason="high confidence",
        reflection=None,
        stages_executed=["fast_lexical"],
        stages_skipped=["cross_encoder", "ensemble"],
        consumed_latency_ms=5.0,
        final_strategy="fast_lexical",
        final_model="TF-IDF + Logistic Regression (Week 2)",
        final_confidence=0.9,
        review_required=False,
        routing_explanation="easy -> fast lexical",
    )
    base.update(kw)
    return build_adaptive_trace(**base)


class TestTraceSections:
    def test_sections_present(self):
        t = build()
        assert "routing" in t
        assert "execution" in t
        assert "adaptive" in t
        assert "evidence" in t
        assert "budget" in t
        assert "final" in t

    def test_routing_section_carries_plan(self):
        t = build()
        assert t["routing"]["initial_strategy"] == "fast_lexical"
        assert t["routing"]["selected_model"] == "TF-IDF + Logistic Regression (Week 2)"

    def test_execution_section_records_stages(self):
        t = build()
        assert t["execution"]["stages_executed"] == ["fast_lexical"]
        assert set(t["execution"]["stages_skipped"]) == {"cross_encoder", "ensemble"}
        assert t["execution"]["model_calls"] == 1
        assert t["adaptive"]["early_exit"] is True

    def test_evidence_records_models(self):
        t = build()
        ev = t["evidence"]["model_predictions"][0]
        assert ev["model_name"] == "TF-IDF + Logistic Regression (Week 2)"
        assert ev["strategy"] == "fast_lexical"
        assert ev["prob_duplicate"] == 0.9

    def test_budget_section_records_limits(self):
        t = build()
        assert t["budget"]["configured_budget"]["name"] == "low"
        assert t["budget"]["consumed_budget"]["latency_ms"] == 5.0


class TestTraceFields:
    def test_error_included_when_serializable(self):
        t = build(error="boom", fallback_used=True)
        assert t["error"] == "boom"
        assert t["fallback_used"] is True

    def test_disagreement_summary_included(self):
        from ares.adaptive.disagreement import DisagreementDetector

        from .conftest import make_evidence as mk

        d = DisagreementDetector().assess([mk("A", 0.1, 0, 0.95), mk("B", 0.9, 1, 0.9)])
        t = build(disagreement=d)
        assert t["evidence"]["disagreement"]["resolution_strategy"] == "confidence_weighted"

    def test_fallback_recorded(self):
        t = build(fallback_used=True, error="fallback")
        assert t["fallback_used"] is True

    def test_review_required_recorded(self):
        t = build(review_required=True)
        assert t["final"]["review_required"] is True
