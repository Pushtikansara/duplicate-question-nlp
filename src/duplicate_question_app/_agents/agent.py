from __future__ import annotations

import time
import uuid
from typing import Any

from duplicate_question_app._agents.agent_result import AgentResult
from duplicate_question_app._agents.interfaces import CognitiveAgent
from duplicate_question_app._reasoning.reasoning_result import (
    Evidence,
    EvidenceType,
    ReasoningResult,
)
from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


def _make_id() -> str:
    return uuid.uuid4().hex[:12]


def _ensure_evidence(
    evidence_list: list[Evidence],
    hyp_id: str,
    etype: EvidenceType,
    text: str,
    confidence: float = 0.8,
    weight: float = 1.0,
    provenance: str = "",
) -> Evidence:
    return Evidence(
        id=_make_id(),
        hypothesis_id=hyp_id,
        evidence_type=etype,
        text=text,
        confidence=confidence,
        source_premises=[],
        weight=weight,
        provenance=provenance or "agent",
    )


class IntentAgent(CognitiveAgent):
    @property
    def name(self) -> str:
        return "intent_agent"

    @property
    def weight(self) -> float:
        return 1.0

    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult:
        start = time.perf_counter()
        evidence: list[Evidence] = []
        warnings: list[str] = []
        confidence = 0.5
        recommendation = "uncertain"

        intent_a = rep_a.intent_summary or ""
        intent_b = rep_b.intent_summary or ""

        if not intent_a and not intent_b:
            warnings.append("No intent data available for either question")
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.NEUTRAL,
                    "No intent data available",
                    confidence=0.5,
                    provenance="intent_agent",
                )
            )
            confidence = 0.5
            recommendation = "uncertain"
        elif not intent_a or not intent_b:
            warnings.append("Intent data missing for one question")
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.CONTRADICTING,
                    "Intent data missing for one question",
                    confidence=0.6,
                    provenance="intent_agent",
                )
            )
            confidence = 0.4
            recommendation = "uncertain"
        else:
            if assessment and assessment.intent_similarity.score > 0.7:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.SUPPORTING,
                        f"Intent similarity {assessment.intent_similarity.score:.2f}: intents match closely",
                        confidence=assessment.intent_similarity.confidence,
                        provenance="intent_agent",
                    )
                )
                confidence = assessment.intent_similarity.score * assessment.intent_similarity.confidence
                recommendation = "duplicate"
            elif assessment and assessment.intent_similarity.score < 0.3:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.CONTRADICTING,
                        f"Intent similarity {assessment.intent_similarity.score:.2f}: intents diverge",
                        confidence=0.8,
                        provenance="intent_agent",
                    )
                )
                confidence = 0.3
                recommendation = "not_duplicate"
            else:
                intent_match = intent_a.lower().strip() == intent_b.lower().strip()
                if intent_match:
                    evidence.append(
                        _ensure_evidence(
                            evidence,
                            "",
                            EvidenceType.SUPPORTING,
                            "Intent summaries match exactly",
                            confidence=0.9,
                            provenance="intent_agent",
                        )
                    )
                    confidence = 0.8
                    recommendation = "duplicate"
                else:
                    evidence.append(
                        _ensure_evidence(
                            evidence,
                            "",
                            EvidenceType.NEUTRAL,
                            f"Intent A: '{intent_a[:60]}' vs Intent B: '{intent_b[:60]}'",
                            confidence=0.5,
                            provenance="intent_agent",
                        )
                    )
                    confidence = 0.4
                    recommendation = "uncertain"

        elapsed = (time.perf_counter() - start) * 1000
        return AgentResult(
            agent_name=self.name,
            confidence=max(0.0, min(1.0, confidence)),
            recommendation=recommendation,
            supporting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.SUPPORTING],
            contradicting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.CONTRADICTING],
            warnings=warnings,
            metadata={"intent_a": intent_a[:60], "intent_b": intent_b[:60]},
            processing_time_ms=elapsed,
        )


