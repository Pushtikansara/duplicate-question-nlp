from __future__ import annotations

from duplicate_question_app._agents.agent_result import AgentResult, ConflictReport, ConsensusResult, Vote
from duplicate_question_app._agents.interfaces import ConsensusStrategy, VotingStrategy
from duplicate_question_app._agents.voting import MajorityVoting


class DefaultConsensusStrategy(ConsensusStrategy):
    def __init__(self, voting_strategy: VotingStrategy | None = None):
        self._voting = voting_strategy or MajorityVoting()

    @property
    def voting_strategy(self) -> VotingStrategy:
        return self._voting

    def build(
        self,
        results: list[AgentResult],
        votes: list[Vote],
        conflict_reports: list[ConflictReport],
    ) -> ConsensusResult:
        if not results:
            return ConsensusResult(
                decision="uncertain",
                confidence=0.0,
                strategy_used=self._voting.name,
                details="No agent results",
            )

        vote_result = self._voting.compute(votes)

        severity_penalty = sum(c.severity for c in conflict_reports) / max(1, len(conflict_reports))
        adjusted_confidence = vote_result.confidence * (1.0 - severity_penalty * 0.3)
        adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))

        if severity_penalty > 0.7:
            return ConsensusResult(
                decision="uncertain",
                confidence=adjusted_confidence,
                vote_counts=vote_result.vote_counts,
                weighted_vote=vote_result.weighted_vote,
                strategy_used=self._voting.name,
                details=f"Overridden to uncertain: high conflict severity ({severity_penalty:.2f})",
            )

        return ConsensusResult(
            decision=vote_result.decision,
            confidence=adjusted_confidence,
            vote_counts=vote_result.vote_counts,
            weighted_vote=vote_result.weighted_vote,
            strategy_used=self._voting.name,
            details=vote_result.details + f" | Conflict penalty: {severity_penalty:.2f}",
        )
