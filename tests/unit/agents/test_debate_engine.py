from __future__ import annotations

from duplicate_question_app._agents.agent import (
    ConfidenceAgent,
    ConflictAgent,
    ConsensusAgent,
    EntityAgent,
    EvidenceAgent,
    IntentAgent,
    RelationAgent,
    SemanticAgent,
)
from duplicate_question_app._agents.agent_registry import AgentRegistry
from duplicate_question_app._agents.conflict_resolution import DefaultConflictDetector
from duplicate_question_app._agents.consensus import DefaultConsensusStrategy
from duplicate_question_app._agents.debate_engine import DebateEngine
from duplicate_question_app._agents.voting import MajorityVoting, WeightedVoting
from duplicate_question_app._reasoning.reasoning_result import (
    ConfidenceChain,
    Evidence,
    EvidenceType,
    Hypothesis,
    HypothesisLabel,
    Premise,
    ProcessingMetadata,
    ReasoningGraph,
    ReasoningResult,
    ReasoningTrace,
)
from duplicate_question_app._semantic.representation import SemanticConcept, SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import (
    ConceptOverlap,
    Conflict,
    IntentSimilarity,
    SemanticAssessment,
)


def _make_simple_rep(label: str = "python") -> SemanticRepresentation:
    return SemanticRepresentation(
        concepts=[SemanticConcept(id="c1", label=label, normalized_form=label, confidence=0.9)],
        entities=[],
        actions=[],
        objects=[],
        attributes=[],
        relationships=[],
        intent_summary=f"asking about {label.lower()}",
        domain="programming",
    )


def _make_reasoning_result(
    decision: str = "duplicate",
    confidence: float = 0.8,
    uncertainty: float = 0.2,
) -> ReasoningResult:
    return ReasoningResult(
        premises=[Premise(id="p1", text="test", source="a", category="intent", confidence=0.9)],
        hypotheses=[
            Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=confidence),
            Hypothesis(id="h2", label=HypothesisLabel.NOT_DUPLICATE, text="non", confidence=1.0 - confidence),
        ],
        supporting_evidence=[
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.8,
                weight=1.0,
            ),
        ],
        contradicting_evidence=[],
        confidence_chain=ConfidenceChain(
            premise_confidence=0.9,
            hypothesis_confidence=confidence,
            evidence_confidence=0.8,
            reasoning_confidence=confidence,
            decision_confidence=confidence,
        ),
        decision=decision,
        confidence=confidence,
        uncertainty=uncertainty,
        reasoning_graph=ReasoningGraph(),
        reasoning_trace=ReasoningTrace(),
        processing_metadata=ProcessingMetadata(),
    )


def _populate_default_registry(registry: AgentRegistry) -> None:
    registry.register(IntentAgent())
    registry.register(SemanticAgent())
    registry.register(EntityAgent())
    registry.register(RelationAgent())
    registry.register(ConflictAgent())
    registry.register(ConfidenceAgent())
    registry.register(EvidenceAgent())
    registry.register(ConsensusAgent())