class SemanticAgent(CognitiveAgent):
    @property
    def name(self) -> str:
        return "semantic_agent"

    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult:
        start = time.perf_counter()
        evidence: list[Evidence] = []
        warnings: list[str] = []
        confidence = 0.5
        recommendation = "uncertain"

        if assessment is None:
            warnings.append("No semantic assessment provided")
            confidence = 0.5
            recommendation = "uncertain"
        else:
            sem_sim = assessment.semantic_similarity
            confidence = 0.5

            concept_a_count = len(rep_a.concepts) if rep_a.concepts else 0
            concept_b_count = len(rep_b.concepts) if rep_b.concepts else 0
            overlap_score = assessment.concept_overlap.overlap_score if assessment.concept_overlap else 0.0

            combined_sem = sem_sim * 0.6 + overlap_score * 0.4
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.SUPPORTING,
                    f"Semantic similarity: {sem_sim:.2f}, concept overlap: {overlap_score:.2f}",
                    confidence=combined_sem,
                    weight=0.8,
                    provenance="semantic_agent",
                )
            )

            if reasoning_result:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.SUPPORTING,
                        f"Reasoning confidence: {reasoning_result.confidence:.2f}, "
                        f"decision: {reasoning_result.decision}",
                        confidence=reasoning_result.confidence,
                        weight=0.6,
                        provenance="semantic_agent",
                    )
                )

                if reasoning_result.confidence < 0.3:
                    warnings.append("Low reasoning confidence")

            if sem_sim >= 0.7 and combined_sem >= 0.5:
                recommendation = "duplicate"
                confidence = combined_sem
            elif sem_sim <= 0.3 and combined_sem <= 0.4:
                recommendation = "not_duplicate"
                confidence = 1.0 - combined_sem
            else:
                recommendation = "uncertain"
                confidence = 0.5

            if reasoning_result and reasoning_result.decision != "uncertain":
                if reasoning_result.decision == recommendation:
                    evidence.append(
                        _ensure_evidence(
                            evidence,
                            "",
                            EvidenceType.SUPPORTING,
                            f"Aligns with reasoning engine ({reasoning_result.decision})",
                            confidence=0.9,
                            weight=0.4,
                            provenance="semantic_agent",
                        )
                    )
                elif recommendation != "uncertain":
                    evidence.append(
                        _ensure_evidence(
                            evidence,
                            "",
                            EvidenceType.CONTRADICTING,
                            f"Disagrees with reasoning engine: agent says {recommendation}, "
                            f"engine says {reasoning_result.decision}",
                            confidence=0.7,
                            weight=0.5,
                            provenance="semantic_agent",
                        )
                    )
                    warnings.append(
                        f"Disagreement with reasoning engine: {recommendation} vs {reasoning_result.decision}"
                    )

            if concept_a_count != concept_b_count:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.NEUTRAL,
                        f"Concept count mismatch: A={concept_a_count}, B={concept_b_count}",
                        confidence=0.5,
                        weight=0.2,
                        provenance="semantic_agent",
                    )
                )

        elapsed = (time.perf_counter() - start) * 1000
        return AgentResult(
            agent_name=self.name,
            confidence=max(0.0, min(1.0, confidence)),
            recommendation=recommendation,
            supporting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.SUPPORTING],
            contradicting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.CONTRADICTING],
            warnings=warnings,
            metadata={"semantic_similarity": getattr(assessment, "semantic_similarity", None) if assessment else None},
            processing_time_ms=elapsed,
        )


