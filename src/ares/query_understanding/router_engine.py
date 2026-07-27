from __future__ import annotations

import time

from ares.query_understanding.complexity_models import ComplexityAnalysis
from ares.query_understanding.entity_models import EntityResult
from ares.query_understanding.query_models import (
    QuestionMetadata,
    QuestionSimilarityFeatures,
)
from ares.query_understanding.relationship_models import RelationshipAnalysis
from ares.query_understanding.router_models import (
    PRIORITY_NORMAL,
    RISK_HIGH,
    STRATEGY_BASELINE,
    STRATEGY_CROSS_ENCODER,
    STRATEGY_ENSEMBLE,
    STRATEGY_FALLBACK,
    STRATEGY_FAST_LEXICAL,
    RoutingDecision,
)
from ares.query_understanding.router_rules import (
    _extract_signal,
    _register_rules,
    compute_strategy_scores,
)
from ares.query_understanding.type_models import QuestionTypeResult


class RouterEngine:
    version: str = "1.0.0"

    def __init__(self) -> None:
        self._rules = _register_rules()

    def decide(
        self,
        question_1: str = "",
        question_2: str = "",
        metadata_1: QuestionMetadata | None = None,
        metadata_2: QuestionMetadata | None = None,
        similarity: QuestionSimilarityFeatures | None = None,
        question_type: QuestionTypeResult | None = None,
        entity_analysis: EntityResult | None = None,
        relationship_analysis: RelationshipAnalysis | None = None,
        complexity_analysis: ComplexityAnalysis | None = None,
    ) -> RoutingDecision:
        start = time.time()

        if not question_1.strip() or not question_2.strip():
            elapsed = (time.time() - start) * 1000
            return RoutingDecision(
                selected_strategy=STRATEGY_FALLBACK,
                confidence=0.0,
                priority=PRIORITY_NORMAL,
                reason_codes=["empty_input"],
                risk_level=RISK_HIGH,
                estimated_cost=0.0,
                estimated_latency=0.0,
                explanation="Empty input",
                processing_time=round(elapsed, 2),
                version=self.version,
            )

        signal = _extract_signal(
            metadata_1=metadata_1,
            metadata_2=metadata_2,
            similarity=similarity,
            question_type=question_type,
            entity_analysis=entity_analysis,
            relationship_analysis=relationship_analysis,
            complexity_analysis=complexity_analysis,
        )

        strategy_scores, triggered = compute_strategy_scores(signal, self._rules)

        strategies_in_order = [
            STRATEGY_ENSEMBLE,
            STRATEGY_CROSS_ENCODER,
            STRATEGY_BASELINE,
            STRATEGY_FAST_LEXICAL,
            STRATEGY_FALLBACK,
        ]

        best_strategy = STRATEGY_FALLBACK
        best_score = -1.0
        all_scores: list[tuple[str, float]] = []

        for strategy in strategies_in_order:
            info = strategy_scores[strategy]
            score = info["score"]
            all_scores.append((strategy, score))
            if score > best_score:
                best_score = score
                best_strategy = strategy

        if best_score <= 0.0:
            best_strategy = STRATEGY_FAST_LEXICAL

        best_info = strategy_scores[best_strategy]
        confidence = min(1.0, best_score)
        risk_level = best_info["risk"]
        priority = best_info["priority"]

        reason_codes = [t["rule"] for t in triggered]

        explanation_lines = [f"Selected: {best_strategy} (score={best_score:.4f})"]
        if triggered:
            explanation_lines.append(f"Triggered rules ({len(triggered)}):")
            for t in triggered:
                explanation_lines.append(f"  - {t['rule']}: {t['description']} (score={t['score']})")
        explanation_lines.append(f"Rejected alternatives: {', '.join(s for s, sc in all_scores if s != best_strategy)}")
        explanation = "\n".join(explanation_lines)

        elapsed = round((time.time() - start) * 1000, 2)

        return RoutingDecision(
            selected_strategy=best_strategy,
            confidence=round(confidence, 4),
            priority=priority,
            reason_codes=reason_codes,
            triggered_rules=triggered,
            risk_level=risk_level,
            estimated_cost=best_info["cost"],
            estimated_latency=best_info["latency"],
            explanation=explanation,
            processing_time=elapsed,
            version=self.version,
        )
