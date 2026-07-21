"""SemanticRoleAnalyzer — assigns lightweight semantic roles to extracted concepts.

Roles: ACTION, ACTOR, TARGET, LOCATION, TOOL, OBJECT, GOAL, TIME
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile
from duplicate_question_app._semantic.representation import SemanticRoleAssignment
from duplicate_question_app._semantic.semantic_graph import SemanticNode

log = get_logger(__name__)


class SemanticRoleAnalyzer(ABC):
    @abstractmethod
    def analyze(self, profile: LinguisticProfile, concepts: list[SemanticNode]) -> dict[str, list[SemanticNode]]: ...


class DefaultSemanticRoleAnalyzer(SemanticRoleAnalyzer):
    def __init__(self) -> None:
        self._logger = log

    def analyze(self, profile: LinguisticProfile, concepts: list[SemanticNode]) -> dict[str, list[SemanticNode]]:
        roles: dict[str, list[SemanticNode]] = {
            "ACTION": [],
            "ACTOR": [],
            "TARGET": [],
            "LOCATION": [],
            "TOOL": [],
            "OBJECT": [],
            "GOAL": [],
            "TIME": [],
        }
        actions = [c for c in concepts if c.node_type == "action"]
        roles["ACTION"] = actions
        entities = [c for c in concepts if c.node_type == "entity"]
        if entities:
            roles["TARGET"] = entities[:1]
            if len(entities) > 1:
                roles["TOOL"] = entities[1:]
        domains = [c for c in concepts if c.node_type == "domain"]
        if domains:
            roles["LOCATION"] = domains
        others = [c for c in concepts if c.node_type == "concept" and c not in actions and c not in entities]
        if others:
            roles["OBJECT"] = others
        if profile.intent and actions:
            roles["GOAL"] = actions[:1]
        self._logger.debug("Assigned semantic roles: %s", {k: len(v) for k, v in roles.items()})
        return roles

    @staticmethod
    def to_assignments(roles: dict[str, list[SemanticNode]]) -> list[SemanticRoleAssignment]:
        return [
            SemanticRoleAssignment(
                role=role, concept_ids=[n.id for n in nodes], confidence=min((n.confidence for n in nodes), default=1.0)
            )
            for role, nodes in roles.items()
            if nodes
        ]