class EntityAgent(CognitiveAgent):
    @property
    def name(self) -> str:
        return "entity_agent"

    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult:
        start = time.perf_counter()
        evidence: list[Evidence] = []
        warnings: list[str] = []
        confidence = 0.5
        recommendation = "uncertain"

        entities_a: list[dict[str, Any]] = rep_a.entities or []
        entities_b: list[dict[str, Any]] = rep_b.entities or []

        entity_labels_a = {e.get("label", "") for e in entities_a if isinstance(e, dict)}
        entity_labels_b = {e.get("label", "") for e in entities_b if isinstance(e, dict)}

        shared = entity_labels_a & entity_labels_b
        only_in_a = entity_labels_a - entity_labels_b
        only_in_b = entity_labels_b - entity_labels_a

        if shared:
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.SUPPORTING,
                    f"Shared entities ({len(shared)}): {', '.join(list(shared)[:5])}",
                    confidence=0.8,
                    weight=0.6,
                    provenance="entity_agent",
                )
            )

        if only_in_a:
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.CONTRADICTING,
                    f"Missing from B ({len(only_in_a)}): {', '.join(list(only_in_a)[:5])}",
                    confidence=0.6,
                    weight=0.4,
                    provenance="entity_agent",
                )
            )

        if only_in_b:
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.CONTRADICTING,
                    f"Missing from A ({len(only_in_b)}): {', '.join(list(only_in_b)[:5])}",
                    confidence=0.6,
                    weight=0.4,
                    provenance="entity_agent",
                )
            )

        if assessment and assessment.entity_overlap:
            eo = assessment.entity_overlap
            if eo.shared_entities:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.SUPPORTING,
                        f"Entity overlap score: {eo.overlap_score:.2f}",
                        confidence=min(1.0, eo.overlap_score),
                        weight=0.5,
                        provenance="entity_agent",
                    )
                )
            if eo.conflicts:
                for c in eo.conflicts[:5]:
                    evidence.append(
                        _ensure_evidence(
                            evidence,
                            "",
                            EvidenceType.CONTRADICTING,
                            f"Entity conflict: {c}",
                            confidence=0.8,
                            weight=0.5,
                            provenance="entity_agent",
                        )
                    )
                warnings.append(f"Entity conflicts detected: {len(eo.conflicts)}")

        if not entities_a and not entities_b:
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.NEUTRAL,
                    "No entities in either question",
                    confidence=0.5,
                    weight=0.2,
                    provenance="entity_agent",
                )
            )
            confidence = 0.5
            recommendation = "uncertain"
        elif len(shared) > max(len(only_in_a), len(only_in_b)):
            recommendation = "duplicate"
            confidence = len(shared) / max(1, len(shared) + len(only_in_a) + len(only_in_b))
        elif len(only_in_a) + len(only_in_b) > len(shared) and (only_in_a or only_in_b):
            recommendation = "not_duplicate"
            confidence = (len(only_in_a) + len(only_in_b)) / max(1, len(entity_labels_a | entity_labels_b))
        else:
            recommendation = "uncertain"
            confidence = 0.5

        confidence = max(0.0, min(1.0, confidence))

        elapsed = (time.perf_counter() - start) * 1000
        return AgentResult(
            agent_name=self.name,
            confidence=confidence,
            recommendation=recommendation,
            supporting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.SUPPORTING],
            contradicting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.CONTRADICTING],
            warnings=warnings,
            metadata={"shared_entities": len(shared), "only_in_a": len(only_in_a), "only_in_b": len(only_in_b)},
            processing_time_ms=elapsed,
        )


