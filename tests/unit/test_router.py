from __future__ import annotations

import time

from ares.query_understanding.complexity_models import ComplexityAnalysis
from ares.query_understanding.entity_models import EntityResult
from ares.query_understanding.query_models import (
    QuestionMetadata,
    QuestionSimilarityFeatures,
)
from ares.query_understanding.relationship_models import (
    ComparisonStatistics,
    RelationshipAnalysis,
    RelationshipInfo,
)
from ares.query_understanding.router_engine import RouterEngine
from ares.query_understanding.router_models import (
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_NORMAL,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    ROUTING_STRATEGIES,
    STRATEGY_BASELINE,
    STRATEGY_CROSS_ENCODER,
    STRATEGY_ENSEMBLE,
    STRATEGY_FALLBACK,
    STRATEGY_FAST_LEXICAL,
    RoutingDecision,
)
from ares.query_understanding.router_report import RouterReport
from ares.query_understanding.router_rules import (
    RouterRule,
    _extract_signal,
    _register_rules,
    compute_strategy_scores,
)
from ares.query_understanding.type_models import QuestionTypeResult


# ============================================================
# RoutingDecision model
# ============================================================
class TestRoutingDecision:
    def test_defaults(self):
        d = RoutingDecision()
        assert d.selected_strategy == STRATEGY_FALLBACK
        assert d.confidence == 0.0
        assert d.priority == PRIORITY_NORMAL
        assert d.risk_level == RISK_LOW
        assert d.version == "1.0.0"

    def test_to_dict(self):
        d = RoutingDecision(selected_strategy=STRATEGY_CROSS_ENCODER, confidence=0.85)
        result = d.to_dict()
        assert result["selected_strategy"] == STRATEGY_CROSS_ENCODER
        assert result["confidence"] == 0.85

    def test_to_dict_includes_all_keys(self):
        d = RoutingDecision()
        keys = d.to_dict().keys()
        expected = {
            "selected_strategy",
            "confidence",
            "priority",
            "reason_codes",
            "triggered_rules",
            "risk_level",
            "estimated_cost",
            "estimated_latency",
            "explanation",
            "processing_time",
            "version",
        }
        assert keys == expected

    def test_from_dict(self):
        d = RoutingDecision.from_dict({"selected_strategy": STRATEGY_ENSEMBLE, "confidence": 0.9})
        assert d.selected_strategy == STRATEGY_ENSEMBLE
        assert d.confidence == 0.9

    def test_from_dict_empty(self):
        d = RoutingDecision.from_dict({})
        assert d.selected_strategy == STRATEGY_FALLBACK

    def test_roundtrip(self):
        d1 = RoutingDecision(
            selected_strategy=STRATEGY_CROSS_ENCODER,
            confidence=0.75,
            priority=PRIORITY_HIGH,
            reason_codes=["negation_detected", "entity_dense"],
            risk_level=RISK_MEDIUM,
        )
        d2 = RoutingDecision.from_dict(d1.to_dict())
        assert d2.selected_strategy == STRATEGY_CROSS_ENCODER
        assert d2.confidence == 0.75
        assert d2.priority == PRIORITY_HIGH
        assert d2.reason_codes == ["negation_detected", "entity_dense"]

    def test_json_serializable(self):
        import json

        d = RoutingDecision(selected_strategy=STRATEGY_FAST_LEXICAL)
        s = json.dumps(d.to_dict())
        assert isinstance(s, str)

    def test_strategies_constant(self):
        assert STRATEGY_FAST_LEXICAL in ROUTING_STRATEGIES
        assert STRATEGY_BASELINE in ROUTING_STRATEGIES
        assert STRATEGY_CROSS_ENCODER in ROUTING_STRATEGIES
        assert STRATEGY_ENSEMBLE in ROUTING_STRATEGIES
        assert STRATEGY_FALLBACK in ROUTING_STRATEGIES


