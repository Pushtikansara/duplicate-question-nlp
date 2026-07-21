from __future__ import annotations

from duplicate_question_app._agents.agent_result import AgentResult, ConflictReport, Vote
from duplicate_question_app._agents.consensus import DefaultConsensusStrategy
from duplicate_question_app._agents.voting import WeightedVoting


class TestDefaultConsensusStrategy:
    def setup_method(self):
        self.strategy = DefaultConsensusStrategy()

    def test_empty_results(self):
        result = self.strategy.build([], [], [])
        assert result.decision == "uncertain"
        assert result.confidence == 0.0

    def test_unanimous_without_conflicts(self):
        results = [
            AgentResult(agent_name="a", confidence=0.9, recommendation="duplicate"),
            AgentResult(agent_name="b", confidence=0.8, recommendation="duplicate"),
        ]
        votes = [Vote("a", "duplicate", 0.9), Vote("b", "duplicate", 0.8)]
        conflicts: list[ConflictReport] = []
        result = self.strategy.build(results, votes, conflicts)
        assert result.decision == "duplicate"
        assert result.confidence >= 0.8

    def test_minority_with_conflicts(self):
        results = [
            AgentResult(agent_name="a", confidence=0.9, recommendation="duplicate"),
            AgentResult(agent_name="b", confidence=0.8, recommendation="not_duplicate"),
        ]
        votes = [Vote("a", "duplicate", 0.9), Vote("b", "not_duplicate", 0.8)]
        conflicts = [ConflictReport(conflict_type="agent_disagreement", agents=["b"], severity=0.5)]
        result = self.strategy.build(results, votes, conflicts)
        assert result.decision in ("duplicate", "uncertain")

    def test_high_severity_overrides_to_uncertain(self):
        results = [
            AgentResult(agent_name="a", confidence=0.9, recommendation="duplicate"),
        ]
        votes = [Vote("a", "duplicate", 0.9)]
        conflicts = [ConflictReport(conflict_type="severe", agents=["a"], severity=0.9)]
        result = self.strategy.build(results, votes, conflicts)
        assert result.decision == "uncertain"

    def test_strategy_used_in_result(self):
        results = [AgentResult(agent_name="a", confidence=0.9, recommendation="duplicate")]
        votes = [Vote("a", "duplicate", 0.9)]
        result = self.strategy.build(results, votes, [])
        assert result.strategy_used == "majority"

    def test_custom_voting_strategy(self):
        strategy = DefaultConsensusStrategy(voting_strategy=WeightedVoting())
        results = [AgentResult(agent_name="a", confidence=0.9, recommendation="duplicate")]
        votes = [Vote("a", "duplicate", 0.9)]
        result = strategy.build(results, votes, [])
        assert result.strategy_used == "weighted"

    def test_confidence_adjusted_by_conflicts(self):
        results = [
            AgentResult(agent_name="a", confidence=0.9, recommendation="duplicate"),
            AgentResult(agent_name="b", confidence=0.8, recommendation="duplicate"),
        ]
        votes = [Vote("a", "duplicate", 0.9), Vote("b", "duplicate", 0.8)]
        conflicts = [ConflictReport(conflict_type="minor", agents=["b"], severity=0.3)]
        result = self.strategy.build(results, votes, conflicts)
        assert result.confidence < 1.0  # Penalty applied
