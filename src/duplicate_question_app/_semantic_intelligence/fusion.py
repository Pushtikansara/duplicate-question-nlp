from __future__ import annotations

from enum import Enum
from typing import Any


class FusionStrategy(Enum):
    CROSS_ENCODER_ONLY = "cross_encoder_only"
    SEMANTIC_ONLY = "semantic_only"
    FUSION = "fusion"
    CROSS_ENCODER_DOMINANT = "cross_encoder_dominant"
    SEMANTIC_DOMINANT = "semantic_dominant"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    ADAPTIVE = "adaptive"
    LEARNED_WEIGHTING = "learned_weighting"


DEFAULT_FUSION_WEIGHTS: dict[str, float] = {
    "cross_encoder": 0.40,
    "semantic_similarity": 0.25,
    "intent_similarity": 0.15,
    "concept_overlap": 0.10,
    "entity_overlap": 0.05,
    "context_similarity": 0.05,
}

FUSION_STRATEGY_WEIGHTS: dict[FusionStrategy, dict[str, float]] = {
    FusionStrategy.CROSS_ENCODER_DOMINANT: {
        "cross_encoder": 0.80,
        "semantic_similarity": 0.08,
        "intent_similarity": 0.05,
        "concept_overlap": 0.03,
        "entity_overlap": 0.02,
        "context_similarity": 0.02,
    },
    FusionStrategy.SEMANTIC_DOMINANT: {
        "cross_encoder": 0.20,
        "semantic_similarity": 0.40,
        "intent_similarity": 0.15,
        "concept_overlap": 0.10,
        "entity_overlap": 0.08,
        "context_similarity": 0.07,
    },
}

DEFAULT_CONFIDENCE_WEIGHTS: dict[str, float] = {
    "cross_encoder": 0.70,
    "semantic": 0.15,
    "intent": 0.08,
    "concept": 0.04,
    "entity": 0.02,
    "context": 0.01,
}


