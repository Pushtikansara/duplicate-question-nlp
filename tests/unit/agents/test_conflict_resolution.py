from __future__ import annotations

from duplicate_question_app._agents.agent_result import AgentResult, Vote
from duplicate_question_app._agents.conflict_resolution import DefaultConflictDetector


class TestDefaultConflictDetector:
    def setup_method(self):
        self.detector = DefaultConflictDetector()

    def test_empty_inputs(self):
        reports = self.detector.detect([], [])
        assert reports == []

    def test_no_conflicts(self):
        from duplicate_question_app._reasoning.reasoning_result import Evidence, EvidenceType

        results = [
            AgentResult(
                agent_name="a",
                confidence=0.9,
                recommendation="duplicate",
                supporting_evidence=[
                    Evidence(
                        id="e1",
                        hypothesis_id="h1",
                        evidence_type=EvidenceType.SUPPORTING,
                        text="support",
                        confidence=0.8,
                        weight=1.0,
                    )
                ],
            ),
            AgentResult(
                agent_name="b",
                confidence=0.8,
                recommendation="duplicate",
                supporting_evidence=[
                    Evidence(
                        id="e2",
                        hypothesis_id="h1",
                        evidence_type=EvidenceType.SUPPORTING,
                        text="support",
                        confidence=0.7,
                        weight=1.0,
                    )
                ],
            ),
        ]
        votes = [Vote("a", "duplicate", 0.9), Vote("b", "duplicate", 0.8)]
        reports = self.detector.detect(results, votes)
        assert len(reports) == 0

    def test_agent_disagreement(self):
        results = [
            AgentResult(agent_name="a", confidence=0.9, recommendation="duplicate"),
            AgentResult(agent_name="b", confidence=0.8, recommendation="not_duplicate"),
        ]
        votes = [Vote("a", "duplicate", 0.9), Vote("b", "not_duplicate", 0.8)]
        reports = self.detector.detect(results, votes)
        assert any(r.conflict_type == "agent_disagreement" for r in reports)

    def test_low_confidence(self):
        results = [
            AgentResult(agent_name="a", confidence=0.2, recommendation="duplicate"),
        ]
        votes = [Vote("a", "duplicate", 0.2)]
        reports = self.detector.detect(results, votes)
        assert any(r.conflict_type == "low_confidence" for r in reports)

    def test_opposite_conclusions(self):
        results = [
            AgentResult(agent_name="a", confidence=0.9, recommendation="duplicate"),
            AgentResult(agent_name="b", confidence=0.8, recommendation="not_duplicate"),
        ]
        votes = [Vote("a", "duplicate", 0.9), Vote("b", "not_duplicate", 0.8)]
        reports = self.detector.detect(results, votes)
        assert any(r.conflict_type == "opposite_conclusion" for r in reports)

    def test_missing_evidence(self):
        results = [
            AgentResult(
                agent_name="a",
                confidence=0.9,
                recommendation="duplicate",
                supporting_evidence=[],
                contradicting_evidence=[],
            ),
        ]
        votes = [Vote("a", "duplicate", 0.9)]
        reports = self.detector.detect(results, votes)
        assert any(r.conflict_type == "missing_evidence" for r in reports)

    def test_contradictory_evidence(self):
        from duplicate_question_app._reasoning.reasoning_result import Evidence, EvidenceType

        results = [
            AgentResult(
                agent_name="a",
                confidence=0.9,
                recommendation="duplicate",
                supporting_evidence=[
                    Evidence(
                        id="e1",
                        hypothesis_id="h1",
                        evidence_type=EvidenceType.SUPPORTING,
                        text="support",
                        confidence=0.8,
                        weight=1.0,
                    )
                ],
                contradicting_evidence=[
                    Evidence(
                        id="e2",
                        hypothesis_id="h1",
                        evidence_type=EvidenceType.CONTRADICTING,
                        text="contra",
                        confidence=0.8,
                        weight=1.0,
                    )
                ],
            ),
        ]
        votes = [Vote("a", "duplicate", 0.9)]
        reports = self.detector.detect(results, votes)
        assert any(r.conflict_type == "contradictory_evidence" for r in reports)

    def test_agent_warnings(self):
        results = [
            AgentResult(agent_name="a", confidence=0.9, recommendation="duplicate", warnings=["something wrong"]),
        ]
        votes = [Vote("a", "duplicate", 0.9)]
        reports = self.detector.detect(results, votes)
        assert any(r.conflict_type == "agent_warnings" for r in reports)
