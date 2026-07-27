from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PIPELINE_VERSION = "1.4.0"


@dataclass
class EvidenceDetail:
    rule_name: str = ""
    rule_layer: int = 0
    matched_pattern: str = ""
    evidence_tokens: list[str] = field(default_factory=list)
    confidence: float = 0.0
    explanation: str = ""
    affected_words: list[str] = field(default_factory=list)
    processing_layer: str = ""


@dataclass
class QuestionTypeTrace:
    question_1_type: str = ""
    question_2_type: str = ""
    pair_type: str = ""
    confidence: float = 0.0
    reason: str = ""
    evidence: list[EvidenceDetail] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)


@dataclass
class EntityTrace:
    entity_count_q1: int = 0
    entity_count_q2: int = 0
    shared_count: int = 0
    overlap_score: float = 0.0
    entity_relationship: str = ""
    confidence: float = 0.0
    evidence: list[EvidenceDetail] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)


@dataclass
class RelationshipTrace:
    relationship_count: int = 0
    primary_relationship: str = ""
    relationship_score: float = 0.0
    confidence: float = 0.0
    semantic_flags: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    evidence: list[EvidenceDetail] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)


@dataclass
class ComplexityTrace:
    overall_score: float = 0.0
    difficulty_level: str = ""
    lexical: float = 0.0
    syntactic: float = 0.0
    semantic: float = 0.0
    entity_complexity: float = 0.0
    ambiguity: float = 0.0
    readability: float = 0.0
    comparison_difficulty: float = 0.0
    confidence: float = 0.0
    risk_score: float = 0.0
    reasoning: str = ""
    evidence: list[EvidenceDetail] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)


@dataclass
class RoutingTrace:
    selected_strategy: str = ""
    confidence: float = 0.0
    risk_level: str = ""
    priority: str = ""
    strategy_scores: dict[str, float] = field(default_factory=dict)
    triggered_rules: list[dict[str, Any]] = field(default_factory=list)
    rejected_rules: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    evidence: list[EvidenceDetail] = field(default_factory=list)


@dataclass
class ConfidenceBreakdown:
    question_type: float = 0.0
    entity: float = 0.0
    relationship: float = 0.0
    complexity: float = 0.0
    routing: float = 0.0
    overall: float = 0.0


@dataclass
class DecisionPath:
    layers_traversed: list[str] = field(default_factory=list)
    current_layer: str = ""
    decision_flow: list[str] = field(default_factory=list)