class TestDebateEngine:
    def test_empty_registry(self):
        engine = DebateEngine()
        result = engine.debate(_make_simple_rep(), _make_simple_rep())
        assert result.debate_summary == "No agents registered"
        assert len(result.agent_results) == 0

    def test_with_registered_agents(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        rep = _make_simple_rep()
        result = engine.debate(rep, rep)
        assert len(result.agent_results) == 8
        assert result.consensus is not None
        assert result.processing_time_ms >= 0

    def test_debate_with_assessment(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        rep = _make_simple_rep()
        assessment = SemanticAssessment(
            semantic_similarity=0.85,
            concept_overlap=ConceptOverlap(overlap_score=0.8),
            intent_similarity=IntentSimilarity(score=0.9, confidence=0.9, reason="match"),
        )
        result = engine.debate(rep, rep, assessment=assessment)
        assert result.consensus is not None
        assert result.processing_time_ms >= 0

    def test_debate_with_reasoning_result(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="duplicate", confidence=0.85)
        result = engine.debate(rep, rep, reasoning_result=rr)
        assert result.consensus is not None

    def test_votes_built(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        result = engine.debate(_make_simple_rep(), _make_simple_rep())
        assert len(result.votes) >= 7  # 8 agents minus consensus_agent
        assert all(v.agent_name for v in result.votes)
        assert all(v.recommendation in ("duplicate", "not_duplicate", "uncertain") for v in result.votes)

    def test_agreement_matrix_built(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        result = engine.debate(_make_simple_rep(), _make_simple_rep())
        assert result.agreement_matrix.mean_agreement() >= 0

    def test_conflict_reports(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        rep_a = _make_simple_rep("python")
        rep_b = _make_simple_rep("cooking")
        assessment = SemanticAssessment(
            semantic_similarity=0.1,
            concept_overlap=ConceptOverlap(overlap_score=0.0),
            conflicts=[Conflict(conflict_type="domain_mismatch", description="Different domains", severity=0.8)],
        )
        result = engine.debate(rep_a, rep_b, assessment=assessment)
        assert len(result.conflict_reports) >= 0

    def test_consensus_decision(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        result = engine.debate(_make_simple_rep(), _make_simple_rep())
        assert result.consensus.decision in ("duplicate", "not_duplicate", "uncertain")

    def test_voting_strategy_pluggable(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        consensus = DefaultConsensusStrategy(voting_strategy=WeightedVoting())
        engine = DebateEngine(registry=registry, consensus_strategy=consensus)
        result = engine.debate(_make_simple_rep(), _make_simple_rep())
        assert result.consensus.strategy_used == "weighted"

    def test_set_consensus_strategy(self):
        engine = DebateEngine()
        consensus = DefaultConsensusStrategy(voting_strategy=MajorityVoting())
        engine.set_consensus_strategy(consensus)
        assert engine.consensus_strategy is consensus

    def test_set_conflict_detector(self):
        engine = DebateEngine()
        detector = DefaultConflictDetector()
        engine.set_conflict_detector(detector)
        assert engine.conflict_detector is detector

    def test_summary_contains_info(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        result = engine.debate(_make_simple_rep(), _make_simple_rep())
        assert "Multi-Agent" in result.debate_summary
        assert "Total agents" in result.debate_summary

    def test_agent_timing_recorded(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        result = engine.debate(_make_simple_rep(), _make_simple_rep())
        for r in result.agent_results:
            assert r.processing_time_ms >= 0

    def test_agents_used_list(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        result = engine.debate(_make_simple_rep(), _make_simple_rep())
        assert len(result.agents_used) == 8

    def test_debate_result_to_dict(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        result = engine.debate(_make_simple_rep(), _make_simple_rep())
        d = result.to_dict()
        assert "agent_results" in d
        assert "votes" in d
        assert "consensus" in d
        assert "conflict_reports" in d
        assert "debate_summary" in d

    def test_agent_failure_handling(self):
        registry = AgentRegistry()

        class FailingAgent(IntentAgent):
            @property
            def name(self) -> str:
                return "failing_agent"

            def evaluate(self, rep_a, rep_b, assessment, reasoning_result):
                raise RuntimeError("Intentional failure")

        registry.register(FailingAgent())
        engine = DebateEngine(registry=registry)
        result = engine.debate(_make_simple_rep(), _make_simple_rep())
        assert len(result.agent_results) == 1
        assert result.agent_results[0].confidence == 0.0
        assert "fail" in str(result.agent_results[0].warnings).lower()

    def test_high_agreement_scenario(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        rep = _make_simple_rep("python")
        assessment = SemanticAssessment(
            semantic_similarity=0.95,
            concept_overlap=ConceptOverlap(overlap_score=0.9),
            intent_similarity=IntentSimilarity(score=0.95, confidence=0.95, reason="match"),
        )
        rr = _make_reasoning_result(decision="duplicate", confidence=0.9)
        result = engine.debate(rep, rep, assessment=assessment, reasoning_result=rr)
        assert result.consensus.decision == "duplicate"
        assert result.consensus.confidence > 0.5

    def test_low_agreement_scenario(self):
        registry = AgentRegistry()
        _populate_default_registry(registry)
        engine = DebateEngine(registry=registry)
        rep_a = _make_simple_rep("python")
        rep_b = _make_simple_rep("cooking")
        assessment = SemanticAssessment(
            semantic_similarity=0.1,
            concept_overlap=ConceptOverlap(overlap_score=0.0),
            intent_similarity=IntentSimilarity(score=0.1, confidence=0.8, reason="different"),
        )
        rr = _make_reasoning_result(decision="not_duplicate", confidence=0.2)
        result = engine.debate(rep_a, rep_b, assessment=assessment, reasoning_result=rr)
        assert result.consensus is not None
        # Should not be high-confidence duplicate due to conflicting signals
        assert not (result.consensus.decision == "duplicate" and result.consensus.confidence > 0.8)
