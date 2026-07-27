from __future__ import annotations

import json

from ares.query_understanding.complexity_models import ComplexityAnalysis
from ares.query_understanding.decision_trace_builder import DecisionTraceBuilder
from ares.query_understanding.decision_trace_models import (
    ComplexityTrace,
    ConfidenceBreakdown,
    DecisionPath,
    DecisionTrace,
    EntityTrace,
    EvidenceDetail,
    QuestionTypeTrace,
    RelationshipTrace,
    RoutingTrace,
)
from ares.query_understanding.decision_trace_renderer import DecisionTraceRenderer
from ares.query_understanding.decision_trace_report import DecisionTraceReport
from ares.query_understanding.entity_models import (
    Entity,
    EntityPairMatch,
    EntityResult,
)
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.relationship_models import (
    Evidence,
    RelationshipAnalysis,
    RelationshipInfo,
)
from ares.query_understanding.router_models import RoutingDecision
from ares.query_understanding.type_models import QuestionTypeResult

# ============================================================
# Decision Trace Models — Unit Tests
# ============================================================


class TestEvidenceDetail:
    def test_defaults(self):
        ed = EvidenceDetail()
        assert ed.rule_name == ""
        assert ed.rule_layer == 0
        assert ed.matched_pattern == ""
        assert ed.evidence_tokens == []
        assert ed.confidence == 0.0
        assert ed.explanation == ""
        assert ed.affected_words == []
        assert ed.processing_layer == ""

    def test_all_fields(self):
        ed = EvidenceDetail(
            rule_name="test_rule",
            rule_layer=3,
            matched_pattern="pattern_found",
            evidence_tokens=["token1", "token2"],
            confidence=0.85,
            explanation="Test explanation",
            affected_words=["word1"],
            processing_layer="relationship",
        )
        assert ed.rule_name == "test_rule"
        assert ed.rule_layer == 3
        assert ed.matched_pattern == "pattern_found"
        assert ed.evidence_tokens == ["token1", "token2"]
        assert ed.confidence == 0.85
        assert ed.explanation == "Test explanation"
        assert ed.affected_words == ["word1"]
        assert ed.processing_layer == "relationship"

    def test_empty_tokens(self):
        ed = EvidenceDetail(evidence_tokens=[], affected_words=[])
        assert ed.evidence_tokens == []
        assert ed.affected_words == []

    def test_confidence_zero(self):
        ed = EvidenceDetail(confidence=0.0)
        assert ed.confidence == 0.0

    def test_confidence_one(self):
        ed = EvidenceDetail(confidence=1.0)
        assert ed.confidence == 1.0


class TestQuestionTypeTrace:
    def test_defaults(self):
        qt = QuestionTypeTrace()
        assert qt.question_1_type == ""
        assert qt.question_2_type == ""
        assert qt.pair_type == ""
        assert qt.confidence == 0.0
        assert qt.reason == ""
        assert qt.evidence == []
        assert qt.rules_fired == []

    def test_all_fields(self):
        ev = EvidenceDetail(rule_name="classify_q1", rule_layer=1, matched_pattern="how")
        qt = QuestionTypeTrace(
            question_1_type="how",
            question_2_type="how",
            pair_type="potential_paraphrase",
            confidence=0.92,
            reason="high_overlap",
            evidence=[ev],
            rules_fired=["classify_q1:how", "classify_q2:how"],
        )
        assert qt.question_1_type == "how"
        assert qt.pair_type == "potential_paraphrase"
        assert qt.confidence == 0.92
        assert len(qt.evidence) == 1

    def test_empty_reason(self):
        qt = QuestionTypeTrace(reason="")
        assert qt.reason == ""


class TestEntityTrace:
    def test_defaults(self):
        et = EntityTrace()
        assert et.entity_count_q1 == 0
        assert et.entity_count_q2 == 0
        assert et.shared_count == 0
        assert et.overlap_score == 0.0
        assert et.entity_relationship == ""
        assert et.confidence == 0.0
        assert et.evidence == []
        assert et.rules_fired == []

    def test_with_entities(self):
        ev = EvidenceDetail(rule_name="extract_entity", rule_layer=2)
        et = EntityTrace(
            entity_count_q1=2,
            entity_count_q2=1,
            shared_count=1,
            overlap_score=0.75,
            entity_relationship="overlapping",
            confidence=0.85,
            evidence=[ev],
            rules_fired=["entity_detected_q1:Python"],
        )
        assert et.entity_count_q1 == 2
        assert et.overlap_score == 0.75
        assert et.entity_relationship == "overlapping"

    def test_no_entities(self):
        et = EntityTrace(entity_relationship="no_entities", confidence=1.0)
        assert et.entity_relationship == "no_entities"


class TestRelationshipTrace:
    def test_defaults(self):
        rt = RelationshipTrace()
        assert rt.relationship_count == 0
        assert rt.primary_relationship == ""
        assert rt.relationship_score == 0.0
        assert rt.confidence == 0.0
        assert rt.semantic_flags == []
        assert rt.risk_flags == []

    def test_with_relationships(self):
        rt = RelationshipTrace(
            relationship_count=3,
            primary_relationship="exact_match",
            relationship_score=95.0,
            confidence=0.98,
            semantic_flags=["equivalent_intent"],
            risk_flags=[],
        )
        assert rt.primary_relationship == "exact_match"
        assert rt.relationship_score == 95.0

    def test_with_risk_flags(self):
        rt = RelationshipTrace(risk_flags=["meaning_changed", "entity_conflict"])
        assert len(rt.risk_flags) == 2
        assert "meaning_changed" in rt.risk_flags


class TestComplexityTrace:
    def test_defaults(self):
        ct = ComplexityTrace()
        assert ct.overall_score == 0.0
        assert ct.difficulty_level == ""
        assert ct.lexical == 0.0
        assert ct.syntactic == 0.0
        assert ct.semantic == 0.0
        assert ct.entity_complexity == 0.0
        assert ct.ambiguity == 0.0
        assert ct.readability == 0.0
        assert ct.comparison_difficulty == 0.0
        assert ct.confidence == 0.0
        assert ct.risk_score == 0.0
        assert ct.reasoning == ""

    def test_high_complexity(self):
        ct = ComplexityTrace(
            overall_score=0.85,
            difficulty_level="Hard",
            lexical=0.7,
            syntactic=0.6,
            semantic=0.8,
            entity_complexity=0.5,
            ambiguity=0.4,
            readability=0.6,
            comparison_difficulty=0.7,
            confidence=0.4,
            risk_score=0.6,
            reasoning="Complex comparison",
        )
        assert ct.overall_score == 0.85
        assert ct.difficulty_level == "Hard"
        assert ct.confidence == 0.4

    def test_very_easy(self):
        ct = ComplexityTrace(
            overall_score=0.05,
            difficulty_level="Very Easy",
            confidence=0.95,
            risk_score=0.01,
        )
        assert ct.difficulty_level == "Very Easy"