@dataclass
class DecisionTrace:
    pipeline_version: str = PIPELINE_VERSION
    processing_time_ms: float = 0.0

    summary: str = ""
    confidence: float = 0.0
    overall_risk: str = ""
    overall_complexity: str = ""

    question_type_trace: QuestionTypeTrace = field(default_factory=QuestionTypeTrace)
    entity_trace: EntityTrace = field(default_factory=EntityTrace)
    relationship_trace: RelationshipTrace = field(default_factory=RelationshipTrace)
    complexity_trace: ComplexityTrace = field(default_factory=ComplexityTrace)
    routing_trace: RoutingTrace = field(default_factory=RoutingTrace)

    triggered_rules: list[str] = field(default_factory=list)
    rejected_rules: list[str] = field(default_factory=list)
    supporting_evidence: list[EvidenceDetail] = field(default_factory=list)

    confidence_breakdown: ConfidenceBreakdown = field(default_factory=ConfidenceBreakdown)

    decision_path: DecisionPath = field(default_factory=DecisionPath)

    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
    version: str = PIPELINE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_version": self.pipeline_version,
            "processing_time_ms": self.processing_time_ms,
            "summary": self.summary,
            "confidence": self.confidence,
            "overall_risk": self.overall_risk,
            "overall_complexity": self.overall_complexity,
            "question_type_trace": _qt_to_dict(self.question_type_trace),
            "entity_trace": _et_to_dict(self.entity_trace),
            "relationship_trace": _rt_to_dict(self.relationship_trace),
            "complexity_trace": _ct_to_dict(self.complexity_trace),
            "routing_trace": _rout_t_to_dict(self.routing_trace),
            "triggered_rules": self.triggered_rules,
            "rejected_rules": self.rejected_rules,
            "supporting_evidence": [
                ev.to_dict() if hasattr(ev, "to_dict") else _ed_to_dict(ev) for ev in self.supporting_evidence
            ],
            "confidence_breakdown": {
                "question_type": self.confidence_breakdown.question_type,
                "entity": self.confidence_breakdown.entity,
                "relationship": self.confidence_breakdown.relationship,
                "complexity": self.confidence_breakdown.complexity,
                "routing": self.confidence_breakdown.routing,
                "overall": self.confidence_breakdown.overall,
            },
            "decision_path": {
                "layers_traversed": self.decision_path.layers_traversed,
                "current_layer": self.decision_path.current_layer,
                "decision_flow": self.decision_path.decision_flow,
            },
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionTrace:
        qt = data.get("question_type_trace", {})
        et = data.get("entity_trace", {})
        rt = data.get("relationship_trace", {})
        ct = data.get("complexity_trace", {})
        rout = data.get("routing_trace", {})
        cb = data.get("confidence_breakdown", {})
        dp = data.get("decision_path", {})
        se = data.get("supporting_evidence", [])

        return cls(
            pipeline_version=data.get("pipeline_version", PIPELINE_VERSION),
            processing_time_ms=data.get("processing_time_ms", 0.0),
            summary=data.get("summary", ""),
            confidence=data.get("confidence", 0.0),
            overall_risk=data.get("overall_risk", ""),
            overall_complexity=data.get("overall_complexity", ""),
            question_type_trace=_qt_from_dict(qt),
            entity_trace=_et_from_dict(et),
            relationship_trace=_rt_from_dict(rt),
            complexity_trace=_ct_from_dict(ct),
            routing_trace=_rout_t_from_dict(rout),
            triggered_rules=data.get("triggered_rules", []),
            rejected_rules=data.get("rejected_rules", []),
            supporting_evidence=[EvidenceDetail(**e) if isinstance(e, dict) else e for e in se],
            confidence_breakdown=ConfidenceBreakdown(
                question_type=cb.get("question_type", 0.0),
                entity=cb.get("entity", 0.0),
                relationship=cb.get("relationship", 0.0),
                complexity=cb.get("complexity", 0.0),
                routing=cb.get("routing", 0.0),
                overall=cb.get("overall", 0.0),
            ),
            decision_path=DecisionPath(
                layers_traversed=dp.get("layers_traversed", []),
                current_layer=dp.get("current_layer", ""),
                decision_flow=dp.get("decision_flow", []),
            ),
            warnings=data.get("warnings", []),
            recommendations=data.get("recommendations", []),
            metadata=data.get("metadata", {}),
            version=data.get("version", PIPELINE_VERSION),
        )


def _ed_to_dict(ed: EvidenceDetail) -> dict[str, Any]:
    return {
        "rule_name": ed.rule_name,
        "rule_layer": ed.rule_layer,
        "matched_pattern": ed.matched_pattern,
        "evidence_tokens": ed.evidence_tokens,
        "confidence": ed.confidence,
        "explanation": ed.explanation,
        "affected_words": ed.affected_words,
        "processing_layer": ed.processing_layer,
    }


def _qt_to_dict(qt: QuestionTypeTrace) -> dict[str, Any]:
    return {
        "question_1_type": qt.question_1_type,
        "question_2_type": qt.question_2_type,
        "pair_type": qt.pair_type,
        "confidence": qt.confidence,
        "reason": qt.reason,
        "evidence": [_ed_to_dict(e) for e in qt.evidence],
        "rules_fired": qt.rules_fired,
    }


def _et_to_dict(et: EntityTrace) -> dict[str, Any]:
    return {
        "entity_count_q1": et.entity_count_q1,
        "entity_count_q2": et.entity_count_q2,
        "shared_count": et.shared_count,
        "overlap_score": et.overlap_score,
        "entity_relationship": et.entity_relationship,
        "confidence": et.confidence,
        "evidence": [_ed_to_dict(e) for e in et.evidence],
        "rules_fired": et.rules_fired,
    }


def _rt_to_dict(rt: RelationshipTrace) -> dict[str, Any]:
    return {
        "relationship_count": rt.relationship_count,
        "primary_relationship": rt.primary_relationship,
        "relationship_score": rt.relationship_score,
        "confidence": rt.confidence,
        "semantic_flags": rt.semantic_flags,
        "risk_flags": rt.risk_flags,
        "evidence": [_ed_to_dict(e) for e in rt.evidence],
        "rules_fired": rt.rules_fired,
    }


