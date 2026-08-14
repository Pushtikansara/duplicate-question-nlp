from __future__ import annotations

from ares.adaptive.budget import BudgetPolicy
from ares.adaptive.models import DifficultyAssessment
from ares.adaptive.policy import AdaptiveRoutingPolicy

from .conftest import hermetic_profile_registry


def plan_for(difficulty: str, risk: str = "low", strategy: str | None = None, cfg=None):
    pol = AdaptiveRoutingPolicy(cfg, profile_registry=hermetic_profile_registry(cfg))
    assessment = DifficultyAssessment(
        difficulty_level=difficulty,
        uncertainty_score=0.2,
        risk_level=risk,
    )
    if strategy:
        assessment.recommended_strategy = strategy
    elif difficulty == "easy":
        assessment.recommended_strategy = "fast_lexical"
    elif difficulty == "medium":
        assessment.recommended_strategy = "baseline_classifier"
    else:
        assessment.recommended_strategy = "cross_encoder"
    budget = BudgetPolicy(cfg).allocate(difficulty, risk)
    return pol.make_plan(assessment, budget)


class TestInitialStrategy:
    def test_easy_prefers_lexical(self):
        plan = plan_for("easy")
        assert plan.initial_strategy == "fast_lexical"

    def test_medium_prefers_baseline(self):
        plan = plan_for("medium")
        assert plan.initial_strategy == "baseline_classifier"

    def test_hard_prefers_cross_encoder(self):
        plan = plan_for("hard")
        assert plan.initial_strategy == "cross_encoder"


class TestEscalationLadder:
    def test_easy_has_no_escalation(self):
        assert plan_for("easy").escalation_ladder == []

    def test_medium_escalates_to_cross_encoder(self):
        plan = plan_for("medium")
        assert "cross_encoder" in plan.escalation_ladder

    def test_hard_escalates_to_ensemble(self):
        plan = plan_for("hard")
        assert "ensemble" in plan.escalation_ladder

    def test_ladder_does_not_repeat_initial(self):
        for difficulty in ("easy", "medium", "hard", "critical"):
            plan = plan_for(difficulty)
            assert plan.initial_strategy not in plan.escalation_ladder


class TestReflection:
    def test_conditional_hard_only(self):
        assert (
            plan_for(
                "easy", cfg={"reflection": {"mode": "conditional", "hard_difficulty_only": True}}
            ).reflection_requested
            is False
        )
        assert (
            plan_for(
                "hard", cfg={"reflection": {"mode": "conditional", "hard_difficulty_only": True}}
            ).reflection_requested
            is True
        )

    def test_always_mode(self):
        assert plan_for("easy", cfg={"reflection": {"mode": "always"}}).reflection_requested is True

    def test_never_mode(self):
        plan = plan_for("hard", cfg={"reflection": {"mode": "never"}})
        assert plan.reflection_requested is False
        assert plan.reflection_skipped_reason


class TestFusion:
    def test_fusion_requested_for_hard(self):
        plan = plan_for("hard", cfg={"fusion": {"enabled": True, "min_models": 2}})
        assert plan.fusion_requested is True

    def test_fusion_disabled(self):
        plan = plan_for("hard", cfg={"fusion": {"enabled": False}})
        assert plan.fusion_requested is False


class TestEarlyExit:
    def test_early_exit_eligible_easy(self):
        plan = plan_for("easy")
        assert plan.early_exit_eligible is True

    def test_early_exit_not_eligible_when_disabled(self):
        plan = plan_for("easy", cfg={"early_exit": {"enabled": False}})
        assert plan.early_exit_eligible is False


class TestHumanReview:
    def test_critical_request_review(self):
        assert plan_for("critical").human_review_recommended is True

    def test_easy_no_review(self):
        assert plan_for("easy").human_review_recommended is False

    def test_high_risk_review(self):
        assert plan_for("easy", risk="high").human_review_recommended is True


class TestPlanMetadata:
    def test_explanation_recorded(self):
        assert plan_for("medium").explanation

    def test_initial_model_is_mapped(self):
        plan = plan_for("medium")
        assert plan.initial_model == "TF-IDF + Linear SVM (Week 2)"
