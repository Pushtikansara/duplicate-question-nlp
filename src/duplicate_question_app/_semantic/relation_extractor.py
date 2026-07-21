"""RelationExtractor — builds typed semantic relations between extracted concepts.

Produces lightweight semantic relations such as:
  INSTALL  ──acts_on──▶  PYTHON
  PYTHON   ──runs_on──▶  UBUNTU
  ERROR    ──occurs_in──▶  PYTHON
  QUESTION ──requests──▶  INSTALL
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile
from duplicate_question_app._semantic.semantic_graph import SemanticNode, SemanticRelation

log = get_logger(__name__)

_ACTION_KEYWORDS: set[str] = {
    "INSTALL",
    "UNINSTALL",
    "UPDATE",
    "DOWNLOAD",
    "DEBUG",
    "FIX",
    "LEARN",
    "COMPARE",
    "MIGRATE",
    "OPTIMIZE",
    "DISABLE",
    "ENABLE",
    "CONFIGURE",
    "DEPLOY",
    "BUILD",
    "COMPILE",
    "TEST",
    "RUN",
    "START",
    "STOP",
    "RECOMMEND",
    "DEFINE",
    "ERROR",
}

_RELATION_PATTERNS: list[tuple[str, str, str]] = [
    ("acts_on", "action", "entity"),
    ("acts_on", "action", "concept"),
    ("runs_on", "entity", "entity"),
    ("runs_on", "entity", "domain"),
    ("depends_on", "concept", "concept"),
    ("depends_on", "entity", "concept"),
    ("occurs_in", "action", "concept"),
    ("located_in", "entity", "domain"),
    ("related_to", "concept", "concept"),
    ("part_of", "concept", "domain"),
]


class RelationExtractor(ABC):
    @abstractmethod
    def extract(self, profile: LinguisticProfile, concepts: list[SemanticNode]) -> list[SemanticRelation]: ...


class DefaultRelationExtractor(RelationExtractor):
    def __init__(self) -> None:
        self._logger = log

    def extract(self, profile: LinguisticProfile, concepts: list[SemanticNode]) -> list[SemanticRelation]:
        relations: list[SemanticRelation] = []
        seen_pairs: set[tuple[str, str, str]] = set()
        intent = (profile.intent or "").upper()
        actions = [c for c in concepts if c.node_type == "action"]
        entities = [c for c in concepts if c.node_type == "entity"]
        domains = [c for c in concepts if c.node_type == "domain"]
        others = [c for c in concepts if c.node_type == "concept"]

        for action in actions:
            for entity in entities:
                rel = SemanticRelation(
                    source_id=action.id,
                    target_id=entity.id,
                    relation_type="acts_on",
                    confidence=min(action.confidence, entity.confidence),
                )
                key = (rel.source_id, rel.target_id, rel.relation_type)
                if key not in seen_pairs:
                    relations.append(rel)
                    seen_pairs.add(key)
            for other in others:
                rel = SemanticRelation(
                    source_id=action.id,
                    target_id=other.id,
                    relation_type="acts_on",
                    confidence=min(action.confidence, other.confidence),
                )
                key = (rel.source_id, rel.target_id, rel.relation_type)
                if key not in seen_pairs:
                    relations.append(rel)
                    seen_pairs.add(key)

        for entity in entities:
            for domain in domains:
                rel = SemanticRelation(
                    source_id=entity.id,
                    target_id=domain.id,
                    relation_type="runs_on",
                    confidence=min(entity.confidence, domain.confidence),
                )
                key = (rel.source_id, rel.target_id, rel.relation_type)
                if key not in seen_pairs:
                    relations.append(rel)
                    seen_pairs.add(key)

        for i, c1 in enumerate(concepts):
            for c2 in concepts[i + 1 :]:
                if c1.node_type == c2.node_type and c1.id != c2.id:
                    rel = SemanticRelation(
                        source_id=c1.id,
                        target_id=c2.id,
                        relation_type="related_to",
                        confidence=min(c1.confidence, c2.confidence),
                    )
                    key = (rel.source_id, rel.target_id, rel.relation_type)
                    if key not in seen_pairs:
                        relations.append(rel)
                        seen_pairs.add(key)

        if intent:
            intent_node = next((c for c in concepts if c.id == intent), None)
            if intent_node:
                for action in actions:
                    if action.id != intent_node.id:
                        rel = SemanticRelation(
                            source_id=intent_node.id,
                            target_id=action.id,
                            relation_type="requests",
                            confidence=intent_node.confidence,
                        )
                        key = (rel.source_id, rel.target_id, rel.relation_type)
                        if key not in seen_pairs:
                            relations.append(rel)
                            seen_pairs.add(key)

        self._logger.debug("Extracted %d semantic relations", len(relations))
        return relations
