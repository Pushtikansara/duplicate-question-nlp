from __future__ import annotations

import pytest


class TestLinguisticsContradiction:
    def test_contradiction_detector_imports(self):
        from duplicate_question_app._linguistics.contradiction import ContradictionResult, get_contradiction_penalty
        assert callable(get_contradiction_penalty)

    def test_get_contradiction_penalty_returns_tuple(self):
        from duplicate_question_app._linguistics.contradiction import get_contradiction_penalty
        penalty, reason = get_contradiction_penalty("How to code Python?", "How to code Python?")
        assert isinstance(penalty, (int, float))

    def test_contradiction_result_dataclass(self):
        from duplicate_question_app._linguistics.contradiction import ContradictionResult, ContradictionType
        result = ContradictionResult(
            has_contradiction=True, contradiction_score=0.8,
            contradiction_types=[ContradictionType.DIRECT_NEGATION],
            details="Negation detected: like vs hate",
        )
        assert result.has_contradiction is True
        assert result.contradiction_score == 0.8

    def test_detect_contradiction_imports(self):
        from duplicate_question_app._linguistics.contradiction import detect_contradiction
        assert callable(detect_contradiction)


class TestLinguisticsEntity:
    def test_entity_detector_imports(self):
        from duplicate_question_app._linguistics.entity import get_entity_penalty
        assert callable(get_entity_penalty)

    def test_get_entity_penalty_returns_tuple(self):
        from duplicate_question_app._linguistics.entity import get_entity_penalty
        result = get_entity_penalty("How to use Python?", "How to use Python?")
        assert isinstance(result, tuple)
        assert isinstance(result[0], (int, float))

    def test_extract_entities_imports(self):
        from duplicate_question_app._linguistics.entity import detect_entities
        assert callable(detect_entities)


class TestLinguisticsIntent:
    def test_intent_detector_imports(self):
        from duplicate_question_app._linguistics.intent import get_intent_details, intent_mismatch_penalty
        assert callable(intent_mismatch_penalty)

    def test_intent_mismatch_penalty_returns_tuple(self):
        from duplicate_question_app._linguistics.intent import intent_mismatch_penalty
        result = intent_mismatch_penalty("How to learn Python?", "How to learn Python?")
        assert isinstance(result, tuple)
        assert isinstance(result[0], (int, float))

    def test_get_intent_details_returns_dict(self):
        from duplicate_question_app._linguistics.intent import get_intent_details
        details = get_intent_details("How to learn Python?", "How to learn Python?")
        assert isinstance(details, dict)


class TestLinguisticsLexical:
    def test_lexical_penalty_imports(self):
        from duplicate_question_app._linguistics.lexical import compute_lexical_penalty, get_lexical_penalty
        assert callable(compute_lexical_penalty)

    def test_compute_lexical_penalty_returns_object(self):
        from duplicate_question_app._linguistics.lexical import compute_lexical_penalty
        result = compute_lexical_penalty("same text", "same text")
        assert result is not None

    def test_get_lexical_penalty_returns_tuple(self):
        from duplicate_question_app._linguistics.lexical import get_lexical_penalty
        result = get_lexical_penalty("How to code?", "How to write code?")
        assert isinstance(result, tuple)


class TestLinguisticsNegation:
    def test_negation_detector_imports(self):
        from duplicate_question_app._linguistics.negation import get_negation_penalty, negation_mismatch
        assert callable(get_negation_penalty)

    def test_negation_mismatch_returns_object(self):
        from duplicate_question_app._linguistics.negation import negation_mismatch
        result = negation_mismatch("How to code?", "How to write code?")
        assert result is not None

    def test_get_negation_penalty_returns_tuple(self):
        from duplicate_question_app._linguistics.negation import get_negation_penalty
        result = get_negation_penalty("I can code", "I cannot code")
        assert isinstance(result, tuple)
        assert isinstance(result[0], (int, float))

    def test_detect_negation_imports(self):
        from duplicate_question_app._linguistics.negation import detect_negations
        assert callable(detect_negations)