class DecisionFusion:
    def __init__(
        self,
        strategy: FusionStrategy = FusionStrategy.FUSION,
        weights: dict[str, float] | None = None,
        conflict_penalty: float = 0.3,
        confidence_threshold: float = 0.7,
    ):
        self._strategy = strategy
        self._conflict_penalty = conflict_penalty
        self._confidence_threshold = confidence_threshold

        if strategy in FUSION_STRATEGY_WEIGHTS:
            self._weights = FUSION_STRATEGY_WEIGHTS[strategy]
        elif weights:
            self._weights = weights
        else:
            self._weights = DEFAULT_FUSION_WEIGHTS

        total = sum(self._weights.values())
        if abs(total - 1.0) > 1e-6:
            self._weights = {k: v / total for k, v in self._weights.items()}

    def fuse(
        self,
        cross_encoder_score: float,
        semantic_assessment: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._strategy == FusionStrategy.CROSS_ENCODER_ONLY:
            return self._cross_encoder_only(cross_encoder_score)

        if self._strategy == FusionStrategy.SEMANTIC_ONLY:
            return self._semantic_only(semantic_assessment)

        if self._strategy == FusionStrategy.LEARNED_WEIGHTING:
            return self._learned_weighting(cross_encoder_score, semantic_assessment)

        return self._fuse(cross_encoder_score, semantic_assessment)

    def _cross_encoder_only(self, cross_encoder_score: float) -> dict[str, Any]:
        return {
            "final_score": cross_encoder_score,
            "final_prediction": "Duplicate" if cross_encoder_score >= 0.5 else "Non-Duplicate",
            "strategy": "cross_encoder_only",
            "cross_encoder_score": cross_encoder_score,
            "semantic_score": None,
            "fusion_score": None,
            "weights_used": None,
            "conflict_penalty_applied": 0.0,
            "explanation": "CrossEncoder only mode — no semantic assessment used",
        }

    def _semantic_only(self, assessment: dict[str, Any] | None) -> dict[str, Any]:
        if assessment is None:
            return {
                "final_score": 0.5,
                "final_prediction": "Non-Duplicate",
                "strategy": "semantic_only",
                "cross_encoder_score": None,
                "semantic_score": 0.5,
                "fusion_score": None,
                "weights_used": None,
                "conflict_penalty_applied": 0.0,
                "explanation": "Semantic only mode — no CrossEncoder available",
            }

        semantic_sim = assessment.get("semantic_similarity", 0.5)
        return {
            "final_score": semantic_sim,
            "final_prediction": "Duplicate" if semantic_sim >= 0.5 else "Non-Duplicate",
            "strategy": "semantic_only",
            "cross_encoder_score": None,
            "semantic_score": semantic_sim,
            "fusion_score": None,
            "weights_used": None,
            "conflict_penalty_applied": 0.0,
            "explanation": "Semantic only mode — using semantic similarity from SIE",
        }

    def _extract_assessment_values(self, assessment: dict[str, Any] | None) -> dict[str, float]:
        if assessment is None:
            return {
                "semantic_similarity": 0.5,
                "intent_similarity": 0.5,
                "concept_overlap": 0.5,
                "entity_overlap": 0.5,
                "context_similarity": 0.5,
                "confidence": 0.5,
                "num_conflicts": 0,
                "max_conflict_severity": 0.0,
            }

        def _get_nested(d: Any, *keys: str, default: float = 0.5) -> float:
            for k in keys:
                if isinstance(d, dict):
                    d = d.get(k, {})
                else:
                    return default
            return float(d) if isinstance(d, (int, float)) else default

        return {
            "semantic_similarity": assessment.get("semantic_similarity", 0.5),
            "intent_similarity": _get_nested(assessment, "intent_similarity", "score"),
            "concept_overlap": _get_nested(assessment, "concept_overlap", "overlap_score"),
            "entity_overlap": _get_nested(assessment, "entity_overlap", "overlap_score"),
            "context_similarity": _get_nested(assessment, "context_similarity", "score"),
            "confidence": assessment.get("confidence", 0.5),
            "num_conflicts": len(assessment.get("conflicts", [])),
            "max_conflict_severity": max(
                (c.get("severity", 0.0) for c in assessment.get("conflicts", []) if isinstance(c, dict)),
                default=0.0,
            ),
        }

    def _fuse(self, cross_encoder_score: float, assessment: dict[str, Any] | None) -> dict[str, Any]:
        vals = self._extract_assessment_values(assessment)
        strategy_name = self._strategy.value

        if self._strategy in (FusionStrategy.CROSS_ENCODER_DOMINANT, FusionStrategy.SEMANTIC_DOMINANT):
            use_confidence_weighting = False
        elif self._strategy == FusionStrategy.CONFIDENCE_WEIGHTED:
            use_confidence_weighting = True
        elif self._strategy == FusionStrategy.ADAPTIVE:
            ce_confidence = abs(cross_encoder_score - 0.5) * 2
            sem_confidence = vals.get("confidence", 0.5)
            use_confidence_weighting = True
            ce_weight = max(0.1, min(0.9, ce_confidence))
            sem_weight = max(0.1, min(0.9, sem_confidence))
            total_w = ce_weight + sem_weight
            self._weights = {
                "cross_encoder": ce_weight / total_w,
                "semantic_similarity": (sem_weight * 0.5) / total_w,
                "intent_similarity": (sem_weight * 0.2) / total_w,
                "concept_overlap": (sem_weight * 0.15) / total_w,
                "entity_overlap": (sem_weight * 0.08) / total_w,
                "context_similarity": (sem_weight * 0.07) / total_w,
            }
        else:
            use_confidence_weighting = False

        if use_confidence_weighting:
            sem_confidence = vals.get("confidence", 0.5)
            ce_weight = self._weights.get("cross_encoder", 0.7)
            sem_weight = 1.0 - ce_weight
            adjusted_ce_weight = ce_weight * min(1.0, abs(cross_encoder_score - 0.5) * 2 + 0.5)
            adjusted_sem_weight = sem_weight * sem_confidence
            total = adjusted_ce_weight + adjusted_sem_weight
            if total > 0:
                self._weights["cross_encoder"] = adjusted_ce_weight / total
                remaining = 1.0 - self._weights["cross_encoder"]
                sem_share = remaining * 0.6
                self._weights["semantic_similarity"] = sem_share
                self._weights["intent_similarity"] = remaining * 0.15
                self._weights["concept_overlap"] = remaining * 0.10
                self._weights["entity_overlap"] = remaining * 0.08
                self._weights["context_similarity"] = remaining * 0.07

        num_conflicts = vals["num_conflicts"]
        max_severity = vals["max_conflict_severity"]
        conflict_penalty = num_conflicts * self._conflict_penalty
        if max_severity > 0:
            conflict_penalty = min(conflict_penalty, max_severity)
        conflict_penalty = min(1.0, conflict_penalty)

        raw_score = (
            self._weights.get("cross_encoder", 0.4) * cross_encoder_score
            + self._weights.get("semantic_similarity", 0.25) * vals["semantic_similarity"]
            + self._weights.get("intent_similarity", 0.15) * vals["intent_similarity"]
            + self._weights.get("concept_overlap", 0.10) * vals["concept_overlap"]
            + self._weights.get("entity_overlap", 0.05) * vals["entity_overlap"]
            + self._weights.get("context_similarity", 0.05) * vals["context_similarity"]
        )

        final_score = raw_score * (1.0 - conflict_penalty)
        final_score = max(0.0, min(1.0, final_score))

        final_prediction = "Duplicate" if final_score >= 0.5 else "Non-Duplicate"

        explanation = self._build_explanation(
            strategy_name, cross_encoder_score, vals, final_score, final_prediction, conflict_penalty
        )

        return {
            "final_score": final_score,
            "final_prediction": final_prediction,
            "strategy": strategy_name,
            "cross_encoder_score": cross_encoder_score,
            "semantic_score": vals["semantic_similarity"],
            "fusion_score": final_score,
            "raw_fusion_score": raw_score,
            "weights_used": dict(self._weights),
            "conflict_penalty_applied": conflict_penalty,
            "num_conflicts": num_conflicts,
            "max_conflict_severity": max_severity,
            "explanation": explanation,
            "component_scores": {
                "cross_encoder": cross_encoder_score,
                "semantic_similarity": vals["semantic_similarity"],
                "intent_similarity": vals["intent_similarity"],
                "concept_overlap": vals["concept_overlap"],
                "entity_overlap": vals["entity_overlap"],
                "context_similarity": vals["context_similarity"],
            },
        }

    def _build_explanation(
        self,
        strategy: str,
        ce_score: float,
        vals: dict[str, float],
        final_score: float,
        final_prediction: str,
        conflict_penalty: float,
    ) -> str:
        parts = [f"Strategy: {strategy.replace('_', ' ').title()}"]
        parts.append(f"CrossEncoder={ce_score:.2f}")
        parts.append(f"Semantic={vals['semantic_similarity']:.2f}")
        if vals["num_conflicts"] > 0:
            parts.append(f"Conflicts={vals['num_conflicts']}(penalty={conflict_penalty:.2f})")
        parts.append(f"Final={final_score:.2f} → {final_prediction}")
        return " | ".join(parts)

    def _learned_weighting(self, cross_encoder_score: float, assessment: dict[str, Any] | None) -> dict[str, Any]:
        result = self._fuse(cross_encoder_score, assessment)
        result["strategy"] = "learned_weighting"
        result["explanation"] = (
            "Learned weighting (placeholder) — uses default weights. Train a regression model on validation data to set optimal weights."
        )
        return result