class TestRoutingTrace:
    def test_defaults(self):
        rt = RoutingTrace()
        assert rt.selected_strategy == ""
        assert rt.confidence == 0.0
        assert rt.risk_level == ""
        assert rt.priority == ""
        assert rt.strategy_scores == {}
        assert rt.triggered_rules == []
        assert rt.rejected_rules == []
        assert rt.reason_codes == []

    def test_with_strategy(self):
        rt = RoutingTrace(
            selected_strategy="cross_encoder",
            confidence=0.85,
            risk_level="medium",
            priority="high",
            strategy_scores={"cross_encoder": 0.85, "fast_lexical": 0.0},
            triggered_rules=[{"rule": "entity_dense", "score": 0.85}],
            rejected_rules=["fast_lexical", "baseline"],
            reason_codes=["entity_dense", "entity_conflict"],
        )
        assert rt.selected_strategy == "cross_encoder"
        assert rt.strategy_scores["cross_encoder"] == 0.85
        assert len(rt.rejected_rules) == 2

    def test_fallback(self):
        rt = RoutingTrace(
            selected_strategy="fallback",
            confidence=0.0,
            risk_level="high",
            priority="normal",
        )
        assert rt.selected_strategy == "fallback"

    def test_empty_strategy_scores(self):
        rt = RoutingTrace(strategy_scores={})
        assert rt.strategy_scores == {}


class TestConfidenceBreakdown:
    def test_defaults(self):
        cb = ConfidenceBreakdown()
        assert cb.question_type == 0.0
        assert cb.entity == 0.0
        assert cb.relationship == 0.0
        assert cb.complexity == 0.0
        assert cb.routing == 0.0
        assert cb.overall == 0.0

    def test_all_high(self):
        cb = ConfidenceBreakdown(
            question_type=0.95,
            entity=0.90,
            relationship=0.88,
            complexity=0.85,
            routing=0.92,
            overall=0.91,
        )
        assert cb.question_type == 0.95
        assert cb.overall == 0.91

    def test_all_low(self):
        cb = ConfidenceBreakdown(
            question_type=0.1,
            entity=0.2,
            relationship=0.15,
            complexity=0.3,
            routing=0.25,
            overall=0.2,
        )
        assert cb.overall == 0.2


class TestDecisionPath:
    def test_defaults(self):
        dp = DecisionPath()
        assert dp.layers_traversed == []
        assert dp.current_layer == ""
        assert dp.decision_flow == []

    def test_with_layers(self):
        dp = DecisionPath(
            layers_traversed=["question_type", "entity", "relationship", "complexity", "routing"],
            current_layer="routing",
            decision_flow=[
                "Classified pair as potential_paraphrase",
                "Found 2 entities",
                "Primary relationship: exact_match",
            ],
        )
        assert len(dp.layers_traversed) == 5
        assert dp.current_layer == "routing"
        assert len(dp.decision_flow) == 3


# ============================================================
# DecisionTrace — Serialization Tests
# ============================================================


class TestDecisionTraceSerialization:
    def test_default_trace(self):
        dt = DecisionTrace()
        assert dt.pipeline_version == "1.4.0"
        assert dt.processing_time_ms == 0.0
        assert dt.summary == ""
        assert dt.confidence == 0.0

    def test_to_dict_roundtrip(self):
        dt = DecisionTrace(
            summary="Test summary",
            confidence=0.85,
            overall_risk="low",
            overall_complexity="Easy",
            triggered_rules=["rule1"],
            rejected_rules=["strategy:fallback"],
            warnings=["High ambiguity"],
            recommendations=["Use ensemble"],
        )
        d = dt.to_dict()
        assert d["summary"] == "Test summary"
        assert d["confidence"] == 0.85
        assert d["overall_risk"] == "low"
        assert d["triggered_rules"] == ["rule1"]
        assert d["warnings"] == ["High ambiguity"]

    def test_from_dict_empty(self):
        dt = DecisionTrace.from_dict({})
        assert dt.pipeline_version == "1.4.0"
        assert dt.confidence == 0.0

    def test_from_dict_full(self):
        d = {
            "pipeline_version": "1.4.0",
            "processing_time_ms": 1.23,
            "summary": "Test",
            "confidence": 0.9,
            "overall_risk": "low",
            "overall_complexity": "Easy",
            "question_type_trace": {
                "question_1_type": "how",
                "question_2_type": "how",
                "pair_type": "potential_paraphrase",
                "confidence": 0.95,
                "reason": "high_overlap",
                "evidence": [],
                "rules_fired": ["classify_q1:how"],
            },
            "entity_trace": {
                "entity_count_q1": 1,
                "entity_count_q2": 1,
                "shared_count": 0,
                "overlap_score": 0.0,
                "entity_relationship": "different_entities",
                "confidence": 0.8,
                "evidence": [],
                "rules_fired": [],
            },
            "relationship_trace": {
                "relationship_count": 1,
                "primary_relationship": "exact_match",
                "relationship_score": 100.0,
                "confidence": 1.0,
                "semantic_flags": [],
                "risk_flags": [],
                "evidence": [],
                "rules_fired": [],
            },
            "complexity_trace": {
                "overall_score": 0.1,
                "difficulty_level": "Very Easy",
                "lexical": 0.0,
                "syntactic": 0.0,
                "semantic": 0.0,
                "entity_complexity": 0.0,
                "ambiguity": 0.0,
                "readability": 0.0,
                "comparison_difficulty": 0.0,
                "confidence": 0.95,
                "risk_score": 0.0,
                "reasoning": "Very simple",
                "evidence": [],
                "rules_fired": [],
            },
            "routing_trace": {
                "selected_strategy": "fast_lexical",
                "confidence": 1.0,
                "risk_level": "low",
                "priority": "low",
                "strategy_scores": {"fast_lexical": 1.0},
                "triggered_rules": [{"rule": "exact_match_simple", "score": 1.0}],
                "rejected_rules": ["cross_encoder"],
                "reason_codes": ["exact_match"],
                "evidence": [],
            },
            "triggered_rules": ["classify_q1:how"],
            "rejected_rules": [],
            "supporting_evidence": [],
            "confidence_breakdown": {
                "question_type": 0.95,
                "entity": 0.8,
                "relationship": 1.0,
                "complexity": 0.95,
                "routing": 1.0,
                "overall": 0.85,
            },
            "decision_path": {
                "layers_traversed": ["question_type", "entity", "relationship", "complexity", "routing"],
                "current_layer": "routing",
                "decision_flow": [],
            },
            "warnings": [],
            "recommendations": [],
            "metadata": {},
            "version": "1.4.0",
        }
        dt = DecisionTrace.from_dict(d)
        assert dt.summary == "Test"
        assert dt.confidence == 0.9
        assert dt.question_type_trace.question_1_type == "how"
        assert dt.entity_trace.entity_count_q1 == 1
        assert dt.relationship_trace.primary_relationship == "exact_match"
        assert dt.complexity_trace.difficulty_level == "Very Easy"
        assert dt.routing_trace.selected_strategy == "fast_lexical"
        assert dt.confidence_breakdown.overall == 0.85

    def test_json_roundtrip(self):
        dt = DecisionTrace(summary="JSON test", confidence=0.75)
        d = dt.to_dict()
        json_str = json.dumps(d)
        restored_dict = json.loads(json_str)
        restored = DecisionTrace.from_dict(restored_dict)
        assert restored.summary == "JSON test"
        assert restored.confidence == 0.75

    def test_trace_immutable_fields(self):
        dt = DecisionTrace(summary="Original")
        d = dt.to_dict()
        d["summary"] = "Modified"
        assert dt.summary == "Original"

    def test_with_evidence(self):
        ev = EvidenceDetail(rule_name="test_rule", confidence=0.9)
        dt = DecisionTrace(supporting_evidence=[ev])
        d = dt.to_dict()
        assert len(d["supporting_evidence"]) == 1
        assert d["supporting_evidence"][0]["rule_name"] == "test_rule"


