from __future__ import annotations

import logging

from ares.orchestration.types import OrchestrationStrategyType
from ares.planning.types import PlanningStrategy

logger = logging.getLogger(__name__)

VALID_STRATEGIES = frozenset(s.name.lower() for s in PlanningStrategy)
VALID_ORCHESTRATION_STRATEGIES = frozenset(s.name.lower() for s in OrchestrationStrategyType)


def resolve_planning_strategy(name: str | None) -> PlanningStrategy:
    if not name or not name.strip():
        raise ValueError("No planning strategy provided. Choose one of: " + ", ".join(sorted(VALID_STRATEGIES)))
    raw = name.strip().lower()
    if raw not in VALID_STRATEGIES:
        raise ValueError(f"Unknown planning strategy '{name}'. Choose one of: {', '.join(sorted(VALID_STRATEGIES))}")
    return PlanningStrategy[raw.upper()]


def resolve_orchestration_strategy(name: str | None) -> OrchestrationStrategyType:
    if not name or not name.strip():
        raise ValueError(
            "No orchestration strategy provided. Choose one of: " + ", ".join(sorted(VALID_ORCHESTRATION_STRATEGIES))
        )
    raw = name.strip().lower()
    if raw not in VALID_ORCHESTRATION_STRATEGIES:
        raise ValueError(
            f"Unknown orchestration strategy '{name}'. Choose one of: {', '.join(sorted(VALID_ORCHESTRATION_STRATEGIES))}"
        )
    return OrchestrationStrategyType[raw.upper()]