# ============================================================
# Signal extraction
# ============================================================
class TestSignalExtraction:
    def test_empty_signal(self):
        signal = _extract_signal()
        assert signal.complexity == 0.0
        assert not signal.has_negation
        assert signal.entity_count_total == 0
        assert not signal.is_empty

    def test_with_complexity(self):
        ca = ComplexityAnalysis(overall_complexity_score=0.5, ambiguity_score=0.3)
        signal = _extract_signal(complexity_analysis=ca)
        assert signal.complexity == 0.5
        assert signal.ambiguity == 0.3

    def test_with_entity_analysis(self):
        from ares.query_understanding.entity_models import Entity

        entities = [
            Entity(text="Python", entity_type="LANGUAGE", start=0, end=6),
            Entity(text="Java", entity_type="LANGUAGE", start=0, end=4),
        ]
        er = EntityResult(entities_1=entities, entities_2=entities)
        ca = ComplexityAnalysis(entity_density=0.5)
        signal = _extract_signal(entity_analysis=er, complexity_analysis=ca)
        assert signal.entity_count_total == 4
        assert signal.entity_density == 0.5

    def test_with_relationship_types(self):
        ra = RelationshipAnalysis(
            relationship_types=[
                RelationshipInfo(relationship_type="negation_introduced", confidence=0.9),
                RelationshipInfo(relationship_type="antonym_detection", confidence=0.8),
            ],
            risk_flags=["entity_conflict"],
        )
        signal = _extract_signal(relationship_analysis=ra)
        assert signal.has_negation
        assert signal.has_antonym
        assert signal.has_entity_conflict

    def test_with_risk_flags(self):
        ra = RelationshipAnalysis(risk_flags=["numeric_conflict", "version_conflict", "temporal_conflict"])
        signal = _extract_signal(relationship_analysis=ra)
        assert signal.has_numeric_conflict
        assert signal.has_version_conflict
        assert signal.has_date_conflict

    def test_with_similarity(self):
        sim = QuestionSimilarityFeatures(word_overlap_ratio=0.8)
        signal = _extract_signal(similarity=sim)
        assert signal.overlap_ratio == 0.8

    def test_with_question_type(self):
        qt = QuestionTypeResult(pair_type="comparison", classification_confidence=0.9)
        signal = _extract_signal(question_type=qt)
        assert signal.question_type_pair == "comparison"
        assert signal.type_confidence == 0.9

    def test_cross_lingual(self):
        m1 = QuestionMetadata(language="en")
        m2 = QuestionMetadata(language="fr")
        signal = _extract_signal(metadata_1=m1, metadata_2=m2)
        assert signal.has_cross_lingual

    def test_not_cross_lingual(self):
        m1 = QuestionMetadata(language="en")
        m2 = QuestionMetadata(language="en")
        signal = _extract_signal(metadata_1=m1, metadata_2=m2)
        assert not signal.has_cross_lingual

    def test_code_detected(self):
        m1 = QuestionMetadata(contains_code=True)
        signal = _extract_signal(metadata_1=m1)
        assert signal.has_code

    def test_low_confidence(self):
        ca = ComplexityAnalysis(confidence_estimate=0.2)
        signal = _extract_signal(complexity_analysis=ca)
        assert signal.has_low_confidence

    def test_high_risk(self):
        ra = RelationshipAnalysis(
            risk_flags=["meaning_changed", "negation_conflict", "entity_conflict"],
        )
        signal = _extract_signal(relationship_analysis=ra)
        assert signal.has_high_risk

    def test_semantic_drift(self):
        ra = RelationshipAnalysis(risk_flags=["high_semantic_drift"])
        signal = _extract_signal(relationship_analysis=ra)
        assert signal.has_semantic_drift

    def test_exact_match(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo(relationship_type="exact_match", confidence=1.0)],
        )
        signal = _extract_signal(relationship_analysis=ra)
        assert signal.has_exact_match

    def test_near_match(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo(relationship_type="near_match", confidence=0.85)],
        )
        signal = _extract_signal(relationship_analysis=ra)
        assert signal.has_near_match

    def test_with_empty_entities(self):
        er = EntityResult(entities_1=[], entities_2=[])
        ca = ComplexityAnalysis(entity_density=0.0)
        signal = _extract_signal(entity_analysis=er, complexity_analysis=ca)
        assert signal.entity_count_total == 0
        assert signal.entity_density == 0.0

    def test_with_comparison_stats(self):
        stats = ComparisonStatistics(jaccard_similarity=0.5, edit_distance=10, length_difference=3)
        ra = RelationshipAnalysis(comparison_statistics=stats)
        signal = _extract_signal(relationship_analysis=ra)
        assert signal.jaccard == 0.5
        assert signal.edit_distance == 10.0
        assert signal.length_difference == 3


