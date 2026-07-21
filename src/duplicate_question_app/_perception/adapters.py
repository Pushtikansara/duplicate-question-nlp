"""Adapters wrapping existing linguistic engines for use by the Linguistic Orchestrator.

Reuses entity, negation, contradiction, lexical, and intent detectors
from `_linguistics` instead of duplicating functionality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistics.entity import detect_entities as _detect_entities
from duplicate_question_app._linguistics.intent import detect_intent as _detect_intent
from duplicate_question_app._linguistics.lexical import extract_tokens as _extract_tokens
from duplicate_question_app._linguistics.negation import detect_negations as _detect_negations
from duplicate_question_app._perception.cognitive_representation import Entity, Negation

log = get_logger(__name__)


class EntityAdapter(ABC):
    @abstractmethod
    def extract(self, text: str) -> list[Entity]: ...


class DefaultEntityAdapter(EntityAdapter):
    def extract(self, text: str) -> list[Entity]:
        raw_entities = _detect_entities(text)
        return [
            Entity(
                entity_type=e.entity_type,
                value=e.value,
                start=e.start,
                end=e.end,
                confidence=e.confidence,
            )
            for e in raw_entities
        ]


class NegationAdapter(ABC):
    @abstractmethod
    def detect(self, text: str) -> list[Negation]: ...


class DefaultNegationAdapter(NegationAdapter):
    def detect(self, text: str) -> list[Negation]:
        raw_negations = _detect_negations(text)
        return [
            Negation(
                text=n.text,
                start=n.start,
                end=n.end,
                negation_type=n.negation_type,
                scope=n.scope.value if hasattr(n.scope, "value") else str(n.scope),
                confidence=n.confidence,
                target=n.target,
            )
            for n in raw_negations
        ]


class IntentAdapter(ABC):
    @abstractmethod
    def detect(self, text: str) -> tuple[str | None, float]: ...


class DefaultIntentAdapter(IntentAdapter):
    def detect(self, text: str) -> tuple[str | None, float]:
        result = _detect_intent(text)
        if result.primary_intent.value == "unknown":
            return None, 0.0
        return result.primary_intent.value, result.confidence


class LexicalAdapter(ABC):
    @abstractmethod
    def analyze(self, text: str) -> dict: ...


class DefaultLexicalAdapter(LexicalAdapter):
    def analyze(self, text: str) -> dict:
        analysis = _extract_tokens(text)
        total = len(analysis.all_tokens)
        unique_content = len(analysis.nouns | analysis.verbs | analysis.entities)
        density = unique_content / total if total > 0 else 0.0
        return {
            "nouns": list(analysis.nouns),
            "verbs": list(analysis.verbs),
            "entities": list(analysis.entities),
            "lexical_density": density,
        }


class LinguisticAdapterFactory:
    @staticmethod
    def create_entity_adapter() -> EntityAdapter:
        return DefaultEntityAdapter()

    @staticmethod
    def create_negation_adapter() -> NegationAdapter:
        return DefaultNegationAdapter()

    @staticmethod
    def create_intent_adapter() -> IntentAdapter:
        return DefaultIntentAdapter()

    @staticmethod
    def create_lexical_adapter() -> LexicalAdapter:
        return DefaultLexicalAdapter()
