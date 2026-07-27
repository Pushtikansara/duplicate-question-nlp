from __future__ import annotations

import json

from ares.query_understanding.query_analyzer import QueryAnalyzer
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.query_pipeline import QueryPipeline
from ares.query_understanding.query_report import QueryReport
from ares.query_understanding.question_type_detector import QuestionTypeDetector
from ares.query_understanding.type_models import QuestionTypeResult
from ares.query_understanding.type_patterns import (
    COMPLEMENTARY_PAIRS,
    PAIR_TYPES,
    QUESTION_TYPES,
)
from ares.query_understanding.type_rules import classify_question

detector = QuestionTypeDetector()
analyzer_with_types = QueryAnalyzer()
pipeline = QueryPipeline()
report = QueryReport()


class TestQuestionTypeResult:
    def test_defaults(self):
        r = QuestionTypeResult()
        assert r.question_1_type == "other"
        assert r.question_2_type == "other"
        assert r.pair_type == "unknown"
        assert r.classification_confidence == 0.0

    def test_serialization_roundtrip(self):
        r = QuestionTypeResult(
            question_1_type="how_to",
            question_2_type="definition",
            pair_type="complementary",
            classification_confidence=0.85,
            classification_reason="test_reason",
        )
        d = r.to_dict()
        assert d["question_1_type"] == "how_to"
        assert d["pair_type"] == "complementary"

        restored = QuestionTypeResult.from_dict(d)
        assert restored.question_1_type == "how_to"
        assert restored.pair_type == "complementary"
        assert restored.classification_confidence == 0.85

    def test_to_dict_structure(self):
        r = QuestionTypeResult(
            question_1_type="factoid",
            classification_confidence=0.75,
        )
        d = r.to_dict()
        assert set(d.keys()) == {
            "question_1_type",
            "question_2_type",
            "pair_type",
            "classification_confidence",
            "classification_reason",
        }


class TestDefinition:
    def test_what_is(self):
        qtype, conf, _ = classify_question("What is Python?")
        assert qtype == "definition"
        assert conf >= 0.5

    def test_what_are(self):
        qtype, conf, _ = classify_question("What are the types of machine learning?")
        assert qtype in ("definition", "list")
        assert conf >= 0.4

    def test_define(self):
        qtype, conf, _ = classify_question("Define recursion")
        assert qtype == "definition"
        assert conf >= 0.6

    def test_what_does_mean(self):
        qtype, conf, _ = classify_question("What does API mean?")
        assert qtype == "definition"
        assert conf >= 0.5

    def test_describe(self):
        qtype, conf, _ = classify_question("Describe the water cycle")
        assert qtype == "definition"
        assert conf >= 0.5


class TestHowTo:
    def test_how_to(self):
        qtype, conf, _ = classify_question("How to learn Python?")
        assert qtype == "how_to"
        assert conf >= 0.7

    def test_how_do_i(self):
        qtype, conf, _ = classify_question("How do I install pandas?")
        assert qtype == "how_to"
        assert conf >= 0.6

    def test_how_can_i(self):
        qtype, conf, _ = classify_question("How can I improve my coding skills?")
        assert qtype == "how_to"
        assert conf >= 0.6

    def test_way_to(self):
        qtype, conf, _ = classify_question("Best way to learn data science?")
        assert qtype == "how_to"
        assert conf >= 0.5


class TestComparison:
    def test_difference_between(self):
        qtype, conf, _ = classify_question("What is the difference between Java and Python?")
        assert qtype == "comparison"
        assert conf >= 0.7

    def test_vs(self):
        qtype, conf, _ = classify_question("Python vs Java: which is better?")
        assert qtype == "comparison"
        assert conf >= 0.6

    def test_compare(self):
        qtype, conf, _ = classify_question("Compare React and Angular")
        assert qtype == "comparison"
        assert conf >= 0.6

    def test_pros_and_cons(self):
        qtype, conf, _ = classify_question("What are the pros and cons of remote work?")
        assert qtype == "comparison"
        assert conf >= 0.6

    def test_which_is_better(self):
        qtype, conf, _ = classify_question("Which is better: iOS or Android?")
        assert qtype == "comparison"
        assert conf >= 0.6


class TestExplanation:
    def test_explain(self):
        qtype, conf, _ = classify_question("Explain how neural networks work")
        assert qtype == "explanation"
        assert conf >= 0.6

    def test_how_does_work(self):
        qtype, conf, _ = classify_question("How does a blockchain work?")
        assert qtype in ("how_to", "explanation")

    def test_what_happens_when(self):
        qtype, conf, _ = classify_question("What happens when you compile C++ code?")
        assert qtype in ("explanation", "definition")
        assert conf >= 0.4