class RelationAgent(CognitiveAgent):
    @property
    def name(self) -> str:
        return "relation_agent"

    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult:
        start = time.perf_counter()
        evidence: list[Evidence] = []
        warnings: list[str] = []
        confidence = 0.5
        recommendation = "uncertain"

        relations_a = rep_a.relationships or []
        relations_b = rep_b.relationships or []

        if not relations_a and not relations_b:
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.NEUTRAL,
                    "No relations in either representation",
                    confidence=0.5,
                    weight=0.2,
                    provenance="relation_agent",
                )
            )
        elif not relations_a or not relations_b:
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.CONTRADICTING,
                    "Relations present in only one representation",
                    confidence=0.6,
                    weight=0.5,
                    provenance="relation_agent",
                )
            )
            warnings.append("Asymmetric relation data")
        else:
            if assessment and assessment.relation_similarity:
                rs = assessment.relation_similarity
                if rs.score > 0.7:
                    evidence.append(
                        _ensure_evidence(
                            evidence,
                            "",
                            EvidenceType.SUPPORTING,
                            f"Relation similarity: {rs.score:.2f} ({len(rs.matching_relations)} matching chains)",
                            confidence=rs.score,
                            weight=0.7,
                            provenance="relation_agent",
                        )
                    )
                    recommendation = "duplicate"
                    confidence = rs.score
                elif rs.score < 0.3:
                    evidence.append(
                        _ensure_evidence(
                            evidence,
                            "",
                            EvidenceType.CONTRADICTING,
                            f"Relation similarity: {rs.score:.2f} (low overlap)",
                            confidence=0.8,
                            weight=0.7,
                            provenance="relation_agent",
                        )
                    )
                    recommendation = "not_duplicate"
                    confidence = 1.0 - rs.score
                else:
                    if rs.missing_in_a:
                        evidence.append(
                            _ensure_evidence(
                                evidence,
                                "",
                                EvidenceType.CONTRADICTING,
                                f"Missing from A: {len(rs.missing_in_a)} relations",
                                confidence=0.6,
                                weight=0.4,
                                provenance="relation_agent",
                            )
                        )
                    if rs.missing_in_b:
                        evidence.append(
                            _ensure_evidence(
                                evidence,
                                "",
                                EvidenceType.CONTRADICTING,
                                f"Missing from B: {len(rs.missing_in_b)} relations",
                                confidence=0.6,
                                weight=0.4,
                                provenance="relation_agent",
                            )
                        )
                    if rs.matching_relations:
                        evidence.append(
                            _ensure_evidence(
                                evidence,
                                "",
                                EvidenceType.SUPPORTING,
                                f"Matching relations: {len(rs.matching_relations)}",
                                confidence=0.7,
                                weight=0.5,
                                provenance="relation_agent",
                            )
                        )
                    recommendation = "uncertain"
                    confidence = 0.5

                if rs.missing_in_a or rs.missing_in_b:
                    warnings.append("Missing relation links detected")

        if not relations_a and not relations_b:
            recommendation = "uncertain"
            confidence = 0.5

        if relations_a or relations_b:
            if recommendation == "uncertain" and assessment and assessment.relation_similarity:
                pass

            type_a = {r.get("relation_type", "") for r in relations_a if isinstance(r, dict)}
            type_b = {r.get("relation_type", "") for r in relations_b if isinstance(r, dict)}
            shared_types = type_a & type_b
            if shared_types:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.SUPPORTING,
                        f"Shared relation types: {', '.join(shared_types)}",
                        confidence=0.7,
                        weight=0.3,
                        provenance="relation_agent",
                    )
                )

        confidence = max(0.0, min(1.0, confidence))

        elapsed = (time.perf_counter() - start) * 1000
        return AgentResult(
            agent_name=self.name,
            confidence=confidence,
            recommendation=recommendation,
            supporting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.SUPPORTING],
            contradicting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.CONTRADICTING],
            warnings=warnings,
            metadata={"relations_a": len(relations_a), "relations_b": len(relations_b)},
            processing_time_ms=elapsed,
        )