# ============================================================
# DecisionTraceBuilder — Unit Tests
# ============================================================


class TestDecisionTraceBuilderQuestionType:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_with_none_question_type(self):
        trace = self.builder._build_question_type_trace(None)
        assert trace.confidence == 0.0
        assert trace.reason == "no_question_type_data"

    def test_with_question_type(self):
        qt = QuestionTypeResult(
            question_1_type="how",
            question_2_type="how",
            pair_type="potential_paraphrase",
            classification_confidence=0.95,
            classification_reason="q1:how | q2:how | pair:potential_paraphrase:high_overlap",
        )
        trace = self.builder._build_question_type_trace(qt)
        assert trace.question_1_type == "how"
        assert trace.pair_type == "potential_paraphrase"
        assert trace.confidence == 0.95
        assert len(trace.rules_fired) >= 2

    def test_unknown_question_type(self):
        qt = QuestionTypeResult(
            pair_type="unknown",
            classification_reason="both_inputs_empty",
        )
        trace = self.builder._build_question_type_trace(qt)
        assert trace.pair_type == "unknown"

    def test_question_type_evidence(self):
        qt = QuestionTypeResult(
            pair_type="potential_paraphrase",
            classification_confidence=0.8,
            classification_reason="test_reason",
        )
        trace = self.builder._build_question_type_trace(qt)
        assert len(trace.evidence) == 1
        assert trace.evidence[0].rule_name == "question_type_classification"

    def test_different_types(self):
        qt = QuestionTypeResult(
            question_1_type="how",
            question_2_type="what",
            pair_type="complementary",
        )
        trace = self.builder._build_question_type_trace(qt)
        assert trace.question_1_type == "how"
        assert trace.question_2_type == "what"
        assert trace.pair_type == "complementary"


class TestDecisionTraceBuilderEntity:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_with_none_entity(self):
        trace = self.builder._build_entity_trace(None)
        assert trace.entity_relationship == "no_entities"
        assert trace.confidence == 1.0

    def test_no_entities(self):
        er = EntityResult(entity_relationship="no_entities")
        trace = self.builder._build_entity_trace(er)
        assert trace.entity_count_q1 == 0
        assert trace.entity_count_q2 == 0

    def test_with_entities(self):
        e1 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", confidence=1.0, start=0, end=6)
        e2 = Entity(text="Java", entity_type="PROGRAMMING_LANGUAGE", confidence=1.0, start=0, end=4)
        match = EntityPairMatch(
            entity_1=e1,
            entity_2=e2,
            match_type="different_entities",
            similarity=0.0,
        )
        er = EntityResult(
            entities_1=[e1],
            entities_2=[e2],
            shared_entities=[match],
            entity_overlap_score=0.5,
            entity_relationship="different_entities",
        )
        trace = self.builder._build_entity_trace(er)
        assert trace.entity_count_q1 == 1
        assert trace.entity_count_q2 == 1
        assert trace.overlap_score == 0.5
        assert len(trace.evidence) >= 2

    def test_shared_entities(self):
        e1 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", confidence=1.0, start=0, end=6)
        e2 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", confidence=1.0, start=0, end=6)
        match = EntityPairMatch(entity_1=e1, entity_2=e2, match_type="exact_match", similarity=1.0)
        er = EntityResult(
            entities_1=[e1],
            entities_2=[e2],
            shared_entities=[match],
            entity_overlap_score=1.0,
            entity_relationship="same_entity",
        )
        trace = self.builder._build_entity_trace(er)
        assert trace.shared_count == 1
        assert trace.overlap_score == 1.0

    def test_entity_evidence_details(self):
        e = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", confidence=0.95, start=0, end=6)
        er = EntityResult(entities_1=[e], entity_relationship="no_entities")
        trace = self.builder._build_entity_trace(er)
        assert len(trace.evidence) >= 1
        ev = trace.evidence[0]
        assert "Python" in ev.evidence_tokens
        assert ev.processing_layer == "entity"


