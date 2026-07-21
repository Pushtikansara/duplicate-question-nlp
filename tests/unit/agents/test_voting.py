from __future__ import annotations

from duplicate_question_app._agents.agent_result import Vote
from duplicate_question_app._agents.voting import ConfidenceWeightedVoting, MajorityVoting, WeightedVoting


class TestMajorityVoting:
    def setup_method(self):
        self.strategy = MajorityVoting()

    def test_name(self):
        assert self.strategy.name == "majority"

    def test_empty_votes(self):
        result = self.strategy.compute([])
        assert result.decision == "uncertain"
        assert result.confidence == 0.0

    def test_all_same(self):
        votes = [
            Vote("a", "duplicate", 0.9),
            Vote("b", "duplicate", 0.8),
            Vote("c", "duplicate", 0.7),
        ]
        result = self.strategy.compute(votes)
        assert result.decision == "duplicate"
        assert result.confidence == 1.0

    def test_majority_wins(self):
        votes = [
            Vote("a", "duplicate", 0.9),
            Vote("b", "duplicate", 0.8),
            Vote("c", "not_duplicate", 0.7),
        ]
        result = self.strategy.compute(votes)
        assert result.decision == "duplicate"
        assert result.confidence == 2.0 / 3.0

    def test_tie_returns_uncertain(self):
        votes = [
            Vote("a", "duplicate", 0.9),
            Vote("b", "not_duplicate", 0.8),
        ]
        result = self.strategy.compute(votes)
        assert result.decision == "uncertain"
        assert result.confidence == 0.0

    def test_vote_counts(self):
        votes = [
            Vote("a", "duplicate", 0.9),
            Vote("b", "duplicate", 0.8),
            Vote("c", "not_duplicate", 0.7),
        ]
        result = self.strategy.compute(votes)
        assert result.vote_counts["duplicate"] == 2
        assert result.vote_counts["not_duplicate"] == 1


class TestWeightedVoting:
    def setup_method(self):
        self.strategy = WeightedVoting()

    def test_name(self):
        assert self.strategy.name == "weighted"

    def test_empty(self):
        result = self.strategy.compute([])
        assert result.decision == "uncertain"

    def test_weighted_decision(self):
        votes = [
            Vote("a", "duplicate", 0.5, weight=2.0),
            Vote("b", "not_duplicate", 0.9, weight=1.0),
        ]
        result = self.strategy.compute(votes)
        dup_weight = 2.0 * 0.5
        non_weight = 1.0 * 0.9
        assert result.decision == ("duplicate" if dup_weight > non_weight else "not_duplicate")

    def test_high_confidence_high_weight(self):
        votes = [
            Vote("a", "duplicate", 1.0, weight=3.0),
            Vote("b", "not_duplicate", 0.9, weight=1.0),
        ]
        result = self.strategy.compute(votes)
        assert result.decision == "duplicate"

    def test_tie_uncertain(self):
        votes = [
            Vote("a", "duplicate", 1.0, weight=1.0),
            Vote("b", "not_duplicate", 1.0, weight=1.0),
        ]
        result = self.strategy.compute(votes)
        assert result.decision == "uncertain"

    def test_custom_weight(self):
        strategy = WeightedVoting(default_weight=2.0)
        votes = [
            Vote("a", "duplicate", 1.0),
            Vote("b", "not_duplicate", 1.0),
        ]
        result = strategy.compute(votes)
        # Both have weight=2.0, confidence=1.0 → tie → uncertain
        assert result.decision == "uncertain"


class TestConfidenceWeightedVoting:
    def setup_method(self):
        self.strategy = ConfidenceWeightedVoting()

    def test_name(self):
        assert self.strategy.name == "confidence_weighted"

    def test_empty(self):
        result = self.strategy.compute([])
        assert result.decision == "uncertain"

    def test_confidence_decides(self):
        votes = [
            Vote("a", "duplicate", 0.9),
            Vote("b", "not_duplicate", 0.5),
        ]
        result = self.strategy.compute(votes)
        assert result.decision == "duplicate"

    def test_tie_uncertain(self):
        votes = [
            Vote("a", "duplicate", 0.8),
            Vote("b", "not_duplicate", 0.8),
        ]
        result = self.strategy.compute(votes)
        assert result.decision == "uncertain"

    def test_confidence_sum(self):
        votes = [
            Vote("a", "duplicate", 1.0),
            Vote("b", "duplicate", 0.5),
            Vote("c", "not_duplicate", 0.3),
        ]
        result = self.strategy.compute(votes)
        assert result.decision == "duplicate"
