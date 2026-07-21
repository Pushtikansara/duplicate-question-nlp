from __future__ import annotations

import logging
import re
from typing import Any

from duplicate_question_app._perception.cognitive_representation import Metadata as PerceptionMetadata
from duplicate_question_app._routing.interfaces import ComplexityEstimator
from duplicate_question_app._routing.routing_result import ComplexityResult

log = logging.getLogger(__name__)

_AMBIGUITY_WORDS = frozenset(
    {
        "maybe",
        "perhaps",
        "possibly",
        "roughly",
        "approximately",
        "around",
        "about",
        "sort of",
        "kind of",
        "not sure",
        "unsure",
        "unclear",
        "might",
        "could",
        "seems",
        "appears",
        "probably",
        "somewhat",
    }
)

_COMPLEX_KEYWORDS = frozenset(
    {
        "compare",
        "contrast",
        "difference",
        "relationship",
        "impact",
        "effect",
        "analysis",
        "evaluate",
        "explain",
        "why",
        "how does",
        "mechanism",
        "architecture",
        "design pattern",
        "underlying",
        "implication",
    }
)

_MEDIUM_KEYWORDS = frozenset(
    {
        "install",
        "setup",
        "configure",
        "how to",
        "tutorial",
        "example",
        "vs",
        "versus",
        "difference between",
        "best",
        "recommend",
        "alternative",
        "migration",
        "compatibility",
        "support",
    }
)

_DOMAIN_SIMPLE_WORDS = frozenset(
    {
        "hello",
        "hi",
        "thanks",
        "thank you",
        "yes",
        "no",
        "goodbye",
    }
)


class DefaultComplexityEstimator(ComplexityEstimator):
    def estimate(
        self,
        question_a: str,
        question_b: str,
        metadata: PerceptionMetadata | None = None,
    ) -> ComplexityResult:
        features: dict[str, Any] = {}
        explanation_parts: list[str] = []

        if question_a is None:
            question_a = ""
        if question_b is None:
            question_b = ""

        len_a = len(question_a)
        len_b = len(question_b)

        words_a = question_a.split()
        words_b = question_b.split()

        word_count_a = len(words_a)
        word_count_b = len(words_b)
        avg_word_count = (word_count_a + word_count_b) / 2.0
        avg_char_len = (len_a + len_b) / 2.0

        features["avg_word_count"] = avg_word_count
        features["avg_char_len"] = avg_char_len
        features["word_count_a"] = word_count_a
        features["word_count_b"] = word_count_b

        combined_text_lower = (question_a + " " + question_b).lower()

        entity_count = 0
        if metadata is not None:
            entity_count = len(metadata.extra.get("entities", []))
            features["entity_count"] = entity_count
            features["question_type_a"] = metadata.question_type
        else:
            features["entity_count"] = 0
            features["question_type_a"] = None

        ambiguity_count = sum(1 for word in _AMBIGUITY_WORDS if word in combined_text_lower)
        features["ambiguity_count"] = ambiguity_count

        complex_kw_count = sum(1 for kw in _COMPLEX_KEYWORDS if kw in combined_text_lower)
        features["complex_keyword_count"] = complex_kw_count

        medium_kw_count = sum(1 for kw in _MEDIUM_KEYWORDS if kw in combined_text_lower)
        features["medium_keyword_count"] = medium_kw_count

        simple_word_count = sum(1 for w in _DOMAIN_SIMPLE_WORDS if w in combined_text_lower.split())
        features["simple_word_count"] = simple_word_count

        has_multi_sentence = (len(re.findall(r"[.!?]+", question_a)) + len(re.findall(r"[.!?]+", question_b))) > 2
        features["has_multi_sentence"] = has_multi_sentence

        has_code = bool(re.search(r"(```|`[^`]+`|def |class |import |function )", combined_text_lower))
        features["has_code"] = has_code

        has_url = bool(re.search(r"https?://\S+|www\.\S+", combined_text_lower))
        features["has_url"] = has_url

        short_text = avg_word_count <= 5 and avg_char_len < 80
        greeting_text = simple_word_count > 0 and avg_word_count <= 4
        very_long = avg_word_count > 30 or avg_char_len > 500
        medium_length = 5 < avg_word_count <= 20

        score = 0.0
        complexity = "simple"

        if question_a is None or question_b is None:
            complexity = "uncertain"
            score = 1.0
            explanation_parts.append("One or both questions are None")
        elif not question_a.strip() or not question_b.strip():
            complexity = "uncertain"
            score = 1.0
            explanation_parts.append("One or both questions are empty")
        elif greeting_text:
            complexity = "simple"
            score = 0.1
            explanation_parts.append("Greeting or very short text detected")
        elif very_long or entity_count > 5 or has_multi_sentence:
            complexity = "complex"
            score = 0.8
            explanation_parts.append("Long question with multiple entities or sentences")
        elif ambiguity_count > 1:
            complexity = "uncertain"
            score = 0.9
            explanation_parts.append("Multiple ambiguity markers detected")
        elif ambiguity_count > 0 and complex_kw_count > 0:
            complexity = "complex"
            score = 0.85
            explanation_parts.append("Ambiguous language with complex keywords")
        elif ambiguity_count > 0:
            complexity = "uncertain"
            score = 0.7
            explanation_parts.append("Ambiguity markers present without other signals")
        elif short_text and complex_kw_count == 0 and medium_kw_count == 0:
            complexity = "simple"
            score = 0.2
            explanation_parts.append("Short factual or definition question")
        elif medium_length and medium_kw_count > 0:
            complexity = "medium"
            score = 0.5
            explanation_parts.append("Medium-length question with configuration or comparison keywords")
        elif medium_length and complex_kw_count > 0:
            complexity = "medium"
            score = 0.6
            explanation_parts.append("Medium-length question with analytical keywords")
        elif entity_count > 3 or complex_kw_count > 2:
            complexity = "complex"
            score = 0.75
            explanation_parts.append("Multiple entities or analytical keywords")
        elif medium_kw_count > 0:
            complexity = "medium"
            score = 0.45
            explanation_parts.append("Configuration or comparison keywords found")
        else:
            complexity = "simple"
            score = 0.3
            explanation_parts.append("Default classification for general questions")

        if has_code:
            score = min(1.0, score + 0.1)
            if complexity == "simple":
                complexity = "medium"
            explanation_parts.append("Code snippets detected")

        if has_url:
            score = min(1.0, score + 0.05)

        if entity_count > 5:
            complexity = "complex"
            explanation_parts.append("High entity count")

        score = max(0.0, min(1.0, score))
        features["ambiguity_count"] = ambiguity_count
        features["entity_count"] = entity_count

        return ComplexityResult(
            complexity=complexity,
            score=score,
            features=features,
            explanation="; ".join(explanation_parts),
        )
