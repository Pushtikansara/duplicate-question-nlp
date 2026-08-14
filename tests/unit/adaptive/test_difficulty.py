from __future__ import annotations

import pytest

from ares.adaptive.difficulty import DifficultyAnalyzer


def analyzer(cfg=None) -> DifficultyAnalyzer:
    return DifficultyAnalyzer(cfg)


class TestDeterminism:
    def test_same_input_same_output(self):
        a = analyzer()
        q1, q2 = "How to learn Python?", "How can I learn Python programming?"
        r1 = a.analyze(q1, q2)
        r2 = a.analyze(q1, q2)
        d1 = {k: v for k, v in r1.to_dict().items() if k != "processing_time_ms"}
        d2 = {k: v for k, v in r2.to_dict().items() if k != "processing_time_ms"}
        assert d1 == d2


class TestLevelClassification:
    @pytest.mark.parametrize(
        ("q1", "q2", "expected"),
        [
            ("What is the capital of France?", "What is the largest city in Germany?", "easy"),
            ("How to learn Python?", "How can I learn Python programming?", "easy"),
            ("How to increase sales?", "How to decrease sales?", "medium"),
            ("I do not want to eat meat", "I want to eat meat", "medium"),
            ("What is the price of the iPhone?", "What is the cost of the iPhone?", "medium"),
            ("What is machine learning?", "What is ML?", "medium"),
        ],
    )
    def test_level(self, q1, q2, expected):
        r = analyzer().analyze(q1, q2)
        assert r.difficulty_level == expected

    def test_exact_match_is_easy(self):
        r = analyzer().analyze("How to fold a fitted sheet?", "How to fold a fitted sheet?")
        assert r.signals["exact_match"] == 1.0
        assert r.difficulty_level == "easy"

    def test_thresholds_are_configurable(self):
        cfg = {"difficulty": {"thresholds": {"easy_max": 0.80, "medium_max": 0.90, "hard_max": 0.99}}}
        r = analyzer(cfg).analyze("How to increase sales?", "How to decrease sales?")
        assert r.difficulty_level == "easy"


class TestHardSignals:
    def test_contradiction_pair_flagged(self):
        r = analyzer().analyze("How to increase sales?", "How to decrease sales?")
        assert r.signals["contradiction"] >= 0.5
        assert r.difficulty_level in ("medium", "hard")

    def test_negation_asymmetry_flagged(self):
        r = analyzer().analyze("I do not want to eat meat", "I want to eat meat")
        assert r.signals["negation"] >= 0.5
        assert r.difficulty_level in ("medium", "hard")

    def test_abbreviation_flagged(self):
        r = analyzer().analyze("What is machine learning?", "What is ML?")
        assert r.signals["abbreviation"] >= 0.5
        assert r.difficulty_level in ("medium", "hard")

    def test_synonym_gap_flags_content_overlap(self):
        r = analyzer().analyze("What is the price of the iPhone?", "What is the cost of the iPhone?")
        assert r.signals["lexical_overlap"] > 0.4
        assert r.signals["content_overlap"] <= 0.35
        assert r.difficulty_level in ("medium", "hard")


class TestAbbreviationRelation:
    def test_lowercase_acronym_detected(self):
        r = analyzer().analyze("what is machine learning", "what is ml")
        assert r.signals["abbreviation"] >= 0.5
        assert r.signals["abbreviation_relation"] == 1.0
        assert r.difficulty_level in ("medium", "hard")

    def test_dotted_acronym_form_detected(self):
        r = analyzer().analyze("what is M.L.", "what is machine learning")
        assert r.signals["abbreviation"] >= 0.5
        assert r.signals["abbreviation_relation"] == 1.0

    def test_unrelated_abbreviation_has_no_relation(self):
        r = analyzer().analyze("what is the cpu speed", "what is the screen size")
        assert r.signals["abbreviation_relation"] == 0.0

    def test_relation_appears_in_signal_details(self):
        r = analyzer().analyze("what is machine learning", "what is ml")
        assert r.signal_details.get("abbreviation_relation")


class TestRecommendations:
    def test_recommended_budget_tracks_level(self):
        r = analyzer().analyze("How to increase sales?", "How to decrease sales?")
        assert r.recommended_budget in ("low", "medium", "high", "extra_high")

    def test_processing_time_recorded(self):
        r = analyzer().analyze("a", "b")
        assert r.processing_time_ms >= 0.0

    def test_signals_include_all_keys(self):
        r = analyzer().analyze("What now?", "Where later?")
        for key in (
            "lexical_overlap",
            "content_overlap",
            "exact_match",
            "negation",
            "contradiction",
            "ambiguity",
            "abbreviation",
            "numeric_conflict",
            "long_input",
            "short_input",
            "cheap_confidence_low",
        ):
            assert key in r.signals