def _ct_to_dict(ct: ComplexityTrace) -> dict[str, Any]:
    return {
        "overall_score": ct.overall_score,
        "difficulty_level": ct.difficulty_level,
        "lexical": ct.lexical,
        "syntactic": ct.syntactic,
        "semantic": ct.semantic,
        "entity_complexity": ct.entity_complexity,
        "ambiguity": ct.ambiguity,
        "readability": ct.readability,
        "comparison_difficulty": ct.comparison_difficulty,
        "confidence": ct.confidence,
        "risk_score": ct.risk_score,
        "reasoning": ct.reasoning,
        "evidence": [_ed_to_dict(e) for e in ct.evidence],
        "rules_fired": ct.rules_fired,
    }


def _rout_t_to_dict(rt: RoutingTrace) -> dict[str, Any]:
    return {
        "selected_strategy": rt.selected_strategy,
        "confidence": rt.confidence,
        "risk_level": rt.risk_level,
        "priority": rt.priority,
        "strategy_scores": rt.strategy_scores,
        "triggered_rules": rt.triggered_rules,
        "rejected_rules": rt.rejected_rules,
        "reason_codes": rt.reason_codes,
        "evidence": [_ed_to_dict(e) for e in rt.evidence],
    }


def _qt_from_dict(data: dict[str, Any]) -> QuestionTypeTrace:
    return QuestionTypeTrace(
        question_1_type=data.get("question_1_type", ""),
        question_2_type=data.get("question_2_type", ""),
        pair_type=data.get("pair_type", ""),
        confidence=data.get("confidence", 0.0),
        reason=data.get("reason", ""),
        evidence=[EvidenceDetail(**e) for e in data.get("evidence", [])],
        rules_fired=data.get("rules_fired", []),
    )


def _et_from_dict(data: dict[str, Any]) -> EntityTrace:
    return EntityTrace(
        entity_count_q1=data.get("entity_count_q1", 0),
        entity_count_q2=data.get("entity_count_q2", 0),
        shared_count=data.get("shared_count", 0),
        overlap_score=data.get("overlap_score", 0.0),
        entity_relationship=data.get("entity_relationship", ""),
        confidence=data.get("confidence", 0.0),
        evidence=[EvidenceDetail(**e) for e in data.get("evidence", [])],
        rules_fired=data.get("rules_fired", []),
    )


def _rt_from_dict(data: dict[str, Any]) -> RelationshipTrace:
    return RelationshipTrace(
        relationship_count=data.get("relationship_count", 0),
        primary_relationship=data.get("primary_relationship", ""),
        relationship_score=data.get("relationship_score", 0.0),
        confidence=data.get("confidence", 0.0),
        semantic_flags=data.get("semantic_flags", []),
        risk_flags=data.get("risk_flags", []),
        evidence=[EvidenceDetail(**e) for e in data.get("evidence", [])],
        rules_fired=data.get("rules_fired", []),
    )


def _ct_from_dict(data: dict[str, Any]) -> ComplexityTrace:
    return ComplexityTrace(
        overall_score=data.get("overall_score", 0.0),
        difficulty_level=data.get("difficulty_level", ""),
        lexical=data.get("lexical", 0.0),
        syntactic=data.get("syntactic", 0.0),
        semantic=data.get("semantic", 0.0),
        entity_complexity=data.get("entity_complexity", 0.0),
        ambiguity=data.get("ambiguity", 0.0),
        readability=data.get("readability", 0.0),
        comparison_difficulty=data.get("comparison_difficulty", 0.0),
        confidence=data.get("confidence", 0.0),
        risk_score=data.get("risk_score", 0.0),
        reasoning=data.get("reasoning", ""),
        evidence=[EvidenceDetail(**e) for e in data.get("evidence", [])],
        rules_fired=data.get("rules_fired", []),
    )


def _rout_t_from_dict(data: dict[str, Any]) -> RoutingTrace:
    return RoutingTrace(
        selected_strategy=data.get("selected_strategy", ""),
        confidence=data.get("confidence", 0.0),
        risk_level=data.get("risk_level", ""),
        priority=data.get("priority", ""),
        strategy_scores=data.get("strategy_scores", {}),
        triggered_rules=data.get("triggered_rules", []),
        rejected_rules=data.get("rejected_rules", []),
        reason_codes=data.get("reason_codes", []),
        evidence=[EvidenceDetail(**e) for e in data.get("evidence", [])],
    )