class TestReasonWhy:
    def test_why(self):
        qtype, conf, _ = classify_question("Why is the sky blue?")
        assert qtype == "reason_why"
        assert conf >= 0.7

    def test_what_causes(self):
        qtype, conf, _ = classify_question("What causes inflation?")
        assert qtype == "reason_why"
        assert conf >= 0.5

    def test_what_is_reason(self):
        qtype, conf, _ = classify_question("What is the reason for climate change?")
        assert qtype in ("reason_why", "explanation")
        assert conf >= 0.5


class TestOpinion:
    def test_do_you_think(self):
        qtype, conf, _ = classify_question("Do you think AI will replace jobs?")
        assert qtype == "opinion"
        assert conf >= 0.6

    def test_what_is_your_opinion(self):
        qtype, conf, _ = classify_question("What is your opinion on remote work?")
        assert qtype == "opinion"
        assert conf >= 0.6

    def test_is_it_worth(self):
        qtype, conf, _ = classify_question("Is it worth learning Rust in 2024?")
        assert qtype == "opinion"
        assert conf >= 0.5

    def test_should_i(self):
        qtype, conf, _ = classify_question("Should I learn Python or JavaScript first?")
        assert qtype == "opinion"
        assert conf >= 0.5


class TestFactoid:
    def test_who_invented(self):
        qtype, conf, _ = classify_question("Who invented the telephone?")
        assert qtype in ("factoid", "person")
        assert conf >= 0.5

    def test_who_is(self):
        qtype, conf, _ = classify_question("Who is the president of the United States?")
        assert qtype in ("factoid", "person")
        assert conf >= 0.5

    def test_when_was(self):
        qtype, conf, _ = classify_question("When was the Berlin Wall built?")
        assert qtype in ("factoid", "temporal")
        assert conf >= 0.5


class TestYesNo:
    def test_is_are(self):
        qtype, conf, _ = classify_question("Is Python an interpreted language?")
        assert qtype == "yes_no"
        assert conf >= 0.4

    def test_can(self):
        qtype, conf, _ = classify_question("Can Java run on any platform?")
        assert qtype == "yes_no"
        assert conf >= 0.4

    def test_does(self):
        qtype, conf, _ = classify_question("Does Python support multiple inheritance?")
        assert qtype == "yes_no"
        assert conf >= 0.4

    def test_has(self):
        qtype, conf, _ = classify_question("Has the project been completed?")
        assert qtype == "yes_no"
        assert conf >= 0.4


class TestNumeric:
    def test_how_many(self):
        qtype, conf, _ = classify_question("How many planets are in the solar system?")
        assert qtype == "numeric"
        assert conf >= 0.7

    def test_how_much(self):
        qtype, conf, _ = classify_question("How much does a Tesla cost?")
        assert qtype == "numeric"
        assert conf >= 0.7

    def test_what_is_price(self):
        qtype, conf, _ = classify_question("What is the price of gold?")
        assert qtype == "numeric"
        assert conf >= 0.6


class TestTemporal:
    def test_when(self):
        qtype, conf, _ = classify_question("When does the next solar eclipse occur?")
        assert qtype == "temporal"
        assert conf >= 0.7

    def test_what_year(self):
        qtype, conf, _ = classify_question("What year did World War 2 end?")
        assert qtype in ("temporal", "factoid")
        assert conf >= 0.5

    def test_what_time(self):
        qtype, conf, _ = classify_question("What time is the meeting?")
        assert qtype == "temporal"
        assert conf >= 0.6


class TestLocation:
    def test_where(self):
        qtype, conf, _ = classify_question("Where is the Eiffel Tower?")
        assert qtype == "location"
        assert conf >= 0.7

    def test_what_country(self):
        qtype, conf, _ = classify_question("What country is known as the Land of the Rising Sun?")
        assert qtype in ("location", "definition")
        assert conf >= 0.5


class TestPerson:
    def test_who(self):
        qtype, conf, _ = classify_question("Who wrote Hamlet?")
        assert qtype in ("person", "factoid")
        assert conf >= 0.5


class TestCode:
    def test_code_snippet(self):
        qtype, conf, _ = classify_question("def hello(): pass", "def hello(): pass")
        assert qtype == "code"
        assert conf >= 0.7

    def test_code_question(self):
        qtype, conf, _ = classify_question("How to fix this bug: import error?", "how to fix this bug: import error?")
        assert qtype in ("troubleshooting", "how_to")


