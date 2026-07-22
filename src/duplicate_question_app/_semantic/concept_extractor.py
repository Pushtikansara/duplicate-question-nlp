from __future__ import annotations

import re
from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile
from duplicate_question_app._semantic.semantic_graph import SemanticNode

log = get_logger(__name__)

_NORMALIZATION_RULES: list[tuple[re.Pattern, str | None]] = [
    (re.compile(r"(install|installation|installing|setup|configure|configuring)", re.IGNORECASE), "INSTALL"),
    (re.compile(r"(uninstall|remove|deinstall|deletion|deleting)", re.IGNORECASE), "UNINSTALL"),
    (re.compile(r"(upgrade|update|updating|upgrading)", re.IGNORECASE), "UPDATE"),
    (re.compile(r"(download|downloading|fetch|fetching)", re.IGNORECASE), "DOWNLOAD"),
    (re.compile(r"(error|errors|bug|bugs|crash|exception|fail|failure|failing)", re.IGNORECASE), "ERROR"),
    (re.compile(r"(fix|fixing|repair|repairing|solve|solving|resolve|resolving)", re.IGNORECASE), "FIX"),
    (re.compile(r"(debug|debugging|troubleshoot|troubleshooting)", re.IGNORECASE), "DEBUG"),
    (re.compile(r"(learn|learning|study|studying|understand|understanding)", re.IGNORECASE), "LEARN"),
    (re.compile(r"(compare|comparison|comparing|vs|versus)", re.IGNORECASE), "COMPARE"),
    (re.compile(r"(difference|differ|different)", re.IGNORECASE), "DIFFERENCE"),
    (re.compile(r"(definition|define|meaning|explain|explanation)", re.IGNORECASE), "DEFINE"),
    (re.compile(r"(recommend|recommendation|best|suggest|suggestion)", re.IGNORECASE), "RECOMMEND"),
    (re.compile(r"(migrate|migration|migrating|port|porting)", re.IGNORECASE), "MIGRATE"),
    (re.compile(r"(optimize|optimization|optimizing|performance)", re.IGNORECASE), "OPTIMIZE"),
    (re.compile(r"(question|ask|query)", re.IGNORECASE), "QUESTION"),
    (re.compile(r"(disable|disabling|turn off|switch off)", re.IGNORECASE), "DISABLE"),
    (re.compile(r"(enable|enabling|turn on|switch on)", re.IGNORECASE), "ENABLE"),
    (re.compile(r"(create|creating|make|making|build|building)", re.IGNORECASE), "CREATE"),
    (re.compile(r"(delete|deleting|remove|removing|erase|erasing)", re.IGNORECASE), "DELETE"),
    (re.compile(r"(find|finding|search|searching|locate|locating)", re.IGNORECASE), "FIND"),
    (re.compile(r"(how|what|why|when|where|which|who)", re.IGNORECASE), None),
]

_STOP_CONCEPTS: set[str] = {
    "UNKNOWN",
    "QUESTION",
    "HOW",
    "WHAT",
    "WHY",
    "WHEN",
    "WHERE",
    "WHICH",
    "WHO",
    "DO",
    "DOES",
    "DID",
    "IS",
    "ARE",
    "WAS",
    "WERE",
    "CAN",
    "COULD",
    "WOULD",
    "SHOULD",
    "MAY",
    "MIGHT",
    "HAVE",
    "HAS",
    "HAD",
    "BE",
    "BEEN",
    "BEING",
    "THE",
    "A",
    "AN",
    "THIS",
    "THAT",
    "THESE",
    "THOSE",
    "IT",
    "ITS",
    "THEY",
    "THEM",
    "THEIR",
    "WE",
    "US",
    "OUR",
    "YOU",
    "YOUR",
    "HE",
    "HIM",
    "HIS",
    "SHE",
    "HER",
    "HERS",
    "THERE",
    "HERE",
}

_ACTION_INDICATORS: set[str] = {
    "install",
    "uninstall",
    "update",
    "download",
    "debug",
    "fix",
    "learn",
    "compare",
    "migrate",
    "optimize",
    "disable",
    "enable",
    "configure",
    "deploy",
    "build",
    "compile",
    "test",
    "run",
    "start",
    "stop",
    "create",
    "delete",
    "remove",
    "find",
    "search",
}


class ConceptExtractor(ABC):
    @abstractmethod
    def extract(self, profile: LinguisticProfile) -> list[SemanticNode]: ...


class DefaultConceptExtractor(ConceptExtractor):
    def __init__(self) -> None:
        self._logger = log

    def extract(self, profile: LinguisticProfile) -> list[SemanticNode]:
        seen_ids: set[str] = set()
        concepts: list[SemanticNode] = []

        if profile.intent and profile.intent not in ("unknown",):
            concept = self._make_node(profile.intent.upper(), profile.intent, "action", profile.intent_confidence)
            if concept.id not in seen_ids:
                concepts.append(concept)
                seen_ids.add(concept.id)

        for kw in profile.keywords:
            normalized = self._normalize(kw.word)
            if normalized is None or normalized in _STOP_CONCEPTS:
                continue
            node_type = "entity" if kw.is_entity else ("action" if kw.word.lower() in _ACTION_INDICATORS else "concept")
            if normalized not in seen_ids:
                concept = self._make_node(normalized, kw.word, node_type, kw.score)
                concepts.append(concept)
                seen_ids.add(normalized)

        for ent in profile.entities:
            normalized = self._normalize(ent.get("value", ""))
            if normalized is None or normalized in _STOP_CONCEPTS:
                continue
            if normalized not in seen_ids:
                concept = self._make_node(normalized, ent.get("value", ""), "entity", ent.get("confidence", 0.8))
                concepts.append(concept)
                seen_ids.add(normalized)

        if profile.domain and profile.domain != "general":
            domain_id = profile.domain.upper().replace("-", "_")
            if domain_id not in seen_ids and domain_id not in _STOP_CONCEPTS:
                concept = self._make_node(domain_id, profile.domain, "domain", profile.domain_confidence)
                concepts.append(concept)
                seen_ids.add(domain_id)

        self._logger.debug("Extracted %d unique concepts from profile", len(concepts))
        return concepts

    @staticmethod
    def _normalize(word: str) -> str | None:
        word = word.strip()
        if not word:
            return None
        for pattern, replacement in _NORMALIZATION_RULES:
            if pattern.fullmatch(word):
                return replacement
        normalized = re.sub(r"[^a-zA-Z0-9]", "_", word).upper()
        return normalized if normalized else None

    @staticmethod
    def _make_node(node_id: str, label: str, node_type: str, confidence: float) -> SemanticNode:
        return SemanticNode(id=node_id, label=label, node_type=node_type, confidence=confidence)