class ConflictAgent(CognitiveAgent):
    @property
    def name(self) -> str:
        return "conflict_agent"

    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult:
        start = time.perf_counter()
        evidence: list[Evidence] = []
        warnings: list[str] = []
        conflict_count = 0

        if assessment and assessment.conflicts:
            for c in assessment.conflicts:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.CONTRADICTING,
                        f"Conflict [{c.conflict_type}]: {c.description}",
                        confidence=c.severity,
                        weight=c.severity,
                        provenance=f"conflict_agent/{c.conflict_type}",
                    )
                )
                conflict_count += 1

        if reasoning_result:
            for e in reasoning_result.contradicting_evidence:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.CONTRADICTING,
                        f"Reasoning contradiction: {e.text}",
                        confidence=e.confidence,
                        weight=e.weight,
                        provenance="conflict_agent/reasoning",
                    )
                )
                conflict_count += 1

            hypotheses = reasoning_result.hypotheses
            dup_hyp = [h for h in hypotheses if h.label and h.label.value == "duplicate"]
            nondup_hyp = [h for h in hypotheses if h.label and h.label.value == "not_duplicate"]
            if (
                dup_hyp
                and nondup_hyp
                and len(dup_hyp[0].supporting_premises) > 0
                and len(nondup_hyp[0].supporting_premises) > 0
            ):
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.CONTRADICTING,
                        "Both duplicate and non-duplicate hypotheses have supporting premises",
                        confidence=0.7,
                        weight=0.6,
                        provenance="conflict_agent/reasoning_conflict",
                    )
                )
                warnings.append("Both hypotheses have supporting evidence")

            if reasoning_result.uncertainty > 0.6:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.CONTRADICTING,
                        f"High reasoning uncertainty: {reasoning_result.uncertainty:.2f}",
                        confidence=reasoning_result.uncertainty,
                        weight=0.5,
                        provenance="conflict_agent/uncertainty",
                    )
                )
                warnings.append("High uncertainty in reasoning")

        low_conf_premises = [
            p.text[:60] for p in (reasoning_result.premises if reasoning_result else []) if p.confidence < 0.5
        ]
        if low_conf_premises:
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.NEUTRAL,
                    f"Low-confidence premises: {len(low_conf_premises)}",
                    confidence=0.5,
                    weight=0.3,
                    provenance="conflict_agent/low_confidence",
                )
            )

        if conflict_count > 3:
            warnings.append(f"Multiple conflicts detected: {conflict_count}")

        if conflict_count == 0:
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.SUPPORTING,
                    "No conflicts detected",
                    confidence=0.9,
                    weight=0.3,
                    provenance="conflict_agent",
                )
            )
            recommendation = "duplicate"
            confidence = 0.8
        elif conflict_count <= 2:
            recommendation = "uncertain"
            confidence = 0.5
        else:
            recommendation = "not_duplicate"
            confidence = max(0.1, 1.0 - (conflict_count * 0.2))

        elapsed = (time.perf_counter() - start) * 1000
        return AgentResult(
            agent_name=self.name,
            confidence=confidence,
            recommendation=recommendation,
            supporting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.SUPPORTING],
            contradicting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.CONTRADICTING],
            warnings=warnings,
            metadata={"conflict_count": conflict_count},
            processing_time_ms=elapsed,
        )


