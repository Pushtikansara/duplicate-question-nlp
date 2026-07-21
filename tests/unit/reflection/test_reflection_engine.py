from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from duplicate_question_app._reflection.confidence_auditor import ConfidenceAuditor
from duplicate_question_app._reflection.configuration import ReflectionConfig
from duplicate_question_app._reflection.consistency_checker import ConsistencyChecker
from duplicate_question_app._reflection.debate_auditor import DebateAuditor
from duplicate_question_app._reflection.evidence_analyzer import EvidenceAnalyzer
from duplicate_question_app._reflection.human_review import HumanReviewDecider
from duplicate_question_app._reflection.interfaces import (
    AuditorResult,
    ConsistencyWarning,
    RecommendationType,
    RiskLevel,
    TrustLevel,
)
from duplicate_question_app._reflection.memory_auditor import MemoryAuditor
from duplicate_question_app._reflection.quality_estimator import QualityEstimator
from duplicate_question_app._reflection.reasoning_auditor import ReasoningAuditor
from duplicate_question_app._reflection.recommendation_engine import RecommendationEngine
from duplicate_question_app._reflection.reflection_engine import ReflectionEngine
from duplicate_question_app._reflection.reflection_report import ReflectionReportGenerator
from duplicate_question_app._reflection.reflection_result import ReflectionResult
from duplicate_question_app._reflection.routing_auditor import RoutingAuditor
from duplicate_question_app._reflection.trust_engine import TrustEngine


@dataclass
class MockRoutingResult:
    selected_pipeline: str = "full_cognitive"
    complexity: str = "medium"
    required_modules: list[str] = field(default_factory=lambda: ["cross_encoder", "semantic", "reasoning", "made"])
    skipped_modules: list[str] = field(default_factory=list)
    confidence: float = 0.9


@dataclass
class MockReasoningResult:
    premises: list = field(default_factory=lambda: [{"text": "p1"}, {"text": "p2"}, {"text": "p3"}])
    hypotheses: list = field(default_factory=lambda: [{"text": "h1"}])
    supporting_evidence: list = field(default_factory=lambda: [{"text": "e1"}, {"text": "e2"}])
    contradicting_evidence: list = field(default_factory=list)
    reasoning_trace: dict = field(default_factory=lambda: {"steps": []})
    confidence: float = 0.85
    uncertainty: float = 0.15
    decision: str = "duplicate"


@dataclass
class MockDebateResult:
    agent_results: list = field(default_factory=lambda: [{"name": f"agent{i}"} for i in range(8)])
    votes: list = field(default_factory=lambda: [{"agent": "a1", "recommendation": "duplicate"}])
    conflict_reports: list = field(default_factory=list)
    consensus: Any = None
    agreement_matrix: Any = None
    agents_used: list = field(default_factory=lambda: [f"agent{i}" for i in range(8)])
    processing_time_ms: float = 5.0
    debate_summary: str = ""


@dataclass
class MockConsensus:
    confidence: float = 0.9
    decision: str = "duplicate"
    vote_counts: dict = field(default_factory=lambda: {"duplicate": 6, "not_duplicate": 2})
    weighted_vote: dict = field(default_factory=lambda: {"duplicate": 0.75, "not_duplicate": 0.25})
    strategy_used: str = "majority"
    details: str = ""


@dataclass
class MockAgreementMatrix:
    matrix: dict = field(default_factory=lambda: {"a": {"b": 0.8}})

    def mean_agreement(self) -> float:
        return 0.85


@dataclass
class MockMemoryStats:
    total_entries: int = 100
    total_by_type: dict = field(default_factory=lambda: {"episodic": 50, "semantic": 30, "reasoning": 20})
    avg_quality: float = 0.75
    avg_confidence: float = 0.80
    oldest_entry: Any = None
    newest_entry: Any = None
    version_count: int = 1
    deleted_count: int = 0


class MockMemoryManager:
    def get_statistics(self) -> MockMemoryStats:
        return MockMemoryStats()


@dataclass
class MockPipelineContext:
    retrieved_memories: list = field(default_factory=lambda: [{"id": "m1"}])
    question_a: str = "q1"
    question_b: str = "q2"