class TestDecisionTraceBuilderRelationship:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_with_none_relationship(self):
        trace = self.builder._build_relationship_trace(None)
        assert trace.confidence == 0.0

    def test_with_relationships(self):
        ev = Evidence(
            rule_name="exact_match",
            rule_layer=2,
            matched_pattern="normalized_text_identical",
            tokens_q1=["hello"],
            tokens_q2=["hello"],
            confidence=1.0,
        )
        rel = RelationshipInfo(
            relationship_type="exact_match",
            confidence=1.0,
            evidence=[ev],
            human_explanation="Both questions are identical",
        )
        ra = RelationshipAnalysis(
            relationship_types=[rel],
            relationship_score=100.0,
            relationship_confidence=1.0,
        )
        trace = self.builder._build_relationship_trace(ra)
        assert trace.primary_relationship == "exact_match"
        assert trace.relationship_score == 100.0
        assert trace.confidence == 1.0
        assert len(trace.evidence) >= 1

    def test_with_semantic_flags(self):
        ra = RelationshipAnalysis(
            semantic_flags=["equivalent_intent", "same_entity"],
            risk_flags=[],
        )
        trace = self.builder._build_relationship_trace(ra)
        assert "equivalent_intent" in trace.semantic_flags

    def test_with_risk_flags(self):
        ra = RelationshipAnalysis(
            risk_flags=["meaning_changed", "entity_conflict"],
        )
        trace = self.builder._build_relationship_trace(ra)
        assert "meaning_changed" in trace.risk_flags

    def test_multiple_relationships(self):
        rels = [
            RelationshipInfo(relationship_type="word_order_change", confidence=0.8),
            RelationshipInfo(relationship_type="synonym_replacement", confidence=0.75),
        ]
        ra = RelationshipAnalysis(
            relationship_types=rels,
            relationship_score=80.0,
            relationship_confidence=0.8,
        )
        trace = self.builder._build_relationship_trace(ra)
        assert trace.relationship_count == 2
        assert len(trace.rules_fired) == 2

    def test_evidence_layer_numbers(self):
        ev = Evidence(rule_name="test", rule_layer=3, matched_pattern="test", confidence=0.9)
        rel = RelationshipInfo(relationship_type="test_rel", confidence=0.9, evidence=[ev])
        ra = RelationshipAnalysis(relationship_types=[rel])
        trace = self.builder._build_relationship_trace(ra)
        assert trace.evidence[0].rule_layer == 3


class TestDecisionTraceBuilderComplexity:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_with_none_complexity(self):
        trace = self.builder._build_complexity_trace(None)
        assert trace.confidence == 0.0

    def test_with_complexity(self):
        ca = ComplexityAnalysis(
            overall_complexity_score=0.25,
            difficulty_level="Easy",
            lexical_complexity=0.1,
            syntactic_complexity=0.05,
            semantic_complexity=0.15,
            entity_complexity=0.0,
            ambiguity_score=0.1,
            readability_score=0.2,
            comparison_difficulty=0.1,
            confidence_estimate=0.9,
            risk_score=0.05,
            reasoning_summary="Moderately simple comparison",
        )
        trace = self.builder._build_complexity_trace(ca)
        assert trace.overall_score == 0.25
        assert trace.difficulty_level == "Easy"
        assert trace.lexical == 0.1
        assert trace.syntactic == 0.05
        assert trace.semantic == 0.15
        assert trace.confidence == 0.9
        assert trace.reasoning == "Moderately simple comparison"

    def test_high_complexity_trace(self):
        ca = ComplexityAnalysis(
            overall_complexity_score=0.85,
            difficulty_level="Very Hard",
            lexical_complexity=0.8,
            syntactic_complexity=0.7,
            semantic_complexity=0.9,
            entity_complexity=0.6,
            ambiguity_score=0.7,
            readability_score=0.8,
            comparison_difficulty=0.9,
            confidence_estimate=0.3,
            risk_score=0.8,
        )
        trace = self.builder._build_complexity_trace(ca)
        assert trace.overall_score == 0.85
        assert trace.difficulty_level == "Very Hard"
        assert trace.risk_score == 0.8

    def test_complexity_metrics_generate_evidence(self):
        ca = ComplexityAnalysis(
            overall_complexity_score=0.5,
            lexical_complexity=0.3,
            syntactic_complexity=0.0,
        )
        trace = self.builder._build_complexity_trace(ca)
        assert len(trace.evidence) >= 1
        has_lexical = any("lexical_complexity" in e.rule_name for e in trace.evidence)
        assert has_lexical

    def test_zero_complexity_trace(self):
        ca = ComplexityAnalysis()
        trace = self.builder._build_complexity_trace(ca)
        assert trace.overall_score == 0.0
        assert len(trace.evidence) == 0


class TestDecisionTraceBuilderRouting:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_with_none_routing(self):
        trace = self.builder._build_routing_trace(None)
        assert trace.confidence == 0.0

    def test_with_routing_decision(self):
        rd = RoutingDecision(
            selected_strategy="fast_lexical",
            confidence=1.0,
            priority="low",
            risk_level="low",
            reason_codes=["exact_match"],
            triggered_rules=[
                {
                    "rule": "exact_match_simple",
                    "description": "Exact match",
                    "category": "fast_path",
                    "score": 1.0,
                    "weight": 1.0,
                }
            ],
        )
        trace = self.builder._build_routing_trace(rd)
        assert trace.selected_strategy == "fast_lexical"
        assert trace.confidence == 1.0
        assert trace.risk_level == "low"
        assert len(trace.triggered_rules) == 1

    def test_cross_encoder_routing(self):
        rd = RoutingDecision(
            selected_strategy="cross_encoder",
            confidence=0.85,
            risk_level="medium",
            priority="high",
            triggered_rules=[
                {
                    "rule": "entity_dense",
                    "description": "Entity dense",
                    "category": "cross_encoder",
                    "score": 0.85,
                    "weight": 0.85,
                }
            ],
        )
        trace = self.builder._build_routing_trace(rd)
        assert trace.selected_strategy == "cross_encoder"
        assert "cross_encoder" in trace.strategy_scores

    def test_rejected_strategies(self):
        rd = RoutingDecision(
            selected_strategy="cross_encoder",
            triggered_rules=[],
        )
        trace = self.builder._build_routing_trace(rd)
        assert len(trace.rejected_rules) > 0
        assert "fallback" in trace.rejected_rules or "fast_lexical" in trace.rejected_rules

    def test_routing_evidence(self):
        rd = RoutingDecision(
            selected_strategy="fast_lexical",
            triggered_rules=[
                {
                    "rule": "exact_match_simple",
                    "description": "Exact match",
                    "category": "fast_path",
                    "score": 1.0,
                    "weight": 1.0,
                }
            ],
        )
        trace = self.builder._build_routing_trace(rd)
        assert len(trace.evidence) >= 1


