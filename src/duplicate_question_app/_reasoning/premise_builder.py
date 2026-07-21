from __future__ import annotations

import uuid

from duplicate_question_app._reasoning.interfaces import PremiseBuilder
from duplicate_question_app._reasoning.reasoning_result import Premise
from duplicate_question_app._semantic.representation import SemanticRepresentation


def _make_id() -> str:
    return uuid.uuid4().hex[:12]


class DefaultPremiseBuilder(PremiseBuilder):
    def extract(self, rep: SemanticRepresentation, source_label: str) -> list[Premise]:
        premises: list[Premise] = []

        for c in rep.concepts:
            premises.append(
                Premise(
                    id=_make_id(),
                    text=f"Concept '{c.label}' (normalized: {c.normalized_form}) is present",
                    source=source_label,
                    category="concept",
                    confidence=c.confidence,
                    provenance=f"SemanticRepresentation.concepts[{c.id}]",
                )
            )

        for e in rep.entities:
            ent_id = e.get("entity_id", e.get("id", str(e.get("text", ""))))
            ent_text = e.get("text", e.get("value", str(e)))
            ent_conf = float(e.get("confidence", 0.8))
            premises.append(
                Premise(
                    id=_make_id(),
                    text=f"Entity '{ent_text}' of type '{e.get('type', 'unknown')}' is present",
                    source=source_label,
                    category="entity",
                    confidence=ent_conf,
                    provenance=f"SemanticRepresentation.entities[{ent_id}]",
                )
            )

        for action in rep.actions:
            premises.append(
                Premise(
                    id=_make_id(),
                    text=f"Action '{action}' is described",
                    source=source_label,
                    category="action",
                    confidence=0.9,
                    provenance="SemanticRepresentation.actions",
                )
            )

        for obj in rep.objects:
            premises.append(
                Premise(
                    id=_make_id(),
                    text=f"Object '{obj}' is referenced",
                    source=source_label,
                    category="object",
                    confidence=0.9,
                    provenance="SemanticRepresentation.objects",
                )
            )

        for attr in rep.attributes:
            premises.append(
                Premise(
                    id=_make_id(),
                    text=f"Attribute '{attr}' is specified",
                    source=source_label,
                    category="attribute",
                    confidence=0.9,
                    provenance="SemanticRepresentation.attributes",
                )
            )

        for rel in rep.relationships:
            premises.append(
                Premise(
                    id=_make_id(),
                    text=f"Relation '{rel.relation_type}' from '{rel.source_id}' to '{rel.target_id}'",
                    source=source_label,
                    category="relation",
                    confidence=rel.confidence,
                    provenance=f"SemanticRepresentation.relationships[{rel.source_id}->{rel.target_id}]",
                )
            )

        if rep.intent_summary:
            premises.append(
                Premise(
                    id=_make_id(),
                    text=f"Intent: {rep.intent_summary}",
                    source=source_label,
                    category="intent",
                    confidence=0.9,
                    provenance="SemanticRepresentation.intent_summary",
                )
            )

        if rep.domain:
            premises.append(
                Premise(
                    id=_make_id(),
                    text=f"Domain: {rep.domain}",
                    source=source_label,
                    category="domain",
                    confidence=0.9,
                    provenance="SemanticRepresentation.domain",
                )
            )

        for amb in rep.ambiguities:
            premises.append(
                Premise(
                    id=_make_id(),
                    text=f"Ambiguity ({amb.type}): {amb.description}",
                    source=source_label,
                    category="ambiguity",
                    confidence=amb.confidence,
                    provenance=f"SemanticRepresentation.ambiguities[{amb.type}]",
                )
            )

        for constraint in rep.constraints:
            premises.append(
                Premise(
                    id=_make_id(),
                    text=f"Constraint: {constraint}",
                    source=source_label,
                    category="constraint",
                    confidence=0.9,
                    provenance="SemanticRepresentation.constraints",
                )
            )

        return premises
