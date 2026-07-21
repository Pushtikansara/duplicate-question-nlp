from __future__ import annotations

import logging
from typing import Any

from duplicate_question_app._routing.configuration import RoutingConfig
from duplicate_question_app._routing.interfaces import PipelineSelector
from duplicate_question_app._routing.routing_result import ComplexityResult, PipelineSelection, UncertaintyResult
from duplicate_question_app._routing.routing_strategy import RoutingStrategy

log = logging.getLogger(__name__)

_PIPELINE_MAP: dict[str, dict[str, Any]] = {
    "cross_encoder_only": {
        "required": ["cross_encoder"],
        "skipped": ["semantic_intelligence", "reasoning", "made"],
    },
    "semantic_reasoning": {
        "required": ["cross_encoder", "semantic_intelligence", "reasoning"],
        "skipped": ["made"],
    },
    "full_cognitive": {
        "required": ["cross_encoder", "semantic_intelligence", "reasoning", "made"],
        "skipped": [],
    },
    "uncertain_full": {
        "required": ["cross_encoder", "semantic_intelligence", "reasoning", "made", "debate"],
        "skipped": [],
    },
}


class DefaultPipelineSelector(PipelineSelector):
    def select(
        self,
        complexity: ComplexityResult,
        uncertainty: UncertaintyResult,
        config: RoutingConfig,
    ) -> PipelineSelection:
        strategy = config.default_strategy
        complexity_label = complexity.complexity
        escalate = uncertainty.should_escalate

        pipeline = self._resolve_pipeline(complexity_label, escalate, strategy)

        pipeline_info = _PIPELINE_MAP.get(pipeline, _PIPELINE_MAP["uncertain_full"])
        required = list(pipeline_info["required"])
        skipped = list(pipeline_info["skipped"])

        reason_parts: list[str] = []
        reason_parts.append(f"Complexity: {complexity_label}")
        reason_parts.append(f"Escalation: {escalate}")
        reason_parts.append(f"Strategy: {strategy.value}")
        reason_parts.append(f"Selected: {pipeline}")

        return PipelineSelection(
            pipeline=pipeline,
            required_modules=required,
            skipped_modules=skipped,
            reason="; ".join(reason_parts),
        )

    def _resolve_pipeline(
        self,
        complexity: str,
        escalate: bool,
        strategy: RoutingStrategy,
    ) -> str:
        if escalate:
            return "uncertain_full"

        if strategy == RoutingStrategy.FASTEST:
            return self._resolve_fastest(complexity)

        if strategy == RoutingStrategy.HIGHEST_ACCURACY:
            return self._resolve_highest_accuracy(complexity)

        if strategy == RoutingStrategy.RESEARCH:
            return "uncertain_full"

        return self._resolve_balanced(complexity)

    def _resolve_fastest(self, complexity: str) -> str:
        mapping = {
            "simple": "cross_encoder_only",
            "medium": "semantic_reasoning",
            "complex": "full_cognitive",
            "uncertain": "cross_encoder_only",
        }
        return mapping.get(complexity, "cross_encoder_only")

    def _resolve_balanced(self, complexity: str) -> str:
        mapping = {
            "simple": "cross_encoder_only",
            "medium": "semantic_reasoning",
            "complex": "full_cognitive",
            "uncertain": "uncertain_full",
        }
        return mapping.get(complexity, "cross_encoder_only")

    def _resolve_highest_accuracy(self, complexity: str) -> str:
        mapping = {
            "simple": "semantic_reasoning",
            "medium": "full_cognitive",
            "complex": "uncertain_full",
            "uncertain": "uncertain_full",
        }
        return mapping.get(complexity, "uncertain_full")
