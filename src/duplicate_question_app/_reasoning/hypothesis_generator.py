from __future__ import annotations

import uuid

from duplicate_question_app._reasoning.interfaces import HypothesisGenerator
from duplicate_question_app._reasoning.reasoning_result import Hypothesis, HypothesisLabel, Premise
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


def _make_id() -> str:
    return uuid.uuid4().hex[:12]


class DefaultHypothesisGenerator(HypothesisGenerator):
    def generate(
        self,
        premises_a: list[Premise],
        premises_b: list[Premise],
        assessment: SemanticAssessment | None = None,
    ) -> list[Hypothesis]:
        hypotheses: list[Hypothesis] = []
        overlap_ratio = 0.0
        sem_sim = 0.5

        if assessment is not None:
            overlap_ratio = assessment.concept_overlap.overlap_score
            sem_sim = assessment.semantic_similarity

        concepts_a = {p.text for p in premises_a if p.category == "concept"}
        concepts_b = {p.text for p in premises_b if p.category == "concept"}
        shared_texts = concepts_a & concepts_b
        only_a = concepts_a - concepts_b
        only_b = concepts_b - concepts_a

        entities_a = {p.text for p in premises_a if p.category == "entity"}
        entities_b = {p.text for p in premises_b if p.category == "entity"}
        shared_entities = entities_a & entities_b
        entity_mismatch = bool(entities_a ^ entities_b)

        intents_a = [p for p in premises_a if p.category == "intent"]
        intents_b = [p for p in premises_b if p.category == "intent"]
        domains_a = [p for p in premises_a if p.category == "domain"]
        domains_b = [p for p in premises_b if p.category == "domain"]

        intent_match = False
        if intents_a and intents_b:
            intent_match = intents_a[0].text == intents_b[0].text

        domain_match = False
        if domains_a and domains_b:
            domain_match = domains_a[0].text == domains_b[0].text

        high_sem = sem_sim >= 0.7
        low_sem = sem_sim < 0.4

        high_overlap = overlap_ratio >= 0.5
        low_overlap = overlap_ratio < 0.2

        dup_premises = []
        nondup_premises = []

        if high_sem:
            dup_premises.append("high_semantic_similarity")
        if high_overlap:
            dup_premises.append("high_concept_overlap")
        if intent_match:
            dup_premises.append("intent_match")
        if domain_match:
            dup_premises.append("domain_match")
        if shared_entities and not entity_mismatch:
            dup_premises.append("entity_alignment")

        if low_sem:
            nondup_premises.append("low_semantic_similarity")
        if low_overlap:
            nondup_premises.append("low_concept_overlap")
        if intent_match is False and intents_a and intents_b:
            nondup_premises.append("intent_mismatch")
        if entity_mismatch:
            nondup_premises.append("entity_mismatch")
        if only_a or only_b:
            if high_overlap:
                dup_premises.append("partial_concept_containment")
            else:
                nondup_premises.append("concept_asymmetry")

        hyp_conf_dup = sem_sim * 0.5 + overlap_ratio * 0.3 + (0.2 if intent_match else 0)
        hyp_conf_non = (1 - sem_sim) * 0.5 + (1 - overlap_ratio) * 0.3 + (0.2 if intent_match is False else 0)

        dup_hypothesis = Hypothesis(
            id=_make_id(),
            label=HypothesisLabel.DUPLICATE,
            text="The two questions are semantically duplicate",
            confidence=hyp_conf_dup,
            supporting_premises=dup_premises,
            contradicting_premises=nondup_premises,
            derivation=f"Generated from semantic_similarity={sem_sim:.3f}, concept_overlap={overlap_ratio:.3f}, "
            f"intent_match={intent_match}, domain_match={domain_match}, "
            f"shared_concepts={len(shared_texts)}, shared_entities={len(shared_entities)}",
        )

        nondup_hypothesis = Hypothesis(
            id=_make_id(),
            label=HypothesisLabel.NOT_DUPLICATE,
            text="The two questions are not semantically duplicate",
            confidence=hyp_conf_non,
            supporting_premises=nondup_premises,
            contradicting_premises=dup_premises,
            derivation=f"Generated from semantic_similarity={sem_sim:.3f}, concept_overlap={overlap_ratio:.3f}, "
            f"intent_mismatch={not intent_match}, entity_mismatch={entity_mismatch}",
        )

        uncertain_hypothesis = Hypothesis(
            id=_make_id(),
            label=HypothesisLabel.UNCERTAIN,
            text="The relationship between the two questions cannot be determined with confidence",
            confidence=0.5,
            supporting_premises=dup_premises + nondup_premises,
            contradicting_premises=[],
            derivation=f"Conflicting signals: dup_confidence={hyp_conf_dup:.3f}, nondup_confidence={hyp_conf_non:.3f}. "
            f"Difference={abs(hyp_conf_dup - hyp_conf_non):.3f}. "
            f"Proposed when difference is below 0.2.",
        )

        hypotheses.append(dup_hypothesis)
        hypotheses.append(nondup_hypothesis)
        if abs(hyp_conf_dup - hyp_conf_non) < 0.2:
            hypotheses.append(uncertain_hypothesis)

        return hypotheses