# ============================================================
# RouterRule
# ============================================================
class TestRouterRule:
    def test_rule_apply_true(self):
        rule = RouterRule(
            name="test_rule",
            description="Test",
            weight=1.0,
            category="fast_path",
            evaluate=lambda s: 1.0 if s.has_exact_match else 0.0,
        )
        signal = _extract_signal()
        assert rule.apply(signal) == 0.0
        signal.has_exact_match = True
        assert rule.apply(signal) == 1.0

    def test_rule_with_weight(self):
        rule = RouterRule(
            name="weighted",
            description="Weighted",
            weight=0.5,
            category="cross_encoder",
            evaluate=lambda s: 1.0 if s.has_negation else 0.0,
        )
        signal = _extract_signal()
        assert rule.apply(signal) == 0.0
        signal.has_negation = True
        assert rule.apply(signal) == 1.0

    def test_rules_registered(self):
        rules = _register_rules()
        assert len(rules) >= 15
        rule_names = {r.name for r in rules}
        assert "exact_match_simple" in rule_names
        assert "very_low_complexity" in rule_names
        assert "entity_dense" in rule_names
        assert "negation_conflict" in rule_names
        assert "high_ambiguity" in rule_names
        assert "semantic_drift" in rule_names
        assert "cross_lingual" in rule_names
        assert "fallback_default" in rule_names

    def test_all_rules_have_categories(self):
        rules = _register_rules()
        valid = {"fast_path", "baseline", "cross_encoder", "ensemble", "fallback"}
        for r in rules:
            assert r.category in valid, f"Rule {r.name} has invalid category {r.category}"

    def test_all_rules_have_positive_weights(self):
        rules = _register_rules()
        for r in rules:
            assert r.weight > 0.0, f"Rule {r.name} has non-positive weight"


# ============================================================
# Strategy scoring
# ============================================================
class TestStrategyScoring:
    def test_empty_signal(self):
        signal = _extract_signal()
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert isinstance(scores, dict)
        assert STRATEGY_FAST_LEXICAL in scores
        assert STRATEGY_CROSS_ENCODER in scores
        assert STRATEGY_ENSEMBLE in scores
        assert isinstance(triggered, list)

    def test_exact_match_low_complexity(self):
        signal = _extract_signal()
        signal.has_exact_match = True
        signal.complexity = 0.1
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_FAST_LEXICAL]["score"] > 0.0

    def test_negation_triggers_cross_encoder(self):
        signal = _extract_signal()
        signal.has_negation = True
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_CROSS_ENCODER]["score"] > 0.0

    def test_high_ambiguity_triggers_ensemble(self):
        signal = _extract_signal()
        signal.ambiguity = 0.5
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_ENSEMBLE]["score"] > 0.0

    def test_entity_dense_triggers_cross_encoder(self):
        signal = _extract_signal()
        signal.entity_density = 0.5
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_CROSS_ENCODER]["score"] > 0.0

    def test_entity_count_high(self):
        signal = _extract_signal()
        signal.entity_count_total = 5
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_CROSS_ENCODER]["score"] > 0.0

    def test_antonym_triggers_cross_encoder(self):
        signal = _extract_signal()
        signal.has_antonym = True
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_CROSS_ENCODER]["score"] > 0.0

    def test_numeric_conflict_triggers_cross_encoder(self):
        signal = _extract_signal()
        signal.has_numeric_conflict = True
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_CROSS_ENCODER]["score"] > 0.0

    def test_high_risk_triggers_ensemble(self):
        signal = _extract_signal()
        signal.has_high_risk = True
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_ENSEMBLE]["score"] > 0.0

    def test_semantic_drift_triggers_ensemble(self):
        signal = _extract_signal()
        signal.has_semantic_drift = True
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_ENSEMBLE]["score"] > 0.0

    def test_cross_lingual_triggers_cross_encoder(self):
        signal = _extract_signal()
        signal.has_cross_lingual = True
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_CROSS_ENCODER]["score"] > 0.0

    def test_code_triggers_cross_encoder(self):
        signal = _extract_signal()
        signal.has_code = True
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_CROSS_ENCODER]["score"] > 0.0

    def test_low_confidence_triggers_ensemble(self):
        signal = _extract_signal()
        signal.has_low_confidence = True
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_ENSEMBLE]["score"] > 0.0

    def test_very_short_exact(self):
        signal = _extract_signal()
        signal.has_exact_match = True
        signal.word_count_total = 4
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_BASELINE]["score"] > 0.0

    def test_complex_question(self):
        signal = _extract_signal()
        signal.complexity = 0.7
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_CROSS_ENCODER]["score"] > 0.0

    def test_multiple_rules_trigger(self):
        signal = _extract_signal()
        signal.has_negation = True
        signal.has_antonym = True
        signal.entity_density = 0.4
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert len(triggered) >= 3
        names = [t["rule"] for t in triggered]
        assert "negation_conflict" in names
        assert "antonym_conflict" in names
        assert "entity_dense" in names

    def test_cost_map(self):
        signal = _extract_signal()
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_FAST_LEXICAL]["cost"] < scores[STRATEGY_ENSEMBLE]["cost"]
        assert scores[STRATEGY_FAST_LEXICAL]["latency"] < scores[STRATEGY_CROSS_ENCODER]["latency"]

    def test_risk_map(self):
        signal = _extract_signal()
        rules = _register_rules()
        scores, triggered = compute_strategy_scores(signal, rules)
        assert scores[STRATEGY_FAST_LEXICAL]["risk"] == RISK_LOW
        assert scores[STRATEGY_ENSEMBLE]["risk"] == RISK_HIGH