class TestDecisionTraceBuilderConfidence:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_empty_analysis(self):
        analysis = QueryAnalysis()
        cb = self.builder._build_confidence_breakdown(analysis)
        assert cb.question_type == 0.0
        assert cb.entity == 1.0
        assert cb.relationship == 0.0
        assert cb.complexity == 1.0
        assert cb.routing == 0.0

    def test_with_all_data(self):
        analysis = QueryAnalysis(
            question_type=QuestionTypeResult(classification_confidence=0.9),
            entity_analysis=EntityResult(entity_overlap_score=0.8, entity_relationship="same_entity"),
            relationship_analysis=RelationshipAnalysis(relationship_confidence=0.85),
            complexity_analysis=ComplexityAnalysis(confidence_estimate=0.88),
            routing_decision=RoutingDecision(confidence=0.95),
        )
        cb = self.builder._build_confidence_breakdown(analysis)
        assert cb.question_type == 0.9
        assert cb.entity == 0.8
        assert cb.relationship == 0.85
        assert cb.complexity == 0.88
        assert cb.routing == 0.95
        assert 0 < cb.overall < 1.0

    def test_overall_weighted(self):
        analysis = QueryAnalysis(
            question_type=QuestionTypeResult(classification_confidence=1.0),
            entity_analysis=EntityResult(entity_overlap_score=1.0, entity_relationship="same_entity"),
            relationship_analysis=RelationshipAnalysis(relationship_confidence=1.0),
            complexity_analysis=ComplexityAnalysis(confidence_estimate=1.0),
            routing_decision=RoutingDecision(confidence=1.0),
        )
        cb = self.builder._build_confidence_breakdown(analysis)
        assert cb.overall == 1.0

    def test_overall_low(self):
        analysis = QueryAnalysis(
            question_type=QuestionTypeResult(classification_confidence=0.0),
            entity_analysis=EntityResult(entity_overlap_score=0.0, entity_relationship="no_entities"),
            relationship_analysis=RelationshipAnalysis(relationship_confidence=0.0),
            complexity_analysis=ComplexityAnalysis(confidence_estimate=0.0),
            routing_decision=RoutingDecision(confidence=0.0),
        )
        cb = self.builder._build_confidence_breakdown(analysis)
        expected = 0.0 * 0.1 + 1.0 * 0.15 + 0.0 * 0.2 + 0.0 * 0.2 + 0.0 * 0.35
        assert cb.overall == expected


