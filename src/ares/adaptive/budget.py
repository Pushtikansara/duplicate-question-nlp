from __future__ import annotations

from typing import Any

from ares.adaptive.config_loader import AdaptiveRoutingConfig
from ares.adaptive.models import ComputeBudget


class BudgetPolicy:
    """Maps a difficulty/risk assessment to a concrete ``ComputeBudget``.

    Budget tiers are fully configurable through the ``budget.tiers`` section;
    the router is free to reason in terms of latency budget, model-invocation
    budget, escalation depth and reflection allowance.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = AdaptiveRoutingConfig(config)

    def allocate(self, difficulty_level: str, risk_level: str) -> ComputeBudget:
        tier_name = self._tier_for(difficulty_level, risk_level)
        tiers = self._config.budget_tiers
        tier = tiers.get(tier_name) if isinstance(tiers, dict) else None
        if not isinstance(tier, dict):
            tier = {}
        return ComputeBudget(
            name=tier_name,
            max_model_calls=int(tier.get("max_model_calls", 1)),
            max_escalation_level=int(tier.get("max_escalation_level", 0)),
            max_latency_ms=float(tier.get("max_latency_ms", 1000)),
            reflection_allowed=bool(tier.get("reflection_allowed", False)),
            fusion_min_models=int(tier.get("fusion_min_models", 0)),
            max_stages=int(tier.get("max_stages", 8)),
        )

    def _tier_for(self, difficulty_level: str, risk_level: str) -> str:
        if difficulty_level in ("hard", "critical") or risk_level in ("high", "critical"):
            return "high"
        if difficulty_level == "medium" or risk_level == "medium":
            return "medium"
        return "low"
