from __future__ import annotations

from collections import Counter

from duplicate_question_app._agents.agent_result import ConsensusResult, Vote
from duplicate_question_app._agents.interfaces import VotingStrategy


class MajorityVoting(VotingStrategy):
    @property
    def name(self) -> str:
        return "majority"

    def compute(self, votes: list[Vote]) -> ConsensusResult:
        if not votes:
            return ConsensusResult(decision="uncertain", confidence=0.0, strategy_used=self.name, details="No votes")

        counts: Counter[str] = Counter()
        for v in votes:
            counts[v.recommendation] += 1

        if not counts:
            return ConsensusResult(
                decision="uncertain", confidence=0.0, strategy_used=self.name, details="No votes counted"
            )

        total = sum(counts.values())
        decision = counts.most_common(1)[0][0]
        top_count = counts.most_common(1)[0][1]
        confidence = top_count / total if total > 0 else 0.0

        if len(counts) >= 2 and counts.most_common(2)[0][1] == counts.most_common(2)[1][1]:
            decision = "uncertain"
            confidence = 0.0

        return ConsensusResult(
            decision=decision,
            confidence=confidence,
            vote_counts=dict(counts),
            weighted_vote={k: v / total for k, v in counts.items()},
            strategy_used=self.name,
            details=f"Majority vote: {top_count}/{total} for {decision}",
        )


class WeightedVoting(VotingStrategy):
    def __init__(self, default_weight: float = 1.0):
        self._default_weight = default_weight

    @property
    def name(self) -> str:
        return "weighted"

    def compute(self, votes: list[Vote]) -> ConsensusResult:
        if not votes:
            return ConsensusResult(decision="uncertain", confidence=0.0, strategy_used=self.name, details="No votes")

        weighted: dict[str, float] = {}
        total_weight = 0.0
        for v in votes:
            w = v.weight * v.confidence
            weighted[v.recommendation] = weighted.get(v.recommendation, 0.0) + w
            total_weight += w

        if not weighted or total_weight == 0:
            return ConsensusResult(
                decision="uncertain", confidence=0.0, strategy_used=self.name, details="Zero total weight"
            )

        decision = max(weighted, key=weighted.get)
        confidence = weighted[decision] / total_weight

        sorted_weights = sorted(weighted.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_weights) >= 2 and abs(sorted_weights[0][1] - sorted_weights[1][1]) < 0.01:
            decision = "uncertain"
            confidence = 0.0

        return ConsensusResult(
            decision=decision,
            confidence=confidence,
            vote_counts={k: int(v / max(1, total_weight) * 100) for k, v in weighted.items()},
            weighted_vote={k: v / total_weight for k, v in weighted.items()},
            strategy_used=self.name,
            details=f"Weighted vote: {decision} with {confidence:.3f} confidence ({len(votes)} agents)",
        )


class ConfidenceWeightedVoting(VotingStrategy):
    @property
    def name(self) -> str:
        return "confidence_weighted"

    def compute(self, votes: list[Vote]) -> ConsensusResult:
        if not votes:
            return ConsensusResult(decision="uncertain", confidence=0.0, strategy_used=self.name, details="No votes")

        weighted: dict[str, float] = {}
        total_confidence = 0.0
        for v in votes:
            weighted[v.recommendation] = weighted.get(v.recommendation, 0.0) + v.confidence
            total_confidence += v.confidence

        if not weighted or total_confidence == 0:
            return ConsensusResult(
                decision="uncertain", confidence=0.0, strategy_used=self.name, details="Zero total confidence"
            )

        decision = max(weighted, key=weighted.get)
        confidence = weighted[decision] / total_confidence

        sorted_weights = sorted(weighted.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_weights) >= 2 and abs(sorted_weights[0][1] - sorted_weights[1][1]) < 0.01:
            decision = "uncertain"
            confidence = 0.0

        return ConsensusResult(
            decision=decision,
            confidence=confidence,
            vote_counts={k: int(v / max(1, total_confidence) * 100) for k, v in weighted.items()},
            weighted_vote={k: v / total_confidence for k, v in weighted.items()},
            strategy_used=self.name,
            details=f"Confidence-weighted vote: {decision} with {confidence:.3f} confidence",
        )
