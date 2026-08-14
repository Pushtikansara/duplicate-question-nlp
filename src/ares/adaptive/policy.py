from __future__ import annotations

from typing import Any

from ares.adaptive.config_loader import AdaptiveRoutingConfig
from ares.adaptive.models import ComputeBudget, DifficultyAssessment, RoutingPlan
from ares.adaptive.profiles import ModelProfileRegistry
from ares.orchestration.strategy_registry import StrategyRegistry

# Cheap -> strong ordering of the Phase 13 strategy catalog.  Used to build the
# escalation ladder deterministically from registry definitions.
_STRATEGY_PRIORITY = ("fast_lexical", "baseline_classifier", "cross_encoder", "ensemble")


class AdaptiveRoutingPolicy:
    """Builds a deterministic routing plan for one request.

    The policy decides the initial strategy, the escalation ladder, whether
    reflection / fusion / early exit apply and whether human review is
    recommended.  Every threshold is configuration-driven.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        strategy_registry: StrategyRegistry | None = None,
        profile_registry: ModelProfileRegistry | None = None,
    ) -> None:
        self._config = AdaptiveRoutingConfig(config)
        self._strategies = strategy_registry or StrategyRegistry.with_defaults()
        self._profiles = profile_registry or ModelProfileRegistry(config)

    def make_plan(self, assessment: DifficultyAssessment, budget: ComputeBudget) -> RoutingPlan:
        ladder = self._build_ladder()
        initial = self._pick_initial(strategy_provided=assessment.recommended_strategy, ladder=ladder)
        if initial is None:
            initial = "fast_lexical"
        initial_model = self._model_for(initial)
        escalation = self._build_escalation_ladder(assessment, ladder, initial)

        reflection_requested, reflection_reason, skipped_reason = self._decide_reflection(assessment)
        fusion_requested, fusion_reason = self._decide_fusion(assessment, budget)
        review = self._decide_human_review(assessment)
        early_exit = self._decide_early_exit(assessment, budget)
        method = self._config.fusion_method

        explanation = (
            f"initial={initial} ({initial_model}); ladder=[{', '.join(ladder)}]; "
            f"reflection={reflection_requested}; fusion={fusion_requested}; early_exit_eligible={early_exit}; "
            f"review={review}"
        )

        return RoutingPlan(
            initial_strategy=initial,
            initial_model=initial_model,
            escalation_ladder=escalation,
            reflection_requested=reflection_requested,
            reflection_reason=reflection_reason,
            reflection_skipped_reason=skipped_reason,
            early_exit_eligible=early_exit,
            fusion_requested=fusion_requested,
            fusion_reason=fusion_reason,
            fusion_method=method,
            human_review_recommended=review,
            explanation=explanation,
        )

    def _build_ladder(self) -> list[str]:
        ladder: list[str] = []
        for name in _STRATEGY_PRIORITY:
            if not self._strategies.contains(name):
                continue
            definition = self._strategies.resolve(name)
            if not definition.enabled:
                continue
            profile = self._profiles.get(definition.model_name)
            if profile is None or not profile.available:
                continue
            ladder.append(name)
        if not ladder:
            ladder.append("fast_lexical")
        return ladder

    def _pick_initial(self, strategy_provided: str, ladder: list[str]) -> str | None:
        if strategy_provided in ladder:
            return strategy_provided
        for name in _STRATEGY_PRIORITY:
            if name in ladder:
                return name
        return ladder[0] if ladder else None

    def _build_escalation_ladder(
        self, assessment: DifficultyAssessment, full_ladder: list[str], initial: str
    ) -> list[str]:
        level = assessment.difficulty_level
        if level == "easy":
            return []
        cheap = {"fast_lexical", "baseline_classifier"}
        stronger = [s for s in full_ladder if s != initial and s not in cheap]
        if level == "medium":
            return stronger[:1]
        if level == "hard":
            return stronger[:2]
        return stronger

    def _model_for(self, strategy: str) -> str:
        try:
            definition = self._strategies.resolve(strategy)
            return str(definition.model_name)
        except Exception:
            return ""

    def _decide_reflection(self, assessment: DifficultyAssessment) -> tuple[bool, str | None, str | None]:
        mode = self._config.reflection_mode
        if mode == "always":
            return True, "reflection_mode=always", None
        if mode == "never":
            return False, None, "reflection disabled by configuration"
        # conditional
        hard_only = self._config.reflection_hard_difficulty_only
        if hard_only:
            if assessment.difficulty_level in ("hard", "critical"):
                return True, "difficulty level requires reflection", None
            return False, None, "difficulty is not hard/critical (conditional mode)"
        if assessment.difficulty_level in ("hard", "critical") or assessment.uncertainty_score >= 0.5:
            return True, "difficulty/uncertainty warrants reflection", None
        return False, None, "easy/medium difficulty with low uncertainty (conditional mode)"

    def _decide_fusion(self, assessment: DifficultyAssessment, budget: ComputeBudget) -> tuple[bool, str | None]:
        if not self._config.fusion_enabled:
            return False, None
        if budget.fusion_min_models <= 0:
            return False, None
        architecture_available = self._fusion_model_count() >= budget.fusion_min_models
        if not architecture_available:
            return False, None
        if assessment.difficulty_level in ("hard", "critical") or assessment.risk_level in ("high", "critical"):
            return True, "hard/critical request benefits from multiple independent evidence sources"
        if assessment.difficulty_level == "medium" and budget.max_escalation_level >= 1:
            return True, "medium difficulty with moderate budget; fusion adds independent evidence"
        return False, None

    def _fusion_model_count(self) -> int:
        names = self._config.fusion_model_names
        if names:
            return sum(1 for n in names if (self._profiles.get(n) or self._profiles.get_by_internal_id(n)) is not None)
        return max(0, len(self._profiles.available()) - 1)

    def _decide_early_exit(self, assessment: DifficultyAssessment, budget: ComputeBudget) -> bool:
        if not self._config.early_exit_enabled:
            return False
        if budget.max_escalation_level != 0:
            # early exit still allowed, but runtime additionally checks confidence
            pass
        if self._config.early_exit_only_low_risk and assessment.risk_level not in ("low", "medium"):
            return False
        return assessment.difficulty_level in ("easy", "medium")

    def _decide_human_review(self, assessment: DifficultyAssessment) -> bool:
        return assessment.difficulty_level == "critical" or assessment.risk_level in ("high", "critical")
