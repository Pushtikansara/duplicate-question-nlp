from __future__ import annotations

import time
from typing import Any

from ares.query_understanding.complexity_models import ComplexityAnalysis
from ares.query_understanding.decision_trace_models import (
    ComplexityTrace,
    ConfidenceBreakdown,
    DecisionPath,
    DecisionTrace,
    EntityTrace,
    EvidenceDetail,
    QuestionTypeTrace,
    RelationshipTrace,
    RoutingTrace,
)
from ares.query_understanding.entity_models import EntityResult
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.relationship_models import RelationshipAnalysis
from ares.query_understanding.router_models import RoutingDecision
from ares.query_understanding.type_models import QuestionTypeResult


class DecisionTraceBuilder:
    version: str = "1.4.0"

    def build(self, analysis: QueryAnalysis) -> DecisionTrace:
        start = time.time()

        qt_trace = self._build_question_type_trace(analysis.question_type)
        et_trace = self._build_entity_trace(analysis.entity_analysis)
        rt_trace = self._build_relationship_trace(analysis.relationship_analysis)
        ct_trace = self._build_complexity_trace(analysis.complexity_analysis)
        rout_trace = self._build_routing_trace(analysis.routing_decision)

        cb = self._build_confidence_breakdown(analysis)
        dp = self._build_decision_path(analysis)

        triggered = self._collect_triggered_rules(qt_trace, et_trace, rt_trace, ct_trace, rout_trace)
        rejected = self._collect_rejected_rules(rout_trace)
        evidence = self._collect_supporting_evidence(qt_trace, et_trace, rt_trace, ct_trace, rout_trace)

        overall_risk = analysis.routing_decision.risk_level if analysis.routing_decision else "low"
        overall_complexity = (
            analysis.complexity_analysis.difficulty_level if analysis.complexity_analysis else "Very Easy"
        )

        summary = self._build_summary(analysis, rout_trace)

        warnings = self._collect_warnings(analysis)
        recommendations = self._collect_recommendations(analysis)

        elapsed = round((time.time() - start) * 1000, 2)

        return DecisionTrace(
            pipeline_version=self.version,
            processing_time_ms=elapsed,
            summary=summary,
            confidence=cb.overall,
            overall_risk=overall_risk,
            overall_complexity=overall_complexity,
            question_type_trace=qt_trace,
            entity_trace=et_trace,
            relationship_trace=rt_trace,
            complexity_trace=ct_trace,
            routing_trace=rout_trace,
            triggered_rules=triggered,
            rejected_rules=rejected,
            supporting_evidence=evidence,
            confidence_breakdown=cb,
            decision_path=dp,
            warnings=warnings,
            recommendations=recommendations,
            metadata=self._build_metadata(analysis),
            version=self.version,
        )

    def _build_question_type_trace(self, qt: QuestionTypeResult | None) -> QuestionTypeTrace:
        if not qt:
            return QuestionTypeTrace(confidence=0.0, reason="no_question_type_data")
        evidence: list[EvidenceDetail] = []
        rules_fired: list[str] = []
        if qt.question_1_type:
            rules_fired.append(f"classify_q1:{qt.question_1_type}")
        if qt.question_2_type:
            rules_fired.append(f"classify_q2:{qt.question_2_type}")
        pair = qt.pair_type
        rules_fired.append(f"pair_analysis:{pair}")
        evidence.append(
            EvidenceDetail(
                rule_name="question_type_classification",
                rule_layer=1,
                matched_pattern=pair,
                evidence_tokens=[],
                confidence=qt.classification_confidence,
                explanation=qt.classification_reason,
                affected_words=[],
                processing_layer="question_type",
            )
        )
        return QuestionTypeTrace(
            question_1_type=qt.question_1_type,
            question_2_type=qt.question_2_type,
            pair_type=qt.pair_type,
            confidence=qt.classification_confidence,
            reason=qt.classification_reason,
            evidence=evidence,
            rules_fired=rules_fired,
        )

    def _build_entity_trace(self, er: EntityResult | None) -> EntityTrace:
        if not er:
            return EntityTrace(confidence=1.0, entity_relationship="no_entities")
        evidence: list[EvidenceDetail] = []
        rules_fired: list[str] = []
        e1 = er.entities_1 or []
        e2 = er.entities_2 or []
        for ent in e1:
            rules_fired.append(f"entity_detected_q1:{ent.entity_type}:{ent.text}")
            evidence.append(
                EvidenceDetail(
                    rule_name="entity_extraction",
                    rule_layer=2,
                    matched_pattern=f"extracted_{ent.entity_type}",
                    evidence_tokens=[ent.text],
                    confidence=ent.confidence,
                    explanation=f"Entity '{ent.text}' detected as {ent.entity_type} in Q1",
                    affected_words=[ent.text],
                    processing_layer="entity",
                )
            )
        for ent in e2:
            rules_fired.append(f"entity_detected_q2:{ent.entity_type}:{ent.text}")
            evidence.append(
                EvidenceDetail(
                    rule_name="entity_extraction",
                    rule_layer=2,
                    matched_pattern=f"extracted_{ent.entity_type}",
                    evidence_tokens=[ent.text],
                    confidence=ent.confidence,
                    explanation=f"Entity '{ent.text}' detected as {ent.entity_type} in Q2",
                    affected_words=[ent.text],
                    processing_layer="entity",
                )
            )
        for match in er.shared_entities or []:
            rules_fired.append(f"entity_match:{match.match_type}:{match.entity_1.text}")
            evidence.append(
                EvidenceDetail(
                    rule_name="entity_matching",
                    rule_layer=2,
                    matched_pattern=match.match_type,
                    evidence_tokens=[match.entity_1.text, match.entity_2.text],
                    confidence=match.similarity,
                    explanation=f"Entity '{match.entity_1.text}' matched '{match.entity_2.text}' ({match.match_type})",
                    affected_words=[match.entity_1.text, match.entity_2.text],
                    processing_layer="entity",
                )
            )
        return EntityTrace(
            entity_count_q1=len(e1),
            entity_count_q2=len(e2),
            shared_count=len(er.shared_entities or []),
            overlap_score=er.entity_overlap_score,
            entity_relationship=er.entity_relationship,
            confidence=er.entity_overlap_score if er.entity_overlap_score > 0 else 1.0,
            evidence=evidence,
            rules_fired=rules_fired,
        )

    def _build_relationship_trace(self, ra: RelationshipAnalysis | None) -> RelationshipTrace:
        if not ra:
            return RelationshipTrace(confidence=0.0)
        evidence: list[EvidenceDetail] = []
        rules_fired: list[str] = []
        for rel in ra.relationship_types or []:
            rules_fired.append(f"rel:{rel.relationship_type}:{rel.confidence:.2f}")
            for ev in rel.evidence or []:
                evidence.append(
                    EvidenceDetail(
                        rule_name=ev.rule_name or rel.relationship_type,
                        rule_layer=ev.rule_layer,
                        matched_pattern=ev.matched_pattern,
                        evidence_tokens=ev.tokens_q1 + ev.tokens_q2,
                        confidence=ev.confidence,
                        explanation=rel.human_explanation or rel.developer_explanation or rel.relationship_type,
                        affected_words=ev.tokens_q1 + ev.tokens_q2,
                        processing_layer=f"relationship_layer_{ev.rule_layer}",
                    )
                )
        return RelationshipTrace(
            relationship_count=len(ra.relationship_types or []),
            primary_relationship=ra.primary_relationship(),
            relationship_score=ra.relationship_score,
            confidence=ra.relationship_confidence,
            semantic_flags=ra.semantic_flags or [],
            risk_flags=ra.risk_flags or [],
            evidence=evidence,
            rules_fired=rules_fired,
        )

    def _build_complexity_trace(self, ca: ComplexityAnalysis | None) -> ComplexityTrace:
        if not ca:
            return ComplexityTrace(confidence=0.0)
        evidence: list[EvidenceDetail] = []
        rules_fired: list[str] = []
        metrics = {
            "lexical_complexity": ca.lexical_complexity,
            "syntactic_complexity": ca.syntactic_complexity,
            "semantic_complexity": ca.semantic_complexity,
            "entity_complexity": ca.entity_complexity,
            "ambiguity_score": ca.ambiguity_score,
            "readability_score": ca.readability_score,
            "comparison_difficulty": ca.comparison_difficulty,
        }
        for name, val in metrics.items():
            if val > 0:
                rules_fired.append(f"complexity:{name}:{val:.4f}")
                evidence.append(
                    EvidenceDetail(
                        rule_name=f"complexity_{name}",
                        rule_layer=4,
                        matched_pattern=f"{name}={val:.4f}",
                        evidence_tokens=[],
                        confidence=max(0.1, 1.0 - val),
                        explanation=f"{name} contributed {val:.4f} to complexity",
                        affected_words=[],
                        processing_layer="complexity",
                    )
                )
        return ComplexityTrace(
            overall_score=ca.overall_complexity_score,
            difficulty_level=ca.difficulty_level,
            lexical=ca.lexical_complexity,
            syntactic=ca.syntactic_complexity,
            semantic=ca.semantic_complexity,
            entity_complexity=ca.entity_complexity,
            ambiguity=ca.ambiguity_score,
            readability=ca.readability_score,
            comparison_difficulty=ca.comparison_difficulty,
            confidence=ca.confidence_estimate,
            risk_score=ca.risk_score,
            reasoning=ca.reasoning_summary,
            evidence=evidence,
            rules_fired=rules_fired,
        )

    def _build_routing_trace(self, rd: RoutingDecision | None) -> RoutingTrace:
        if not rd:
            return RoutingTrace(confidence=0.0)
        evidence: list[EvidenceDetail] = []
        strategy_scores: dict[str, float] = {}
        for rule in rd.triggered_rules or []:
            cat = rule.get("category", "")
            score = rule.get("score", 0.0)
            strategy_scores[cat] = max(strategy_scores.get(cat, 0.0), score)
            evidence.append(
                EvidenceDetail(
                    rule_name=rule.get("rule", ""),
                    rule_layer=5,
                    matched_pattern=rule.get("description", ""),
                    evidence_tokens=[],
                    confidence=rule.get("weight", 0.5),
                    explanation=f"Triggered rule '{rule.get('rule', '')}' with score {score:.4f}",
                    affected_words=[],
                    processing_layer="routing",
                )
            )
        all_strategies = ["fast_lexical", "baseline_classifier", "cross_encoder", "ensemble", "fallback"]
        rejected = [s for s in all_strategies if s != rd.selected_strategy and s not in strategy_scores]
        return RoutingTrace(
            selected_strategy=rd.selected_strategy,
            confidence=rd.confidence,
            risk_level=rd.risk_level,
            priority=rd.priority,
            strategy_scores=strategy_scores,
            triggered_rules=rd.triggered_rules or [],
            rejected_rules=rejected,
            reason_codes=rd.reason_codes or [],
            evidence=evidence,
        )

    def _build_confidence_breakdown(self, analysis: QueryAnalysis) -> ConfidenceBreakdown:
        qt_conf = analysis.question_type.classification_confidence if analysis.question_type else 0.0
        et_conf = analysis.entity_analysis.entity_overlap_score if analysis.entity_analysis else 0.0
        et_conf = et_conf if et_conf > 0 else 1.0
        rt_conf = analysis.relationship_analysis.relationship_confidence if analysis.relationship_analysis else 0.0
        ct_conf = analysis.complexity_analysis.confidence_estimate if analysis.complexity_analysis else 0.0
        rout_conf = analysis.routing_decision.confidence if analysis.routing_decision else 0.0
        overall = round((qt_conf * 0.1 + et_conf * 0.15 + rt_conf * 0.2 + ct_conf * 0.2 + rout_conf * 0.35), 4)
        return ConfidenceBreakdown(
            question_type=round(qt_conf, 4),
            entity=round(et_conf, 4),
            relationship=round(rt_conf, 4),
            complexity=round(ct_conf, 4),
            routing=round(rout_conf, 4),
            overall=round(overall, 4),
        )

    def _build_decision_path(self, analysis: QueryAnalysis) -> DecisionPath:
        layers = ["question_type", "entity", "relationship", "complexity", "routing"]
        flow: list[str] = []
        if analysis.question_type and analysis.question_type.pair_type:
            flow.append(f"Classified pair as {analysis.question_type.pair_type}")
        if analysis.entity_analysis:
            flow.append(
                f"Found {len(analysis.entity_analysis.entities_1 or [])} entities in Q1, {len(analysis.entity_analysis.entities_2 or [])} in Q2"
            )
        if analysis.relationship_analysis and analysis.relationship_analysis.relationship_types:
            flow.append(f"Primary relationship: {analysis.relationship_analysis.primary_relationship()}")
        if analysis.complexity_analysis:
            flow.append(
                f"Complexity: {analysis.complexity_analysis.difficulty_level} ({analysis.complexity_analysis.overall_complexity_score:.4f})"
            )
        if analysis.routing_decision:
            flow.append(f"Routing decision: {analysis.routing_decision.selected_strategy}")
        return DecisionPath(
            layers_traversed=layers,
            current_layer="routing",
            decision_flow=flow,
        )

    def _build_summary(self, analysis: QueryAnalysis, rout_trace: RoutingTrace) -> str:
        parts: list[str] = []
        if analysis.question_type:
            parts.append(f"Pair type: {analysis.question_type.pair_type}")
        if analysis.relationship_analysis:
            parts.append(f"Primary: {analysis.relationship_analysis.primary_relationship()}")
        if analysis.complexity_analysis:
            parts.append(f"Complexity: {analysis.complexity_analysis.difficulty_level}")
        if analysis.routing_decision:
            parts.append(f"Routed to: {analysis.routing_decision.selected_strategy}")
        return " | ".join(parts) if parts else "No analysis data"

    def _collect_triggered_rules(
        self,
        qt: QuestionTypeTrace,
        et: EntityTrace,
        rt: RelationshipTrace,
        ct: ComplexityTrace,
        rout: RoutingTrace,
    ) -> list[str]:
        result: list[str] = []
        result.extend(qt.rules_fired)
        result.extend(et.rules_fired)
        result.extend(rt.rules_fired)
        result.extend(ct.rules_fired)
        for r in rout.triggered_rules:
            result.append(f"routing:{r.get('rule', 'unknown')}")
        return result

    def _collect_rejected_rules(self, rout: RoutingTrace) -> list[str]:
        rejected: list[str] = []
        for s in rout.rejected_rules:
            rejected.append(f"strategy_rejected:{s}")
        return rejected

    def _collect_supporting_evidence(
        self,
        qt: QuestionTypeTrace,
        et: EntityTrace,
        rt: RelationshipTrace,
        ct: ComplexityTrace,
        rout: RoutingTrace,
    ) -> list[EvidenceDetail]:
        evidence: list[EvidenceDetail] = []
        evidence.extend(qt.evidence)
        evidence.extend(et.evidence)
        evidence.extend(rt.evidence)
        evidence.extend(ct.evidence)
        evidence.extend(rout.evidence)
        return evidence

    def _collect_warnings(self, analysis: QueryAnalysis) -> list[str]:
        warnings: list[str] = []
        if analysis.relationship_analysis and analysis.relationship_analysis.risk_flags:
            for flag in analysis.relationship_analysis.risk_flags:
                warnings.append(f"Risk flag: {flag}")
        if analysis.complexity_analysis and analysis.complexity_analysis.ambiguity_score > 0.5:
            warnings.append("High ambiguity detected")
        if analysis.complexity_analysis and analysis.complexity_analysis.overall_complexity_score > 0.7:
            warnings.append("Very high complexity")
        return warnings

    def _collect_recommendations(self, analysis: QueryAnalysis) -> list[str]:
        recs: list[str] = []
        if analysis.routing_decision:
            strat = analysis.routing_decision.selected_strategy
            if strat == "cross_encoder":
                recs.append("Consider ensemble for higher confidence")
            elif strat == "fast_lexical":
                recs.append("Simple case, fast path sufficient")
            elif strat == "fallback":
                recs.append("Input may need review")
        if analysis.complexity_analysis and analysis.complexity_analysis.overall_complexity_score > 0.5:
            recs.append("Review complex comparison for edge cases")
        return recs

    def _build_metadata(self, analysis: QueryAnalysis) -> dict[str, Any]:
        return {
            "original_length_1": len(analysis.original_question_1),
            "original_length_2": len(analysis.original_question_2),
            "has_both_inputs": bool(analysis.original_question_1 and analysis.original_question_2),
            "pipeline_processing_ms": analysis.processing_time_ms,
        }