class TestDecisionTraceBuilderDecisionPath:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_empty_analysis_path(self):
        analysis = QueryAnalysis()
        dp = self.builder._build_decision_path(analysis)
        assert dp.layers_traversed == ["question_type", "entity", "relationship", "complexity", "routing"]
        assert dp.current_layer == "routing"

    def test_with_data_path(self):
        analysis = QueryAnalysis(
            question_type=QuestionTypeResult(pair_type="potential_paraphrase"),
            entity_analysis=EntityResult(
                entities_1=[Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", confidence=1.0, start=0, end=6)],
                entity_relationship="no_entities",
            ),
            relationship_analysis=RelationshipAnalysis(
                relationship_types=[RelationshipInfo(relationship_type="exact_match", confidence=1.0)]
            ),
            complexity_analysis=ComplexityAnalysis(overall_complexity_score=0.1, difficulty_level="Very Easy"),
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )
        dp = self.builder._build_decision_path(analysis)
        assert len(dp.decision_flow) >= 4


class TestDecisionTraceBuilderSummary:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_empty_summary(self):
        analysis = QueryAnalysis()
        rout = RoutingTrace()
        s = self.builder._build_summary(analysis, rout)
        assert "Pair type" in s or "No analysis" in s

    def test_with_data(self):
        analysis = QueryAnalysis(
            question_type=QuestionTypeResult(pair_type="potential_paraphrase"),
            relationship_analysis=RelationshipAnalysis(
                relationship_types=[RelationshipInfo(relationship_type="exact_match", confidence=1.0)]
            ),
            complexity_analysis=ComplexityAnalysis(difficulty_level="Very Easy"),
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )
        rout = RoutingTrace(selected_strategy="fast_lexical")
        s = self.builder._build_summary(analysis, rout)
        assert "potential_paraphrase" in s
        assert "Very Easy" in s
        assert "fast_lexical" in s


class TestDecisionTraceBuilderWarnings:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_no_warnings(self):
        analysis = QueryAnalysis()
        w = self.builder._collect_warnings(analysis)
        assert w == []

    def test_risk_flags_warning(self):
        analysis = QueryAnalysis(
            relationship_analysis=RelationshipAnalysis(risk_flags=["meaning_changed", "entity_conflict"])
        )
        w = self.builder._collect_warnings(analysis)
        assert len(w) == 2
        assert any("meaning_changed" in x for x in w)

    def test_high_ambiguity_warning(self):
        analysis = QueryAnalysis(complexity_analysis=ComplexityAnalysis(ambiguity_score=0.6))
        w = self.builder._collect_warnings(analysis)
        assert any("ambiguity" in x.lower() for x in w)

    def test_high_complexity_warning(self):
        analysis = QueryAnalysis(complexity_analysis=ComplexityAnalysis(overall_complexity_score=0.8))
        w = self.builder._collect_warnings(analysis)
        assert "Very high complexity" in w


class TestDecisionTraceBuilderRecommendations:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_no_recommendations(self):
        analysis = QueryAnalysis(routing_decision=RoutingDecision(selected_strategy="cross_encoder"))
        r = self.builder._collect_recommendations(analysis)
        assert len(r) >= 1

    def test_cross_encoder_recommendation(self):
        analysis = QueryAnalysis(routing_decision=RoutingDecision(selected_strategy="cross_encoder"))
        r = self.builder._collect_recommendations(analysis)
        assert "ensemble" in r[0].lower()

    def test_fast_lexical_recommendation(self):
        analysis = QueryAnalysis(routing_decision=RoutingDecision(selected_strategy="fast_lexical"))
        r = self.builder._collect_recommendations(analysis)
        assert any("Simple" in x or "fast" in x for x in r)

    def test_fallback_recommendation(self):
        analysis = QueryAnalysis(routing_decision=RoutingDecision(selected_strategy="fallback"))
        r = self.builder._collect_recommendations(analysis)
        assert any("review" in x.lower() for x in r)

    def test_high_complexity_recommendation(self):
        analysis = QueryAnalysis(complexity_analysis=ComplexityAnalysis(overall_complexity_score=0.6))
        r = self.builder._collect_recommendations(analysis)
        assert any("complex" in x.lower() for x in r)


# ============================================================
# DecisionTraceBuilder — Integration Tests
# ============================================================


class TestDecisionTraceBuilderIntegration:
    def setup_method(self):
        self.builder = DecisionTraceBuilder()

    def test_build_empty_analysis(self):
        analysis = QueryAnalysis()
        trace = self.builder.build(analysis)
        assert isinstance(trace, DecisionTrace)
        assert "Pair type" in trace.summary or "No analysis" in trace.summary

    def test_build_full_analysis(self):
        analysis = QueryAnalysis(
            original_question_1="How to install Python?",
            original_question_2="How to install Python?",
            normalized_question_1="how to install python",
            normalized_question_2="how to install python",
            question_type=QuestionTypeResult(
                question_1_type="how",
                question_2_type="how",
                pair_type="potential_paraphrase",
                classification_confidence=0.95,
            ),
            entity_analysis=EntityResult(
                entities_1=[
                    Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", confidence=1.0, start=14, end=20)
                ],
                entities_2=[
                    Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", confidence=1.0, start=14, end=20)
                ],
                shared_entities=[
                    EntityPairMatch(
                        entity_1=Entity(
                            text="Python", entity_type="PROGRAMMING_LANGUAGE", confidence=1.0, start=14, end=20
                        ),
                        entity_2=Entity(
                            text="Python", entity_type="PROGRAMMING_LANGUAGE", confidence=1.0, start=14, end=20
                        ),
                        match_type="exact_match",
                        similarity=1.0,
                    )
                ],
                entity_overlap_score=1.0,
                entity_relationship="same_entity",
            ),
            relationship_analysis=RelationshipAnalysis(
                relationship_types=[
                    RelationshipInfo(
                        relationship_type="exact_match",
                        confidence=1.0,
                        evidence=[
                            Evidence(rule_name="exact_match", rule_layer=2, matched_pattern="identical", confidence=1.0)
                        ],
                        human_explanation="Both questions are identical",
                    )
                ],
                relationship_score=100.0,
                relationship_confidence=1.0,
            ),
            complexity_analysis=ComplexityAnalysis(
                overall_complexity_score=0.1,
                difficulty_level="Very Easy",
                confidence_estimate=0.95,
                risk_score=0.01,
            ),
            routing_decision=RoutingDecision(
                selected_strategy="fast_lexical",
                confidence=1.0,
                risk_level="low",
                priority="low",
            ),
            processing_time_ms=5.0,
        )
        trace = self.builder.build(analysis)
        assert trace.summary != ""
        assert trace.confidence > 0
        assert trace.question_type_trace.pair_type == "potential_paraphrase"
        assert trace.entity_trace.entity_count_q1 == 1
        assert trace.relationship_trace.primary_relationship == "exact_match"
        assert trace.complexity_trace.difficulty_level == "Very Easy"
        assert trace.routing_trace.selected_strategy == "fast_lexical"

    def test_build_sets_metadata(self):
        analysis = QueryAnalysis(
            original_question_1="Q1",
            original_question_2="Q2",
            processing_time_ms=10.0,
        )
        trace = self.builder.build(analysis)
        assert trace.metadata["original_length_1"] == 2
        assert trace.metadata["has_both_inputs"] is True

    def test_build_with_warnings(self):
        analysis = QueryAnalysis(
            relationship_analysis=RelationshipAnalysis(risk_flags=["meaning_changed"]),
            complexity_analysis=ComplexityAnalysis(ambiguity_score=0.6),
        )
        trace = self.builder.build(analysis)
        assert len(trace.warnings) >= 1

    def test_build_triggered_rules_collected(self):
        analysis = QueryAnalysis(
            question_type=QuestionTypeResult(
                question_1_type="how",
                pair_type="potential_paraphrase",
                classification_confidence=0.9,
            ),
            entity_analysis=EntityResult(
                entities_1=[Entity(text="Test", entity_type="OTHER", confidence=0.5, start=0, end=4)],
            ),
        )
        trace = self.builder.build(analysis)
        assert len(trace.triggered_rules) >= 2

    def test_build_supporting_evidence_collected(self):
        analysis = QueryAnalysis(
            question_type=QuestionTypeResult(
                pair_type="potential_paraphrase",
                classification_confidence=0.9,
            )
        )
        trace = self.builder.build(analysis)
        assert len(trace.supporting_evidence) >= 1

    def test_processing_time_positive(self):
        analysis = QueryAnalysis()
        trace = self.builder.build(analysis)
        assert trace.processing_time_ms >= 0


# ============================================================
# DecisionTraceRenderer — Unit Tests
# ============================================================


class TestDecisionTraceRendererPlainText:
    def setup_method(self):
        self.renderer = DecisionTraceRenderer()
        self.trace = DecisionTrace(
            pipeline_version="1.4.0",
            processing_time_ms=1.5,
            summary="Test trace",
            confidence=0.85,
            overall_risk="low",
            overall_complexity="Easy",
            question_type_trace=QuestionTypeTrace(
                question_1_type="how",
                question_2_type="how",
                pair_type="potential_paraphrase",
                confidence=0.95,
            ),
            routing_trace=RoutingTrace(
                selected_strategy="fast_lexical",
                confidence=1.0,
                risk_level="low",
                priority="low",
            ),
        )

    def test_render_contains_header(self):
        output = self.renderer.render_plaintext(self.trace)
        assert "DECISION TRACE" in output

    def test_render_contains_summary(self):
        output = self.renderer.render_plaintext(self.trace)
        assert "Test trace" in output

    def test_render_contains_confidence(self):
        output = self.renderer.render_plaintext(self.trace)
        assert "0.85" in output

    def test_render_contains_pipeline_version(self):
        output = self.renderer.render_plaintext(self.trace)
        assert "1.4.0" in output

    def test_render_contains_question_type(self):
        output = self.renderer.render_plaintext(self.trace)
        assert "QUESTION TYPE TRACE" in output
        assert "potential_paraphrase" in output

    def test_render_contains_routing(self):
        output = self.renderer.render_plaintext(self.trace)
        assert "ROUTING TRACE" in output
        assert "fast_lexical" in output

    def test_render_empty_trace(self):
        t = DecisionTrace()
        output = self.renderer.render_plaintext(t)
        assert "DECISION TRACE" in output

    def test_render_with_warnings(self):
        t = DecisionTrace(warnings=["Test warning"])
        output = self.renderer.render_plaintext(t)
        assert "WARNINGS" in output
        assert "Test warning" in output

    def test_render_with_recommendations(self):
        t = DecisionTrace(recommendations=["Test rec"])
        output = self.renderer.render_plaintext(t)
        assert "RECOMMENDATIONS" in output
        assert "Test rec" in output

    def test_render_with_triggered_rules(self):
        t = DecisionTrace(triggered_rules=["rule1", "rule2"])
        output = self.renderer.render_plaintext(t)
        assert "ALL TRIGGERED RULES" in output
        assert "rule1" in output


class TestDecisionTraceRendererMarkdown:
    def setup_method(self):
        self.renderer = DecisionTraceRenderer()
        self.trace = DecisionTrace(
            summary="MD Test",
            confidence=0.9,
        )

    def test_render_markdown_contains_header(self):
        output = self.renderer.render_markdown(self.trace)
        assert "# Decision Trace" in output

    def test_render_markdown_contains_summary(self):
        output = self.renderer.render_markdown(self.trace)
        assert "MD Test" in output

    def test_render_markdown_contains_tables(self):
        output = self.renderer.render_markdown(self.trace)
        assert "| Stage | Confidence |" in output
        assert "|-------|------------|" in output

    def test_render_markdown_contains_sections(self):
        output = self.renderer.render_markdown(self.trace)
        assert "## Decision Path" in output
        assert "## Question Type Trace" in output
        assert "## Entity Trace" in output
        assert "## Relationship Trace" in output
        assert "## Complexity Trace" in output
        assert "## Routing Trace" in output
        assert "## Confidence Breakdown" in output

    def test_render_markdown_with_warnings(self):
        t = DecisionTrace(warnings=["Warning!"])
        output = self.renderer.render_markdown(t)
        assert "## Warnings" in output
        assert "Warning!" in output

    def test_render_markdown_with_recommendations(self):
        t = DecisionTrace(recommendations=["Recommendation!"])
        output = self.renderer.render_markdown(t)
        assert "## Recommendations" in output


class TestDecisionTraceRendererJSON:
    def setup_method(self):
        self.renderer = DecisionTraceRenderer()

    def test_render_json_valid(self):
        t = DecisionTrace(summary="JSON test")
        output = self.renderer.render_json(t)
        data = json.loads(output)
        assert data["summary"] == "JSON test"

    def test_render_json_contains_confidence(self):
        t = DecisionTrace(confidence=0.75)
        output = self.renderer.render_json(t)
        data = json.loads(output)
        assert data["confidence"] == 0.75

    def test_render_json_pretty(self):
        t = DecisionTrace(summary="pretty")
        output = self.renderer.render_json(t)
        assert "\n" in output
        assert "  " in output


class TestDecisionTraceRendererDict:
    def setup_method(self):
        self.renderer = DecisionTraceRenderer()

    def test_render_dict(self):
        t = DecisionTrace(summary="dict test")
        d = self.renderer.render_dict(t)
        assert isinstance(d, dict)
        assert d["summary"] == "dict test"

    def test_render_dict_contains_nested(self):
        t = DecisionTrace(question_type_trace=QuestionTypeTrace(pair_type="paraphrase"))
        d = self.renderer.render_dict(t)
        assert "question_type_trace" in d
        assert d["question_type_trace"]["pair_type"] == "paraphrase"

    def test_render_dict_matches_to_dict(self):
        t = DecisionTrace(summary="match")
        d1 = self.renderer.render_dict(t)
        d2 = t.to_dict()
        assert d1 == d2


# ============================================================
# DecisionTraceReport — Test
# ============================================================


class TestDecisionTraceReport:
    def setup_method(self):
        self.report = DecisionTraceReport()
        self.trace = DecisionTrace(summary="Report test", confidence=0.8)

    def test_generate_human(self):
        output = self.report.generate_human(self.trace)
        assert "DECISION TRACE" in output

    def test_generate_developer(self):
        output = self.report.generate_developer(self.trace)
        data = json.loads(output)
        assert data["summary"] == "Report test"

    def test_generate_machine(self):
        d = self.report.generate_machine(self.trace)
        assert isinstance(d, dict)
        assert d["summary"] == "Report test"

    def test_generate_markdown(self):
        output = self.report.generate_markdown(self.trace)
        assert "# Decision Trace" in output


# ============================================================
# Pipeline Integration — QueryAnalysis contains decision_trace
# ============================================================


class TestQueryAnalysisDecisionTrace:
    def test_decision_trace_field_exists(self):
        analysis = QueryAnalysis()
        assert hasattr(analysis, "decision_trace")
        assert isinstance(analysis.decision_trace, DecisionTrace)

    def test_decision_trace_default(self):
        analysis = QueryAnalysis()
        assert analysis.decision_trace.summary == ""

    def test_decision_trace_in_to_dict(self):
        analysis = QueryAnalysis(original_question_1="Q1", original_question_2="Q2")
        d = analysis.to_dict()
        assert "decision_trace" in d

    def test_decision_trace_in_from_dict(self):
        d = {
            "original_question_1": "Q1",
            "original_question_2": "Q2",
            "decision_trace": {
                "summary": "From dict trace",
                "confidence": 0.9,
            },
        }
        analysis = QueryAnalysis.from_dict(d)
        assert analysis.decision_trace.summary == "From dict trace"
        assert analysis.decision_trace.confidence == 0.9

    def test_decision_trace_json_roundtrip(self):
        analysis = QueryAnalysis(
            original_question_1="Q1",
            original_question_2="Q2",
            decision_trace=DecisionTrace(summary="Roundtrip", confidence=0.85),
        )
        json_str = analysis.to_json()
        restored = QueryAnalysis.from_dict(json.loads(json_str))
        assert restored.decision_trace.summary == "Roundtrip"
        assert restored.decision_trace.confidence == 0.85


# ============================================================
# Evidence Detail — Utility Tests
# ============================================================


class TestEvidenceDetailEdgeCases:
    def test_long_explanation(self):
        ed = EvidenceDetail(explanation="x" * 1000)
        assert len(ed.explanation) == 1000

    def test_many_tokens(self):
        tokens = [f"token{i}" for i in range(100)]
        ed = EvidenceDetail(evidence_tokens=tokens)
        assert len(ed.evidence_tokens) == 100

    def test_special_chars_in_pattern(self):
        ed = EvidenceDetail(matched_pattern="test_pattern_123!@#")
        assert ed.matched_pattern == "test_pattern_123!@#"

    def test_unicode_in_explanation(self):
        ed = EvidenceDetail(explanation="café français 中文")
        assert "café" in ed.explanation


# ============================================================
# Integration with actual QueryAnalyzer
# ============================================================


class TestQueryAnalyzerDecisionTraceIntegration:
    def test_analyzer_adds_decision_trace(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("How to install Python?", "How to install Python?")
        assert result.decision_trace is not None
        assert isinstance(result.decision_trace, DecisionTrace)
        assert result.decision_trace.summary != ""

    def test_decision_trace_has_all_layers(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        dt = result.decision_trace
        assert dt.question_type_trace.pair_type != ""
        assert dt.entity_trace.entity_count_q1 >= 0
        assert dt.relationship_trace.primary_relationship != ""
        assert dt.complexity_trace.difficulty_level != ""
        assert dt.routing_trace.selected_strategy != ""

    def test_decision_trace_confidence_breakdown_present(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("A", "B")
        cb = result.decision_trace.confidence_breakdown
        assert cb.question_type >= 0
        assert cb.entity >= 0
        assert cb.relationship >= 0
        assert cb.complexity >= 0
        assert cb.routing >= 0

    def test_decision_trace_triggered_rules_non_empty(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("How to install Python?", "How to install Python?")
        assert len(result.decision_trace.triggered_rules) > 0

    def test_empty_input_still_has_trace(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("", "")
        assert result.decision_trace is not None
        assert isinstance(result.decision_trace, DecisionTrace)


# ============================================================
# Performance Tests
# ============================================================


class TestDecisionTracePerformance:
    def test_build_under_2ms(self):
        import time

        builder = DecisionTraceBuilder()
        analysis = QueryAnalysis(
            question_type=QuestionTypeResult(pair_type="test"),
            entity_analysis=EntityResult(
                entities_1=[Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", confidence=1.0, start=0, end=6)],
                entity_relationship="no_entities",
            ),
            relationship_analysis=RelationshipAnalysis(
                relationship_types=[RelationshipInfo(relationship_type="exact_match", confidence=1.0)]
            ),
            complexity_analysis=ComplexityAnalysis(overall_complexity_score=0.1, difficulty_level="Easy"),
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )
        start = time.time()
        for _ in range(100):
            builder.build(analysis)
        elapsed_ms = (time.time() - start) * 10
        assert elapsed_ms < 2.0

    def test_render_under_1ms(self):
        import time

        renderer = DecisionTraceRenderer()
        trace = DecisionTrace(
            summary="perf test",
            question_type_trace=QuestionTypeTrace(pair_type="test"),
            entity_trace=EntityTrace(entity_count_q1=3, entity_count_q2=2),
            relationship_trace=RelationshipTrace(primary_relationship="test", relationship_count=2),
            complexity_trace=ComplexityTrace(overall_score=0.5, difficulty_level="Medium"),
            routing_trace=RoutingTrace(selected_strategy="fast_lexical"),
        )
        start = time.time()
        for _ in range(100):
            renderer.render_plaintext(trace)
        elapsed_ms = (time.time() - start) * 10
        assert elapsed_ms < 1.0


# ============================================================
# Unicode and Edge Case Tests
# ============================================================


class TestDecisionTraceUnicode:
    def test_unicode_in_trace(self):
        trace = DecisionTrace(summary="中文测试 café ñoño")
        d = trace.to_dict()
        assert "中文" in d["summary"]
        assert "café" in d["summary"]

    def test_mixed_language_entities(self):
        builder = DecisionTraceBuilder()
        e = Entity(text="café", entity_type="OTHER", confidence=0.5, start=0, end=5)
        er = EntityResult(entities_1=[e])
        trace = builder._build_entity_trace(er)
        assert len(trace.evidence) > 0

    def test_emoji_not_breaking(self):
        trace = DecisionTrace(summary="Test with 😊 emoji")
        d = trace.to_dict()
        assert "😊" in d["summary"]


class TestDecisionTraceEdgeCases:
    def test_missing_entities(self):
        builder = DecisionTraceBuilder()
        er = EntityResult(entity_relationship="no_entities")
        trace = builder._build_entity_trace(er)
        assert trace.entity_count_q1 == 0
        assert trace.entity_count_q2 == 0

    def test_high_ambiguity_question(self):
        analysis = QueryAnalysis(
            complexity_analysis=ComplexityAnalysis(ambiguity_score=0.8, overall_complexity_score=0.3),
        )
        builder = DecisionTraceBuilder()
        trace = builder.build(analysis)
        assert any("ambiguity" in x.lower() for x in trace.warnings)

    def test_very_long_question(self):
        analysis = QueryAnalysis(
            original_question_1="x" * 10000,
            original_question_2="y" * 10000,
        )
        builder = DecisionTraceBuilder()
        trace = builder.build(analysis)
        assert trace.metadata["original_length_1"] == 10000

    def test_short_question(self):
        analysis = QueryAnalysis(original_question_1="A", original_question_2="B")
        builder = DecisionTraceBuilder()
        trace = builder.build(analysis)
        assert trace.metadata["original_length_1"] == 1

    def test_pipeline_version_constant(self):
        assert DecisionTrace().pipeline_version == "1.4.0"


# ============================================================
# Regression Tests — Verify backward compatibility
# ============================================================


class TestDecisionTraceRegression:
    def test_analysis_prediction_unchanged(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        r1 = analyzer.analyze("How to install Python?", "How to install Java?")
        r2 = analyzer.analyze("How to install Python?", "How to install Java?")
        assert r1.question_type.pair_type == r2.question_type.pair_type
        assert r1.entity_analysis.entity_relationship == r2.entity_analysis.entity_relationship
        assert r1.relationship_analysis.relationship_score == r2.relationship_analysis.relationship_score
        assert r1.complexity_analysis.overall_complexity_score == r2.complexity_analysis.overall_complexity_score
        assert r1.routing_decision.selected_strategy == r2.routing_decision.selected_strategy

    def test_router_unchanged_with_trace(self):
        from ares.query_understanding.router_engine import RouterEngine

        engine = RouterEngine()
        d1 = engine.decide(
            question_1="test",
            question_2="test",
        )
        d2 = engine.decide(
            question_1="test",
            question_2="test",
        )
        assert d1.selected_strategy == d2.selected_strategy
        assert d1.confidence == d2.confidence

    def test_serialization_backward_compat(self):
        d = {
            "original_question_1": "Q1",
            "original_question_2": "Q2",
        }
        analysis = QueryAnalysis.from_dict(d)
        assert analysis.decision_trace is not None
        assert isinstance(analysis.decision_trace, DecisionTrace)

    def test_empty_decision_trace_serialization(self):
        analysis = QueryAnalysis()
        json_str = analysis.to_json()
        restored = QueryAnalysis.from_dict(json.loads(json_str))
        assert isinstance(restored.decision_trace, DecisionTrace)