class TestReflectionConfig:
    def test_defaults(self):
        config = ReflectionConfig()
        assert config.enable_routing_audit is True
        assert config.human_review_threshold == 40.0
        assert config.low_confidence_threshold == 0.6

    def test_trust_weights_sum(self):
        config = ReflectionConfig()
        total = sum(config.trust_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_custom_config(self):
        config = ReflectionConfig(enable_routing_audit=False, human_review_threshold=50.0)
        assert config.enable_routing_audit is False
        assert config.human_review_threshold == 50.0


class TestRoutingAuditor:
    def test_audit_with_result(self):
        auditor = RoutingAuditor()
        result = MockRoutingResult()
        assessment = auditor.audit(result)
        assert assessment.module == "routing"
        assert assessment.score > 0.5
        assert assessment.details["selected_pipeline"] == "full_cognitive"

    def test_audit_without_result(self):
        auditor = RoutingAuditor()
        assessment = auditor.audit(None)
        assert assessment.score == 0.5
        assert assessment.passed is False

    def test_low_confidence_warning(self):
        auditor = RoutingAuditor()
        result = MockRoutingResult(confidence=0.3)
        assessment = auditor.audit(result)
        assert len(assessment.warnings) > 0


class TestReasoningAuditor:
    def test_audit_with_result(self):
        auditor = ReasoningAuditor()
        result = MockReasoningResult()
        assessment = auditor.audit(result)
        assert assessment.score > 0.5
        assert assessment.details["premise_count"] == 3

    def test_audit_without_result(self):
        auditor = ReasoningAuditor()
        assessment = auditor.audit(None)
        assert assessment.score == 0.5

    def test_no_evidence_warning(self):
        auditor = ReasoningAuditor()
        result = MockReasoningResult(supporting_evidence=[], contradicting_evidence=[])
        assessment = auditor.audit(result)
        assert any("evidence" in w.lower() for w in assessment.warnings)


class TestDebateAuditor:
    def test_audit_with_consensus(self):
        auditor = DebateAuditor()
        result = MockDebateResult(
            consensus=MockConsensus(),
            agreement_matrix=MockAgreementMatrix(),
        )
        assessment = auditor.audit(result)
        assert assessment.score > 0.5
        assert assessment.details["agent_count"] == 8

    def test_audit_without_debate(self):
        auditor = DebateAuditor()
        assessment = auditor.audit(None)
        assert assessment.score == 0.5

    def test_high_conflicts_warning(self):
        auditor = DebateAuditor()
        conflicts = [{"type": "disagreement"}] * 5
        result = MockDebateResult(
            conflict_reports=conflicts,
            consensus=MockConsensus(),
            agreement_matrix=MockAgreementMatrix(),
        )
        assessment = auditor.audit(result)
        assert len(assessment.warnings) > 0


class TestMemoryAuditor:
    def test_audit_with_manager(self):
        auditor = MemoryAuditor()
        mm = MockMemoryManager()
        ctx = MockPipelineContext()
        assessment = auditor.audit(mm, ctx)
        assert assessment.score > 0.5
        assert assessment.details["total_entries"] == 100

    def test_audit_without_manager(self):
        auditor = MemoryAuditor()
        assessment = auditor.audit(None, None)
        assert assessment.score == 0.0


class TestConfidenceAuditor:
    def test_audit_high_confidence(self):
        auditor = ConfidenceAuditor()
        pred = {"confidence": 0.95, "prob_duplicate": 0.92}
        assessment = auditor.audit(pred, None)
        assert assessment.score > 0.5

    def test_audit_low_confidence(self):
        auditor = ConfidenceAuditor()
        pred = {"confidence": 0.40, "prob_duplicate": 0.55}
        assessment = auditor.audit(pred, None)
        assert assessment.score < 0.6

    def test_audit_borderline(self):
        auditor = ConfidenceAuditor()
        pred = {"confidence": 0.51, "prob_duplicate": 0.51}
        assessment = auditor.audit(pred, None)
        assert len(assessment.warnings) > 0

    def test_audit_with_calibration(self):
        auditor = ConfidenceAuditor()
        pred = {"confidence": 0.90, "prob_duplicate": 0.88}
        cal = {"ece": 0.25}
        assessment = auditor.audit(pred, cal)
        assert any("calibration" in w.lower() for w in assessment.warnings)


class TestTrustEngine:
    def test_high_trust(self):
        engine = TrustEngine()
        high = AuditorResult(module="test", score=0.95, details={})
        score, level, risk = engine.compute_trust_score(high, high, high, high, high, 0.95, 0.95)
        assert score >= 80.0
        assert level == TrustLevel.HIGH
        assert risk == RiskLevel.LOW

    def test_low_trust(self):
        engine = TrustEngine()
        low = AuditorResult(module="test", score=0.2, details={}, warnings=["bad"], passed=False)
        score, level, risk = engine.compute_trust_score(low, low, low, low, low, 0.1, 0.1)
        assert score < 40.0
        assert level == TrustLevel.CRITICAL
        assert risk == RiskLevel.CRITICAL


class TestConsistencyChecker:
    def test_no_warnings_with_good_data(self):
        checker = ConsistencyChecker()
        reasoning = MockReasoningResult()
        debate = MockDebateResult(consensus=MockConsensus(), agreement_matrix=MockAgreementMatrix())
        pred = {"predicted_label": 1, "prediction": "Duplicate"}
        warnings = checker.check(reasoning, debate, pred)
        assert len(warnings) == 0

    def test_conflicting_evidence_warning(self):
        checker = ConsistencyChecker()
        reasoning = MockReasoningResult(
            supporting_evidence=[{"text": "e1"}],
            contradicting_evidence=[{"text": "c1"}, {"text": "c2"}],
        )
        debate = MockDebateResult(consensus=MockConsensus())
        pred = {"predicted_label": 1}
        warnings = checker.check(reasoning, debate, pred)
        assert any(w.warning_type == "conflicting_evidence" for w in warnings)

    def test_cross_module_inconsistency(self):
        checker = ConsistencyChecker()
        reasoning = MockReasoningResult(decision="not_duplicate")
        debate = MockDebateResult(consensus=MockConsensus(decision="duplicate"))
        pred = {"predicted_label": 0, "prediction": "Non-Duplicate"}
        warnings = checker.check(reasoning, debate, pred)
        assert any(w.warning_type == "cross_module_inconsistency" for w in warnings)


class TestEvidenceAnalyzer:
    def test_analyze_with_data(self):
        analyzer = EvidenceAnalyzer()
        reasoning = MockReasoningResult()
        debate = MockDebateResult(consensus=MockConsensus())
        result = analyzer.analyze(reasoning, debate)
        assert result["total_evidence"] > 0
        assert result["completeness"] > 0

    def test_analyze_without_data(self):
        analyzer = EvidenceAnalyzer()
        result = analyzer.analyze(None, None)
        assert result["total_evidence"] == 0
        assert result["completeness"] == 0.0


class TestQualityEstimator:
    def test_high_quality(self):
        estimator = QualityEstimator()
        mock = type(
            "_",
            (),
            {
                "trust_score": 90.0,
                "consistency_warnings": [],
                "routing_assessment": AuditorResult("r", 0.9, {}),
                "reasoning_assessment": AuditorResult("re", 0.9, {}),
                "debate_assessment": AuditorResult("d", 0.9, {}),
                "memory_assessment": AuditorResult("m", 0.9, {}),
                "confidence_assessment": AuditorResult("c", 0.9, {}),
            },
        )()
        result = estimator.estimate(mock)
        assert result["quality_level"] == "high"
        assert result["quality_score"] > 0.7

    def test_low_quality(self):
        estimator = QualityEstimator()
        mock = type(
            "_",
            (),
            {
                "trust_score": 20.0,
                "consistency_warnings": [{"w": 1}],
                "routing_assessment": AuditorResult("r", 0.2, {}, ["bad"], False),
                "reasoning_assessment": AuditorResult("re", 0.2, {}, ["bad"], False),
                "debate_assessment": AuditorResult("d", 0.2, {}, ["bad"], False),
                "memory_assessment": AuditorResult("m", 0.2, {}, ["bad"], False),
                "confidence_assessment": AuditorResult("c", 0.2, {}, ["bad"], False),
            },
        )()
        result = estimator.estimate(mock)
        assert result["quality_level"] in ("low", "critical")


class TestRecommendationEngine:
    def test_accept_high_trust(self):
        engine = RecommendationEngine(ReflectionConfig(human_review_threshold=30.0))
        recs = engine.generate(
            trust_score=90.0,
            confidence=0.95,
            routing_assessment=AuditorResult("r", 0.9, {}),
            reasoning_assessment=AuditorResult("re", 0.9, {}),
            debate_assessment=AuditorResult("d", 0.9, {}),
            memory_assessment=AuditorResult("m", 0.9, {}),
            consistency_warnings=[],
            evidence_completeness=0.9,
        )
        assert RecommendationType.ACCEPT in recs

    def test_human_review_low_trust(self):
        engine = RecommendationEngine(ReflectionConfig(human_review_threshold=50.0))
        recs = engine.generate(
            trust_score=30.0,
            confidence=0.5,
            routing_assessment=AuditorResult("r", 0.3, {}),
            reasoning_assessment=AuditorResult("re", 0.3, {}),
            debate_assessment=AuditorResult("d", 0.3, {}),
            memory_assessment=AuditorResult("m", 0.3, {}),
            consistency_warnings=[ConsistencyWarning("w", "d", 0.5)],
            evidence_completeness=0.2,
        )
        assert RecommendationType.HUMAN_REVIEW in recs


class TestHumanReviewDecider:
    def test_should_not_review(self):
        decider = HumanReviewDecider(ReflectionConfig(human_review_threshold=30.0))
        should, reason = decider.should_review(
            trust_score=90.0,
            confidence=0.95,
            routing_assessment=AuditorResult("r", 0.9, {}),
            reasoning_assessment=AuditorResult("re", 0.9, {}),
            debate_assessment=AuditorResult("d", 0.9, {}),
            consistency_warnings=[],
            recommendations=[RecommendationType.ACCEPT],
            explainability_score=0.9,
        )
        assert should is False

    def test_should_review_low_trust(self):
        decider = HumanReviewDecider(ReflectionConfig(human_review_threshold=50.0))
        should, reason = decider.should_review(
            trust_score=30.0,
            confidence=0.4,
            routing_assessment=AuditorResult("r", 0.3, {}),
            reasoning_assessment=AuditorResult("re", 0.2, {}),
            debate_assessment=AuditorResult("d", 0.3, {}),
            consistency_warnings=[ConsistencyWarning("w", "d", 0.5)] * 3,
            recommendations=[RecommendationType.HUMAN_REVIEW],
            explainability_score=0.2,
        )
        assert should is True
        assert len(reason) > 0


class TestReflectionEngine:
    def test_reflect_with_all_data(self):
        engine = ReflectionEngine()
        result = engine.reflect(
            prediction={"predicted_label": 1, "prediction": "Duplicate", "confidence": 0.92, "prob_duplicate": 0.92},
            routing_result=MockRoutingResult(),
            reasoning_result=MockReasoningResult(),
            debate_result=MockDebateResult(consensus=MockConsensus(), agreement_matrix=MockAgreementMatrix()),
            memory_manager=MockMemoryManager(),
            pipeline_context=MockPipelineContext(),
        )
        assert isinstance(result, ReflectionResult)
        assert result.trust_score > 0
        assert result.confidence == 0.92
        assert result.explainability_score > 0

    def test_reflect_minimal(self):
        engine = ReflectionEngine()
        result = engine.reflect(
            prediction={"predicted_label": 0, "prediction": "Non-Duplicate", "confidence": 0.5, "prob_duplicate": 0.3},
        )
        assert isinstance(result, ReflectionResult)
        assert result.routing_assessment is not None
        assert result.routing_assessment.score == 0.5
        assert result.reasoning_assessment is not None

    def test_reflect_result_to_dict(self):
        engine = ReflectionEngine()
        result = engine.reflect(
            prediction={"predicted_label": 1, "prediction": "Duplicate", "confidence": 0.9, "prob_duplicate": 0.9}
        )
        d = result.to_dict()
        assert "trust_score" in d
        assert "trust_level" in d
        assert "recommendations" in d

    def test_disabled_modules(self):
        config = ReflectionConfig(
            enable_routing_audit=False,
            enable_reasoning_audit=False,
            enable_debate_audit=False,
            enable_memory_audit=False,
        )
        engine = ReflectionEngine(config=config)
        result = engine.reflect(
            prediction={"predicted_label": 1, "prediction": "Duplicate", "confidence": 0.9, "prob_duplicate": 0.9},
            routing_result=MockRoutingResult(),
            reasoning_result=MockReasoningResult(),
            debate_result=MockDebateResult(consensus=MockConsensus()),
            memory_manager=MockMemoryManager(),
        )
        assert result.routing_assessment is None
        assert result.reasoning_assessment is None
        assert result.debate_assessment is None
        assert result.memory_assessment is None
        assert result.trust_score > 0


class TestReflectionReport:
    def test_generate_report(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            generator = ReflectionReportGenerator()
            results = [
                ReflectionResult(
                    prediction={"predicted_label": 1},
                    confidence=0.9,
                    trust_score=85.0,
                    trust_level=TrustLevel.HIGH,
                    risk_level=RiskLevel.LOW,
                ),
                ReflectionResult(
                    prediction={"predicted_label": 0},
                    confidence=0.4,
                    trust_score=30.0,
                    trust_level=TrustLevel.CRITICAL,
                    risk_level=RiskLevel.CRITICAL,
                    human_review_required=True,
                    human_review_reason="Low trust",
                    recommendations=[RecommendationType.HUMAN_REVIEW],
                ),
            ]
            path = generator.generate(results, Path(tmp) / "report.md")
            assert Path(path).exists()