class ConfidenceAgent(CognitiveAgent):
    @property
    def name(self) -> str:
        return "confidence_agent"

    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult:
        start = time.perf_counter()
        evidence: list[Evidence] = []
        warnings: list[str] = []
        confidence = 0.5
        recommendation = "uncertain"

        if reasoning_result is None or reasoning_result.confidence_chain is None:
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.NEUTRAL,
                    "No confidence chain available",
                    confidence=0.5,
                    weight=0.3,
                    provenance="confidence_agent",
                )
            )
            confidence = 0.5
            recommendation = "uncertain"
        else:
            chain = reasoning_result.confidence_chain
            premise_conf = chain.premise_confidence
            hypothesis_conf = chain.hypothesis_confidence
            evidence_conf = chain.evidence_confidence
            reasoning_conf = chain.reasoning_confidence
            decision_conf = chain.decision_confidence

            detail = (
                f"premise={premise_conf:.2f}, hypothesis={hypothesis_conf:.2f}, "
                f"evidence={evidence_conf:.2f}, reasoning={reasoning_conf:.2f}, decision={decision_conf:.2f}"
            )
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.SUPPORTING,
                    f"Confidence chain: {detail}",
                    confidence=decision_conf,
                    weight=0.8,
                    provenance="confidence_agent",
                )
            )

            overconfidence = hypothesis_conf > 0.7 and evidence_conf < 0.4
            underconfidence = hypothesis_conf < 0.3 and evidence_conf > 0.7

            if overconfidence:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.CONTRADICTING,
                        f"Potential overconfidence: hypothesis={hypothesis_conf:.2f} vs evidence={evidence_conf:.2f}",
                        confidence=0.7,
                        weight=0.7,
                        provenance="confidence_agent/overconfidence",
                    )
                )
                warnings.append(f"Overconfidence detected: hyp={hypothesis_conf:.2f} vs ev={evidence_conf:.2f}")
                confidence = 0.3
                recommendation = "uncertain"
            elif underconfidence:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.CONTRADICTING,
                        f"Potential underconfidence: hypothesis={hypothesis_conf:.2f} vs evidence={evidence_conf:.2f}",
                        confidence=0.6,
                        weight=0.5,
                        provenance="confidence_agent/underconfidence",
                    )
                )
                warnings.append("Underconfidence detected")
                confidence = 0.5
                recommendation = "uncertain"
            elif decision_conf > 0.7:
                recommendation = "duplicate"
                confidence = decision_conf
            elif decision_conf < 0.3:
                recommendation = "not_duplicate"
                confidence = 1.0 - decision_conf
            else:
                recommendation = "uncertain"
                confidence = decision_conf

            if reasoning_result.confidence < 0.3:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.CONTRADICTING,
                        f"Low overall confidence: {reasoning_result.confidence:.2f}",
                        confidence=0.6,
                        weight=0.4,
                        provenance="confidence_agent/low_confidence",
                    )
                )

        elapsed = (time.perf_counter() - start) * 1000
        return AgentResult(
            agent_name=self.name,
            confidence=max(0.0, min(1.0, confidence)),
            recommendation=recommendation,
            supporting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.SUPPORTING],
            contradicting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.CONTRADICTING],
            warnings=warnings,
            metadata={
                "premise_confidence": getattr(chain, "premise_confidence", None) if reasoning_result else None,
                "hypothesis_confidence": getattr(chain, "hypothesis_confidence", None) if reasoning_result else None,
                "evidence_confidence": getattr(chain, "evidence_confidence", None) if reasoning_result else None,
                "reasoning_confidence": getattr(chain, "reasoning_confidence", None) if reasoning_result else None,
                "decision_confidence": getattr(chain, "decision_confidence", None) if reasoning_result else None,
            },
            processing_time_ms=elapsed,
        )


