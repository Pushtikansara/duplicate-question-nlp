"""Linguistic Analyzer Orchestrator — fifth stage of the Cognitive Perception Pipeline.

Orchestrates entity extraction, negation detection, intent detection,
and lexical analysis through adapter-wrapped existing engines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._perception.adapters import (
    EntityAdapter,
    IntentAdapter,
    LexicalAdapter,
    LinguisticAdapterFactory,
    NegationAdapter,
)
from duplicate_question_app._perception.cognitive_representation import LinguisticFeatures
from duplicate_question_app._perception.config import LinguisticOrchestratorConfig
from duplicate_question_app._perception.exceptions import LinguisticAnalysisError

log = get_logger(__name__)


class LinguisticOrchestrator(ABC):
    @abstractmethod
    def analyze(self, text: str) -> LinguisticFeatures: ...


class DefaultLinguisticOrchestrator(LinguisticOrchestrator):
    def __init__(
        self,
        config: LinguisticOrchestratorConfig | None = None,
        entity_adapter: EntityAdapter | None = None,
        negation_adapter: NegationAdapter | None = None,
        intent_adapter: IntentAdapter | None = None,
        lexical_adapter: LexicalAdapter | None = None,
    ):
        self._config = config or LinguisticOrchestratorConfig()
        self._entity_adapter = entity_adapter or LinguisticAdapterFactory.create_entity_adapter()
        self._negation_adapter = negation_adapter or LinguisticAdapterFactory.create_negation_adapter()
        self._intent_adapter = intent_adapter or LinguisticAdapterFactory.create_intent_adapter()
        self._lexical_adapter = lexical_adapter or LinguisticAdapterFactory.create_lexical_adapter()
        self._logger = get_logger(f"{__name__}.DefaultLinguisticOrchestrator")

    def analyze(self, text: str) -> LinguisticFeatures:
        if not text or not text.strip():
            return LinguisticFeatures()
        try:
            entities: list = []
            negations: list = []
            intent: str | None = None
            intent_confidence: float = 0.0
            lexical_density: float = 0.0

            if self._config.enable_entity_extraction:
                entities = self._entity_adapter.extract(text)
                self._logger.debug("Extracted %d entities", len(entities))

            if self._config.enable_negation_detection:
                negations = self._negation_adapter.detect(text)
                self._logger.debug("Detected %d negations", len(negations))

            if self._config.enable_intent_detection:
                intent, intent_confidence = self._intent_adapter.detect(text)
                self._logger.debug("Detected intent: %s (%.2f)", intent, intent_confidence)

            if self._config.enable_lexical_analysis:
                lexical_result = self._lexical_adapter.analyze(text)
                lexical_density = lexical_result.get("lexical_density", 0.0)

            return LinguisticFeatures(
                entities=entities,
                negations=negations,
                intent=intent,
                intent_confidence=intent_confidence,
                lexical_density=lexical_density,
                subjectivity=0.0,
            )
        except Exception as exc:
            raise LinguisticAnalysisError(
                str(exc),
                context="linguistic_orchestration",
                cause="Linguistic analysis pipeline failed",
                resolution="Check text encoding and linguistic engine availability",
            ) from exc
