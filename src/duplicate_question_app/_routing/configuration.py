from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from duplicate_question_app._routing.routing_strategy import RoutingStrategy

log = logging.getLogger(__name__)


@dataclass
class RoutingConfig:
    default_strategy: RoutingStrategy = RoutingStrategy.BALANCED
    complexity_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "medium_score": 0.4,
            "complex_score": 0.7,
        }
    )
    uncertainty_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "escalation_confidence": 0.4,
            "semantic_confidence": 0.5,
        }
    )
    cost_limits: dict[str, float] = field(
        default_factory=lambda: {
            "max_cost": 1.0,
        }
    )
    latency_limits: dict[str, float] = field(
        default_factory=lambda: {
            "max_latency_ms": 5000.0,
        }
    )
    enable_cost_estimation: bool = True
    enable_latency_estimation: bool = True


class RoutingConfigLoader:
    @staticmethod
    def from_dict(data: dict[str, Any]) -> RoutingConfig:
        strategy_value = data.get("default_strategy", "balanced")
        try:
            strategy = RoutingStrategy(strategy_value)
        except ValueError:
            log.warning("Unknown strategy '%s', falling back to BALANCED", strategy_value)
            strategy = RoutingStrategy.BALANCED

        return RoutingConfig(
            default_strategy=strategy,
            complexity_thresholds=data.get(
                "complexity_thresholds",
                {
                    "medium_score": 0.4,
                    "complex_score": 0.7,
                },
            ),
            uncertainty_thresholds=data.get(
                "uncertainty_thresholds",
                {
                    "escalation_confidence": 0.4,
                    "semantic_confidence": 0.5,
                },
            ),
            cost_limits=data.get("cost_limits", {"max_cost": 1.0}),
            latency_limits=data.get("latency_limits", {"max_latency_ms": 5000.0}),
            enable_cost_estimation=data.get("enable_cost_estimation", True),
            enable_latency_estimation=data.get("enable_latency_estimation", True),
        )

    @staticmethod
    def from_file(path: str | Path) -> RoutingConfig:
        path = Path(path)
        if not path.exists():
            log.warning("Config file '%s' not found, using defaults", path)
            return RoutingConfig()

        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return RoutingConfigLoader.from_dict(data)
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Failed to load config from '%s': %s, using defaults", path, exc)
            return RoutingConfig()