class EvidenceAgent(CognitiveAgent):
    @property
    def name(self) -> str:
        return "evidence_agent"

    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult:
        start = time.perf_counter()
        evidence: list[Evidence] = []
        warnings: list[str] = []
        confidence = 0.5
        recommendation = "uncertain"

        if reasoning_result is None:
            evidence.append(
                _ensure_evidence(
                    evidence,
                    "",
                    EvidenceType.NEUTRAL,
                    "No reasoning result available",
                    confidence=0.5,
                    weight=0.3,
                    provenance="evidence_agent",
                )
            )
            confidence = 0.5
            recommendation = "uncertain"
        else:
            all_ev = reasoning_result.supporting_evidence + reasoning_result.contradicting_evidence
            if not all_ev:
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.NEUTRAL,
                        "No evidence in reasoning result",
                        confidence=0.5,
                        weight=0.3,
                        provenance="evidence_agent",
                    )
                )
                confidence = 0.5
                recommendation = "uncertain"
            else:
                seen_texts: set[str] = set()
                unique_ev: list[Evidence] = []
                for e in all_ev:
                    if e.text not in seen_texts:
                        seen_texts.add(e.text)
                        unique_ev.append(e)

                duplicates_removed = len(all_ev) - len(unique_ev)
                if duplicates_removed > 0:
                    evidence.append(
                        _ensure_evidence(
                            evidence,
                            "",
                            EvidenceType.NEUTRAL,
                            f"Removed {duplicates_removed} duplicate evidence entries",
                            confidence=0.8,
                            weight=0.3,
                            provenance="evidence_agent/dedup",
                        )
                    )
                    warnings.append(f"Found {duplicates_removed} duplicate evidence entries")

                supporting = [e for e in unique_ev if e.evidence_type == EvidenceType.SUPPORTING]
                contradicting = [e for e in unique_ev if e.evidence_type == EvidenceType.CONTRADICTING]

                ranked = sorted(supporting, key=lambda e: e.weight * e.confidence, reverse=True)
                low_quality = [e for e in ranked if e.weight * e.confidence < 0.3]
                if low_quality:
                    warnings.append(f"Low-quality evidence: {len(low_quality)} items below 0.3 weight*confidence")

                high_quality_count = len([e for e in ranked if e.weight * e.confidence >= 0.7])
                evidence.append(
                    _ensure_evidence(
                        evidence,
                        "",
                        EvidenceType.SUPPORTING,
                        f"Evidence quality: {high_quality_count} high-quality of {len(ranked)} supporting, "
                        f"{len(contradicting)} contradicting",
                        confidence=high_quality_count / max(1, len(ranked)),
                        weight=0.7,
                        provenance="evidence_agent",
                    )
                )

                if len(supporting) > len(contradicting) * 2:
                    recommendation = "duplicate"
                    evidence.append(
                        _ensure_evidence(
                            evidence,
                            "",
                            EvidenceType.SUPPORTING,
                            f"Supporting evidence dominates ({len(supporting)} vs {len(contradicting)})",
                            confidence=0.8,
                            weight=0.5,
                            provenance="evidence_agent",
                        )
                    )
                    confidence = len(supporting) / max(1, len(supporting) + len(contradicting))
                elif len(contradicting) > len(supporting) * 2:
                    recommendation = "not_duplicate"
                    evidence.append(
                        _ensure_evidence(
                            evidence,
                            "",
                            EvidenceType.CONTRADICTING,
                            f"Contradicting evidence dominates ({len(contradicting)} vs {len(supporting)})",
                            confidence=0.8,
                            weight=0.5,
                            provenance="evidence_agent",
                        )
                    )
                    confidence = len(contradicting) / max(1, len(supporting) + len(contradicting))
                else:
                    recommendation = "uncertain"
                    confidence = 0.5

        elapsed = (time.perf_counter() - start) * 1000
        return AgentResult(
            agent_name=self.name,
            confidence=max(0.0, min(1.0, confidence)),
            recommendation=recommendation,
            supporting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.SUPPORTING],
            contradicting_evidence=[e for e in evidence if e.evidence_type == EvidenceType.CONTRADICTING],
            warnings=warnings,
            metadata={
                "total_evidence": len(all_ev) if reasoning_result else 0,
                "duplicates_removed": duplicates_removed if reasoning_result else 0,
            },
            processing_time_ms=elapsed,
        )


class ConsensusAgent(CognitiveAgent):
    @property
    def name(self) -> str:
        return "consensus_agent"

    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult:
        start = time.perf_counter()
        evidence: list[Evidence] = []

        evidence.append(
            _ensure_evidence(
                evidence,
                "",
                EvidenceType.NEUTRAL,
                "Consensus agent: meta-agent does not evaluate directly",
                confidence=1.0,
                weight=0.0,
                provenance="consensus_agent",
            )
        )

        elapsed = (time.perf_counter() - start) * 1000
        return AgentResult(
            agent_name=self.name,
            confidence=1.0,
            recommendation="uncertain",
            supporting_evidence=[],
            contradicting_evidence=[],
            warnings=[],
            metadata={"note": "Consensus is computed by DebateEngine, not by this agent"},
            processing_time_ms=elapsed,
        )