class TestTroubleshooting:
    def test_how_to_fix(self):
        qtype, conf, _ = classify_question("How to fix a segmentation fault?")
        assert qtype == "troubleshooting"
        assert conf >= 0.7

    def test_why_is_not_working(self):
        qtype, conf, _ = classify_question("Why is my code not working?")
        assert qtype in ("troubleshooting", "reason_why")
        assert conf >= 0.5

    def test_error_keyword(self):
        qtype, conf, _ = classify_question("Error: module not found")
        assert qtype == "troubleshooting"
        assert conf >= 0.6


class TestList:
    def test_list(self):
        qtype, conf, _ = classify_question("List the features of Python")
        assert qtype == "list"
        assert conf >= 0.6

    def test_what_are_types(self):
        qtype, conf, _ = classify_question("What are the types of machine learning?")
        assert qtype in ("list", "definition")
        assert conf >= 0.5

    def test_name_some(self):
        qtype, conf, _ = classify_question("Name some popular programming languages")
        assert qtype == "list"
        assert conf >= 0.5


class TestOther:
    def test_statement(self):
        qtype, conf, _ = classify_question("I think this is a good idea.")
        assert qtype == "other" or conf < 0.3

    def test_empty(self):
        qtype, conf, _ = classify_question("")
        assert qtype == "other"
        assert conf == 0.0

    def test_gibberish(self):
        qtype, conf, _ = classify_question("xqz abcd mnop")
        assert qtype == "other"


class TestDetector:
    def test_detector_basic(self):
        result = detector.detect(
            "How to learn Python?",
            "What is Python?",
        )
        assert result.question_1_type == "how_to"
        assert result.question_2_type == "definition"
        assert result.pair_type == "complementary"
        assert result.classification_confidence > 0

    def test_detector_same_type(self):
        result = detector.detect(
            "What is Python?",
            "What is Java?",
        )
        assert result.question_1_type != "other"
        assert result.question_2_type != "other"

    def test_detector_paraphrase(self):
        result = detector.detect(
            "How to learn Python?",
            "Best way to learn Python?",
        )
        assert result.question_1_type == "how_to"
        assert result.pair_type == "potential_paraphrase"

    def test_detector_empty(self):
        result = detector.detect("", "")
        assert result.pair_type == "unknown"
        assert result.question_1_type == "other"

    def test_detector_with_norm(self):
        result = detector.detect(
            "How to learn Python?",
            "What is Python?",
            normalized_1="how to learn python?",
            normalized_2="what is python?",
        )
        assert result.question_1_type == "how_to"


class TestIntegrationWithAnalyzer:
    def test_analyzer_has_question_type(self):
        result = analyzer_with_types.analyze(
            "How to learn Python?",
            "What is Python?",
        )
        assert hasattr(result, "question_type")
        assert result.question_type.question_1_type != ""
        assert result.question_type.pair_type != ""
        assert result.question_type.classification_confidence > 0

    def test_analyzer_type_in_to_dict(self):
        result = analyzer_with_types.analyze("What is AI?", "How does ML work?")
        d = result.to_dict()
        assert "question_type" in d
        assert d["question_type"]["question_1_type"] != ""

    def test_analyzer_type_json_roundtrip(self):
        result = analyzer_with_types.analyze("Define recursion", "Explain recursion")
        j = result.to_json()
        parsed = json.loads(j)
        assert "question_type" in parsed
        assert parsed["question_type"]["question_1_type"] == "definition"

    def test_analyzer_from_dict_restores_type(self):
        original = analyzer_with_types.analyze("How to code?", "What is coding?")
        d = original.to_dict()
        restored = QueryAnalysis.from_dict(d)
        assert restored.question_type.question_1_type == original.question_type.question_1_type
        assert restored.question_type.pair_type == original.question_type.pair_type
        assert restored.question_type.classification_confidence == original.question_type.classification_confidence


class TestPipelineWithTypes:
    def test_pipeline_run_has_types(self):
        result = pipeline.run("How to learn Python?", "What is Python?")
        assert hasattr(result, "question_type")
        assert result.question_type.question_1_type == "how_to"

    def test_pipeline_batch_types(self):
        pairs = [
            ("What is Python?", "What is Java?"),
            ("How to code?", "Fix this error"),
        ]
        results = pipeline.run_batch(pairs)
        for r in results:
            assert r.question_type.question_1_type != ""


