"""AmbiguityDetector — detects simple semantic ambiguity without LLM reasoning.

Detects:
  - Multiple intents
  - Conflicting entities
  - Low confidence in any analysis
  - Unknown domain
  - Negation/contradiction presence
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile
from duplicate_question_app._semantic.representation import AmbiguityEntry, SemanticRepresentation

log = get_logger(__name__)

_LOW_CONFIDENCE_THRESHOLD = 0.4


class AmbiguityDetector(ABC):
    @abstractmethod
    def detect(self, profile: LinguisticProfile, representation: SemanticRepresentation) -> list[AmbiguityEntry]: ...


class DefaultAmbiguityDetector(AmbiguityDetector):
    def __init__(self) -> None:
        self._logger = log

    def detect(self, profile: LinguisticProfile, representation: SemanticRepresentation) -> list[AmbiguityEntry]:
        ambiguities: list[AmbiguityEntry] = []

        if profile.analysis_confidence.overall < _LOW_CONFIDENCE_THRESHOLD:
            ambiguities.append(
                AmbiguityEntry(
                    type="low_confidence",
                    description="Overall analysis confidence is below threshold",
                    confidence=profile.analysis_confidence.overall,
                    evidence=[f"overall_confidence={profile.analysis_confidence.overall:.2f}"],
                )
            )

        if profile.negation:
            ambiguities.append(
                AmbiguityEntry(
                    type="negation_present",
                    description="Negation detected — meaning may be inverted",
                    confidence=0.7,
                    evidence=[f"negation_count={profile.negation_count}"],
                )
            )

        if profile.contradiction:
            ambiguities.append(
                AmbiguityEntry(
                    type="contradiction_present",
                    description="Contradiction detected between concepts",
                    confidence=profile.contradiction_score,
                    evidence=[f"contradiction_score={profile.contradiction_score:.2f}"],
                )
            )

        if not profile.domain or profile.domain == "general":
            ambiguities.append(
                AmbiguityEntry(
                    type="unknown_domain",
                    description="Domain could not be determined",
                    confidence=0.5,
                    evidence=["domain=general"],
                )
            )

        if profile.entity_count == 0 and len(profile.keywords) > 0:
            ambiguities.append(
                AmbiguityEntry(
                    type="no_entities",
                    description="No named entities detected despite keywords",
                    confidence=0.4,
                    evidence=[f"keywords={len(profile.keywords)}"],
                )
            )

        if not profile.intent or profile.intent == "unknown":
            ambiguities.append(
                AmbiguityEntry(
                    type="unknown_intent",
                    description="Question intent could not be determined",
                    confidence=0.5,
                    evidence=["intent=unknown"],
                )
            )

        self._logger.debug("Detected %d ambiguities", len(ambiguities))
        return ambiguities
