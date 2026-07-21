from __future__ import annotations

from duplicate_question_app._agents.agent_result import (
    AgentResult,
    AgreementMatrix,
    ConflictReport,
    ConsensusResult,
    DebateResult,
    Vote,
)
from duplicate_question_app._reasoning.reasoning_result import Evidence, EvidenceType


class TestAgentResult:
    def test_create_agent_result(self):
        r = AgentResult(agent_name="test", confidence=0.8, recommendation="duplicate")
        assert r.agent_name == "test"
        assert r.confidence == 0.8
        assert r.recommendation == "duplicate"
        assert r.warnings == []
        assert r.processing_time_ms == 0.0

    def test_agent_result_to_dict(self):
        ev = Evidence(id="e1", hypothesis_id="h1", evidence_type=EvidenceType.SUPPORTING, text="test")
        r = AgentResult(
            agent_name="test",
            confidence=0.7,
            recommendation="not_duplicate",
            supporting_evidence=[ev],
            warnings=["warning"],
        )
        d = r.to_dict()
        assert d["agent_name"] == "test"
        assert d["confidence"] == 0.7
        assert d["recommendation"] == "not_duplicate"
        assert len(d["supporting_evidence"]) == 1
        assert d["warnings"] == ["warning"]

    def test_vote_create(self):
        v = Vote(agent_name="a", recommendation="duplicate", confidence=0.9)
        assert v.agent_name == "a"
        assert v.weight == 1.0

    def test_vote_to_dict(self):
        v = Vote(agent_name="a", recommendation="duplicate", confidence=0.9, weight=0.8)
        d = v.to_dict()
        assert d["weight"] == 0.8

    def test_agreement_matrix(self):
        m = AgreementMatrix(matrix={"a": {"b": 1.0, "c": 0.0}, "b": {"a": 1.0, "c": 0.0}, "c": {"a": 0.0, "b": 0.0}})
        assert m.get_agreement("a", "b") == 1.0
        assert m.get_agreement("a", "c") == 0.0
        assert m.get_agreement("x", "y") == 0.0
        assert m.mean_agreement() > 0

    def test_agreement_matrix_empty(self):
        m = AgreementMatrix()
        assert m.mean_agreement() == 0.0

    def test_agreement_matrix_to_dict(self):
        m = AgreementMatrix(matrix={"a": {"b": 1.0}})
        d = m.to_dict()
        assert "matrix" in d
        assert "mean_agreement" in d

    def test_conflict_report_create(self):
        c = ConflictReport(conflict_type="disagreement", agents=["a", "b"], description="test", severity=0.8)
        assert c.conflict_type == "disagreement"
        assert c.severity == 0.8

    def test_conflict_report_to_dict(self):
        c = ConflictReport(conflict_type="test", severity=0.5)
        d = c.to_dict()
        assert d["conflict_type"] == "test"

    def test_consensus_result_create(self):
        cr = ConsensusResult(decision="duplicate", confidence=0.8, strategy_used="majority")
        assert cr.decision == "duplicate"
        assert cr.vote_counts == {}

    def test_consensus_result_to_dict(self):
        cr = ConsensusResult(decision="duplicate", confidence=0.8, vote_counts={"dup": 3, "non": 1})
        d = cr.to_dict()
        assert d["vote_counts"]["dup"] == 3
        assert d["strategy_used"] == ""

    def test_debate_result_create(self):
        dr = DebateResult(agents_used=["a", "b"])
        assert dr.processing_time_ms == 0.0
        assert dr.agents_used == ["a", "b"]

    def test_debate_result_to_dict(self):
        dr = DebateResult(
            agent_results=[
                AgentResult(agent_name="a", confidence=0.9, recommendation="duplicate"),
            ],
            votes=[Vote(agent_name="a", recommendation="duplicate", confidence=0.9)],
            agents_used=["a"],
        )
        d = dr.to_dict()
        assert len(d["agent_results"]) == 1
        assert len(d["votes"]) == 1
        assert d["agents_used"] == ["a"]

    def test_debate_result_none_consensus(self):
        dr = DebateResult()
        d = dr.to_dict()
        assert d["consensus"] is None