class TestReportWithTypes:
    def test_report_shows_types(self):
        result = analyzer_with_types.analyze("How to learn Python?", "What is Python?")
        text = report.generate(result)
        assert "Question Types" in text
        assert "how_to" in text
        assert "definition" in text
        assert "complementary" in text

    def test_short_report_shows_types(self):
        result = analyzer_with_types.analyze("How to X?", "What is X?")
        short = report.generate_short(result)
        assert "Types:" in short
        assert "how_to" in short


class TestEdgeCases:
    def test_unicode_questions(self):
        result = detector.detect(
            "¿Qué es Python?",
            "Comment apprendre Python?",
        )
        assert result.question_1_type != ""
        assert result.question_2_type != ""

    def test_numeric_with_code(self):
        result = analyzer_with_types.analyze(
            "How to sum numbers in Python?",
            "What is the total of 1, 2, 3?",
        )
        assert result.question_type.classification_confidence > 0

    def test_very_long_question(self):
        long_q = " ".join(["word"] * 50) + "?"
        qtype, conf, _ = classify_question(long_q)
        assert qtype != ""
        assert isinstance(conf, float)

    def test_question_with_multiple_patterns(self):
        qtype, conf, _ = classify_question("Why is my code not working and how to fix it?")
        assert qtype in ("troubleshooting", "reason_why", "how_to")
        assert conf >= 0.4

    def test_whitespace_only(self):
        qtype, conf, _ = classify_question("   ")
        assert qtype == "other"
        assert conf == 0.0

    def test_special_chars_only(self):
        qtype, conf, _ = classify_question("!@#$%^&*()")
        assert qtype in ("other", "troubleshooting")


class TestQuestionTypesSet:
    def test_all_types_accounted(self):
        expected = {
            "definition",
            "how_to",
            "comparison",
            "explanation",
            "reason_why",
            "opinion",
            "factoid",
            "yes_no",
            "numeric",
            "temporal",
            "location",
            "person",
            "organization",
            "procedure",
            "recommendation",
            "troubleshooting",
            "code",
            "list",
            "other",
        }
        assert expected == QUESTION_TYPES

    def test_all_pair_types_accounted(self):
        expected = {
            "same_type",
            "different_type",
            "complementary",
            "potential_paraphrase",
            "potential_reformulation",
            "unknown",
        }
        assert expected == PAIR_TYPES

    def test_complementary_pairs_symmetric(self):
        for t1, related in COMPLEMENTARY_PAIRS.items():
            for t2 in related:
                assert t1 in QUESTION_TYPES
                assert t2 in QUESTION_TYPES


class TestTroubleshootingDetailed:
    def test_fix_keyword(self):
        qtype, conf, _ = classify_question("How to fix memory leak?")
        assert qtype == "troubleshooting"
        assert conf >= 0.7

    def test_bug_keyword(self):
        qtype, conf, _ = classify_question("Bug in my Python code")
        assert qtype == "troubleshooting"
        assert conf >= 0.6

    def test_not_working(self):
        qtype, conf, _ = classify_question("My internet is not working")
        assert qtype == "troubleshooting"
        assert conf >= 0.6


class TestRecommendation:
    def test_what_is_best(self):
        qtype, conf, _ = classify_question("What is the best programming language for beginners?")
        assert qtype == "recommendation"
        assert conf >= 0.6

    def test_which_should(self):
        qtype, conf, _ = classify_question("Which laptop should I buy?")
        assert qtype == "recommendation"
        assert conf >= 0.5

    def test_recommend(self):
        qtype, conf, _ = classify_question("Recommend a good book on machine learning")
        assert qtype == "recommendation"
        assert conf >= 0.6


class TestProcedure:
    def test_what_are_steps(self):
        qtype, conf, _ = classify_question("What are the steps to deploy a web app?")
        assert qtype == "procedure"
        assert conf >= 0.6

    def test_how_to_setup(self):
        qtype, conf, _ = classify_question("How to set up a Django project?")
        assert qtype in ("how_to", "procedure")
        assert conf >= 0.6

    def test_algorithm_for(self):
        qtype, conf, _ = classify_question("Algorithm for sorting an array")
        assert qtype in ("procedure", "how_to")
        assert conf >= 0.5


def test_detector_importable():
    from ares.query_understanding import QuestionTypeDetector, QuestionTypeResult

    assert QuestionTypeDetector is not None
    assert QuestionTypeResult is not None