# ============================================================
# RouterEngine
# ============================================================
class TestRouterEngine:
    def test_empty_input(self):
        engine = RouterEngine()
        decision = engine.decide("", "")
        assert decision.selected_strategy == STRATEGY_FALLBACK
        assert "empty_input" in decision.reason_codes

    def test_simple_questions(self):
        engine = RouterEngine()
        m1 = QuestionMetadata(word_count=3, language="en")
        m2 = QuestionMetadata(word_count=3, language="en")
        sim = QuestionSimilarityFeatures(word_overlap_ratio=0.5)
        ca = ComplexityAnalysis(overall_complexity_score=0.12, ambiguity_score=0.0)
        ra = RelationshipAnalysis()
        decision = engine.decide(
            "What is Python?",
            "What is Java?",
            metadata_1=m1,
            metadata_2=m2,
            similarity=sim,
            complexity_analysis=ca,
            relationship_analysis=ra,
        )
        assert decision.selected_strategy in ROUTING_STRATEGIES
        assert decision.processing_time >= 0.0
        assert decision.version == "1.0.0"

    def test_entity_dense_routes_cross_encoder(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(overall_complexity_score=0.3, entity_density=0.5)
        decision = engine.decide("A", "B", complexity_analysis=ca)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER

    def test_negation_routes_cross_encoder(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo(relationship_type="negation_introduced", confidence=0.9)],
        )
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER

    def test_high_ambiguity_routes_ensemble(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(overall_complexity_score=0.3, ambiguity_score=0.5)
        decision = engine.decide("A", "B", complexity_analysis=ca)
        assert decision.selected_strategy == STRATEGY_ENSEMBLE

    def test_low_complexity_exact_routes_fast_lexical(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo(relationship_type="exact_match", confidence=1.0)],
        )
        ca = ComplexityAnalysis(overall_complexity_score=0.05)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_FAST_LEXICAL

    def test_very_short_exact_routes_baseline(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo(relationship_type="exact_match", confidence=1.0)],
        )
        ca = ComplexityAnalysis(overall_complexity_score=0.1)
        m1 = QuestionMetadata(word_count=2)
        m2 = QuestionMetadata(word_count=2)
        decision = engine.decide(
            "A",
            "B",
            metadata_1=m1,
            metadata_2=m2,
            complexity_analysis=ca,
            relationship_analysis=ra,
        )
        assert decision.selected_strategy == STRATEGY_BASELINE

    def test_high_risk_routes_ensemble(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(
            risk_flags=["meaning_changed", "negation_conflict", "entity_conflict"],
        )
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_ENSEMBLE

    def test_complex_question_routes_cross_encoder(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(overall_complexity_score=0.7)
        decision = engine.decide("A", "B", complexity_analysis=ca)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER

    def test_cross_lingual_routes_cross_encoder(self):
        engine = RouterEngine()
        m1 = QuestionMetadata(language="en")
        m2 = QuestionMetadata(language="fr")
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        decision = engine.decide("A", "B", metadata_1=m1, metadata_2=m2, complexity_analysis=ca)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER

    def test_reason_codes_present(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(overall_complexity_score=0.7)
        decision = engine.decide("A", "B", complexity_analysis=ca)
        assert len(decision.reason_codes) > 0
        assert "complex_question" in decision.reason_codes

    def test_explanation_not_empty(self):
        engine = RouterEngine()
        decision = engine.decide("A", "B")
        assert decision.explanation != ""

    def test_triggered_rules_in_decision(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(overall_complexity_score=0.7)
        decision = engine.decide("A", "B", complexity_analysis=ca)
        assert len(decision.triggered_rules) > 0
        assert any(t["rule"] == "complex_question" for t in decision.triggered_rules)

    def test_confidence_reflects_score(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo(relationship_type="exact_match", confidence=1.0)],
        )
        ca = ComplexityAnalysis(overall_complexity_score=0.05)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.confidence > 0.0

    def test_latency_estimate_non_negative(self):
        engine = RouterEngine()
        decision = engine.decide("A", "B")
        assert decision.estimated_latency >= 0.0

    def test_cost_estimate_non_negative(self):
        engine = RouterEngine()
        decision = engine.decide("A", "B")
        assert decision.estimated_cost >= 0.0

    def test_with_all_inputs(self):
        engine = RouterEngine()
        m1 = QuestionMetadata(word_count=5, language="en", contains_code=False)
        m2 = QuestionMetadata(word_count=5, language="en", contains_code=False)
        sim = QuestionSimilarityFeatures(word_overlap_ratio=0.6)
        qt = QuestionTypeResult(pair_type="comparison", classification_confidence=0.8)
        er = EntityResult()
        ra = RelationshipAnalysis()
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        decision = engine.decide(
            "Q1",
            "Q2",
            metadata_1=m1,
            metadata_2=m2,
            similarity=sim,
            question_type=qt,
            entity_analysis=er,
            relationship_analysis=ra,
            complexity_analysis=ca,
        )
        assert decision.selected_strategy in ROUTING_STRATEGIES


# ============================================================
# RouterReport
# ============================================================
class TestRouterReport:
    def test_generate_default(self):
        report = RouterReport()
        d = RoutingDecision(selected_strategy=STRATEGY_CROSS_ENCODER, confidence=0.85)
        text = report.generate(d)
        assert "ROUTING DECISION REPORT" in text
        assert STRATEGY_CROSS_ENCODER in text

    def test_generate_detailed(self):
        report = RouterReport()
        d = RoutingDecision(
            selected_strategy=STRATEGY_ENSEMBLE,
            confidence=0.9,
            triggered_rules=[
                {
                    "rule": "high_ambiguity",
                    "description": "High ambiguity",
                    "category": "ensemble",
                    "score": 0.85,
                    "weight": 0.85,
                }
            ],
        )
        text = report.generate(d, detailed=True)
        assert "TRIGGERED RULES" in text
        assert "EXPLANATION" in text

    def test_generate_short(self):
        report = RouterReport()
        d = RoutingDecision(selected_strategy=STRATEGY_FAST_LEXICAL, confidence=0.7)
        text = report.generate(d, detailed=False)
        assert "ROUTING DECISION REPORT" in text
        assert "TRIGGERED RULES" not in text

    def test_short_report(self):
        report = RouterReport()
        d = RoutingDecision(selected_strategy=STRATEGY_CROSS_ENCODER, confidence=0.85)
        text = report.short_report(d)
        assert STRATEGY_CROSS_ENCODER in text

    def test_report_with_reason_codes(self):
        report = RouterReport()
        d = RoutingDecision(
            selected_strategy=STRATEGY_CROSS_ENCODER,
            reason_codes=["negation_detected", "entity_dense"],
        )
        text = report.generate(d)
        assert "negation_detected" in text
        assert "entity_dense" in text

    def test_report_empty_triggered(self):
        report = RouterReport()
        d = RoutingDecision()
        text = report.generate(d, detailed=True)
        assert "No rules triggered" in text


# ============================================================
# Specific routing scenarios
# ============================================================
class TestRoutingScenarios:
    def test_exact_identical(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo(relationship_type="exact_match", confidence=1.0)],
        )
        ca = ComplexityAnalysis(overall_complexity_score=0.05)
        decision = engine.decide("Hello world", "Hello world", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_FAST_LEXICAL

    def test_entity_heavy(self):
        engine = RouterEngine()
        from ares.query_understanding.entity_models import Entity

        entities = [Entity(text=f"E{i}", entity_type="TYPE", start=0, end=1) for i in range(6)]
        er = EntityResult(entities_1=entities, entities_2=entities)
        ca = ComplexityAnalysis(entity_density=0.6)
        decision = engine.decide("A", "B", entity_analysis=er, complexity_analysis=ca)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER

    def test_numeric_conflict(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(
            risk_flags=["numeric_conflict"],
        )
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER

    def test_negation_and_entity(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo(relationship_type="negation_introduced", confidence=0.9)],
        )
        ca = ComplexityAnalysis(entity_density=0.4, overall_complexity_score=0.3)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER

    def test_ambiguity_and_risk(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(ambiguity_score=0.5, overall_complexity_score=0.3)
        ra = RelationshipAnalysis(risk_flags=["meaning_changed", "entity_conflict"])
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_ENSEMBLE

    def test_conflicting_signals_ensemble_wins(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(ambiguity_score=0.5, entity_density=0.4, overall_complexity_score=0.4)
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo(relationship_type="negation_introduced", confidence=0.9)],
            risk_flags=["entity_conflict"],
        )
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy in (STRATEGY_ENSEMBLE, STRATEGY_CROSS_ENCODER)

    def test_empty_with_metadata(self):
        engine = RouterEngine()
        decision = engine.decide("", "full question")
        assert decision.selected_strategy == STRATEGY_FALLBACK

    def test_whitespace_only_input(self):
        engine = RouterEngine()
        decision = engine.decide("   ", "   ")
        assert decision.selected_strategy == STRATEGY_FALLBACK

    def test_very_long_questions(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(overall_complexity_score=0.7, question_length_score=1.0)
        decision = engine.decide("A" * 200, "B" * 200, complexity_analysis=ca)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER

    def test_code_question(self):
        engine = RouterEngine()
        m1 = QuestionMetadata(contains_code=True)
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        decision = engine.decide("A", "B", metadata_1=m1, complexity_analysis=ca)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER

    def test_date_conflict(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(risk_flags=["temporal_conflict"])
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER

    def test_version_conflict(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(risk_flags=["version_conflict"])
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_CROSS_ENCODER


# ============================================================
# Performance
# ============================================================
class TestPerformance:
    def test_average_under_1ms(self):
        engine = RouterEngine()
        times = []
        m1 = QuestionMetadata(word_count=5, language="en")
        m2 = QuestionMetadata(word_count=5, language="en")
        sim = QuestionSimilarityFeatures(word_overlap_ratio=0.5)
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        ra = RelationshipAnalysis()
        for _ in range(50):
            start = time.time()
            engine.decide(
                "Q1",
                "Q2",
                metadata_1=m1,
                metadata_2=m2,
                similarity=sim,
                complexity_analysis=ca,
                relationship_analysis=ra,
            )
            times.append((time.time() - start) * 1000)
        avg = sum(times) / len(times)
        assert avg < 1.0

    def test_bulk_throughput(self):
        engine = RouterEngine()
        pairs = [
            ("A", "B"),
            ("What is Python?", "What is Java?"),
            ("How does X work?", "How does Y work?"),
            ("Compare A and B", "Differences between C and D"),
            ("Why is the sky blue?", "Explain color of sky"),
        ]
        start = time.time()
        for q1, q2 in pairs:
            engine.decide(q1, q2)
        elapsed = (time.time() - start) * 1000
        assert elapsed < 50.0


# ============================================================
# Integration with QueryAnalyzer
# ============================================================
class TestIntegration:
    def test_analyzer_has_routing_decision(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        assert hasattr(result, "routing_decision")
        assert isinstance(result.routing_decision, RoutingDecision)

    def test_routing_decision_in_to_dict(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("A", "B")
        d = result.to_dict()
        assert "routing_decision" in d
        assert "selected_strategy" in d["routing_decision"]

    def test_routing_roundtrip(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer
        from ares.query_understanding.query_models import QueryAnalysis

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("A", "B")
        d = result.to_dict()
        restored = QueryAnalysis.from_dict(d)
        assert restored.routing_decision.selected_strategy == result.routing_decision.selected_strategy
        assert restored.routing_decision.confidence == result.routing_decision.confidence

    def test_pipeline_includes_routing(self):
        from ares.query_understanding.query_pipeline import QueryPipeline

        pipeline = QueryPipeline()
        result = pipeline.run("What is Python?", "What is Java?")
        assert result.routing_decision.selected_strategy in ROUTING_STRATEGIES

    def test_full_report_includes_routing(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer
        from ares.query_understanding.query_report import QueryReport

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        report = QueryReport()
        text = report.generate(result)
        assert "routing" in text.lower() or "Routing" in text


# ============================================================
# Edge cases
# ============================================================
class TestEdgeCases:
    def test_non_string_input(self):
        engine = RouterEngine()
        decision = engine.decide("", "")
        assert decision.selected_strategy == STRATEGY_FALLBACK

    def test_unicode_questions(self):
        engine = RouterEngine()
        m1 = QuestionMetadata(language="es")
        m2 = QuestionMetadata(language="de")
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        decision = engine.decide("¿Qué?", "Was?", metadata_1=m1, metadata_2=m2, complexity_analysis=ca)
        assert decision.selected_strategy in ROUTING_STRATEGIES

    def test_very_low_confidence(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(confidence_estimate=0.1, overall_complexity_score=0.4)
        decision = engine.decide("A", "B", complexity_analysis=ca)
        assert decision.selected_strategy == STRATEGY_ENSEMBLE

    def test_high_overlap_no_entities(self):
        engine = RouterEngine()
        sim = QuestionSimilarityFeatures(word_overlap_ratio=0.85)
        ca = ComplexityAnalysis(overall_complexity_score=0.1)
        decision = engine.decide("A", "B", similarity=sim, complexity_analysis=ca)
        assert decision.selected_strategy == STRATEGY_FAST_LEXICAL

    def test_no_signals_fallback_to_fast_lexical(self):
        engine = RouterEngine()
        decision = engine.decide("Some question", "Another question")
        assert decision.selected_strategy == STRATEGY_FAST_LEXICAL

    def test_risk_level_present(self):
        engine = RouterEngine()
        decision = engine.decide("A", "B")
        assert decision.risk_level in (RISK_LOW, RISK_MEDIUM, RISK_HIGH)

    def test_priority_present(self):
        engine = RouterEngine()
        decision = engine.decide("A", "B")
        assert decision.priority in (PRIORITY_LOW, PRIORITY_NORMAL, PRIORITY_HIGH)

    def test_triggered_rules_structure(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(overall_complexity_score=0.7)
        decision = engine.decide("A", "B", complexity_analysis=ca)
        if decision.triggered_rules:
            t = decision.triggered_rules[0]
            assert "rule" in t
            assert "description" in t
            assert "category" in t
            assert "score" in t
            assert "weight" in t

    def test_multiple_reason_codes(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo(relationship_type="negation_introduced", confidence=0.9)],
            risk_flags=["entity_conflict"],
        )
        ca = ComplexityAnalysis(entity_density=0.4, overall_complexity_score=0.3)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert len(decision.reason_codes) >= 2

    def test_semantic_drift_detected(self):
        engine = RouterEngine()
        ra = RelationshipAnalysis(risk_flags=["high_semantic_drift"])
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_ENSEMBLE

    def test_low_overlap_no_entities_fast(self):
        engine = RouterEngine()
        sim = QuestionSimilarityFeatures(word_overlap_ratio=0.1)
        ca = ComplexityAnalysis(overall_complexity_score=0.1)
        ra = RelationshipAnalysis()
        decision = engine.decide("A", "B", similarity=sim, complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_FAST_LEXICAL

    def test_high_jaccard_fast(self):
        engine = RouterEngine()
        stats = ComparisonStatistics(jaccard_similarity=0.8)
        ra = RelationshipAnalysis(comparison_statistics=stats)
        ca = ComplexityAnalysis(overall_complexity_score=0.2)
        decision = engine.decide("A", "B", complexity_analysis=ca, relationship_analysis=ra)
        assert decision.selected_strategy == STRATEGY_FAST_LEXICAL


# ============================================================
# Regression
# ============================================================
class TestRegression:
    def test_regression_simple_pair(self):
        engine = RouterEngine()
        decision = engine.decide("What is Python?", "What is Java?")
        assert decision.selected_strategy in ROUTING_STRATEGIES
        assert decision.processing_time >= 0.0

    def test_regression_complex_pair(self):
        engine = RouterEngine()
        ca = ComplexityAnalysis(overall_complexity_score=0.65)
        decision = engine.decide(
            "How does gradient descent with momentum compare to Adam?",
            "Differences between supervised and unsupervised learning",
            complexity_analysis=ca,
        )
        assert decision.selected_strategy in (STRATEGY_CROSS_ENCODER, STRATEGY_ENSEMBLE)

    def test_regression_deterministic(self):
        engine = RouterEngine()
        m1 = QuestionMetadata(word_count=3, language="en")
        m2 = QuestionMetadata(word_count=3, language="en")
        sim = QuestionSimilarityFeatures(word_overlap_ratio=0.5)
        ca = ComplexityAnalysis(overall_complexity_score=0.3)
        ra = RelationshipAnalysis()
        d1 = engine.decide(
            "A", "B", metadata_1=m1, metadata_2=m2, similarity=sim, complexity_analysis=ca, relationship_analysis=ra
        )
        d2 = engine.decide(
            "A", "B", metadata_1=m1, metadata_2=m2, similarity=sim, complexity_analysis=ca, relationship_analysis=ra
        )
        assert d1.selected_strategy == d2.selected_strategy
        assert d1.confidence == d2.confidence

    def test_regression_entity_count_high(self):
        engine = RouterEngine()
        from ares.query_understanding.entity_models import Entity

        entities = [Entity(text=f"T{i}", entity_type="TYPE", start=0, end=1) for i in range(8)]
        er = EntityResult(entities_1=entities, entities_2=entities)
        ca = ComplexityAnalysis(entity_density=0.5, overall_complexity_score=0.3)
        d1 = engine.decide("A", "B", entity_analysis=er, complexity_analysis=ca)
        d2 = engine.decide("A", "B", entity_analysis=er, complexity_analysis=ca)
        assert d1.selected_strategy == d2.selected_strategy
        assert d1.selected_strategy == STRATEGY_CROSS_ENCODER


# ============================================================
# Serialization
# ============================================================
class TestSerialization:
    def test_routing_decision_to_dict_full(self):
        d = RoutingDecision(
            selected_strategy=STRATEGY_CROSS_ENCODER,
            confidence=0.85,
            priority=PRIORITY_HIGH,
            reason_codes=["negation_detected"],
            triggered_rules=[{"rule": "negation_conflict", "score": 0.9}],
            risk_level=RISK_MEDIUM,
            estimated_cost=0.5,
            estimated_latency=10.0,
            explanation="Test",
            processing_time=0.5,
            version="1.0.0",
        )
        result = d.to_dict()
        assert result["selected_strategy"] == STRATEGY_CROSS_ENCODER
        assert result["confidence"] == 0.85
        assert result["priority"] == PRIORITY_HIGH
        assert result["reason_codes"] == ["negation_detected"]
        assert result["triggered_rules"] == [{"rule": "negation_conflict", "score": 0.9}]
        assert result["risk_level"] == RISK_MEDIUM
        assert result["estimated_cost"] == 0.5
        assert result["estimated_latency"] == 10.0
        assert result["explanation"] == "Test"
        assert result["processing_time"] == 0.5

    def test_routing_decision_from_dict_full(self):
        data = {
            "selected_strategy": STRATEGY_ENSEMBLE,
            "confidence": 0.9,
            "priority": PRIORITY_HIGH,
            "reason_codes": ["high_ambiguity", "high_risk"],
            "triggered_rules": [{"rule": "high_ambiguity", "score": 0.85}],
            "risk_level": RISK_HIGH,
            "estimated_cost": 1.0,
            "estimated_latency": 25.0,
            "explanation": "Ensemble needed",
            "processing_time": 0.3,
            "version": "1.0.0",
        }
        d = RoutingDecision.from_dict(data)
        assert d.selected_strategy == STRATEGY_ENSEMBLE
        assert d.confidence == 0.9
        assert len(d.reason_codes) == 2
        assert len(d.triggered_rules) == 1

    def test_routing_decision_json(self):
        import json

        d = RoutingDecision(selected_strategy=STRATEGY_FAST_LEXICAL, confidence=0.7)
        s = json.dumps(d.to_dict())
        parsed = json.loads(s)
        assert parsed["selected_strategy"] == STRATEGY_FAST_LEXICAL
        assert parsed["confidence"] == 0.7
