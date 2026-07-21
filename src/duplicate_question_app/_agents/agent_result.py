from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from duplicate_question_app._reasoning.reasoning_result import Evidence


@dataclass
class AgentResult:
    agent_name: str
    confidence: float
    recommendation: str
    supporting_evidence: list[Evidence] = field(default_factory=list)
    contradicting_evidence: list[Evidence] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "contradicting_evidence": [e.to_dict() for e in self.contradicting_evidence],
            "warnings": self.warnings,
            "metadata": self.metadata,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class Vote:
    agent_name: str
    recommendation: str
    confidence: float
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "weight": self.weight,
        }


@dataclass
class AgreementMatrix:
    matrix: dict[str, dict[str, float]] = field(default_factory=dict)

    def get_agreement(self, agent_a: str, agent_b: str) -> float:
        return self.matrix.get(agent_a, {}).get(agent_b, 0.0)

    def mean_agreement(self) -> float:
        values = []
        for a, inner in self.matrix.items():
            for b, v in inner.items():
                if a != b:
                    values.append(v)
        if not values:
            return 0.0
        return sum(values) / len(values)

    def to_dict(self) -> dict[str, Any]:
        return {"matrix": self.matrix, "mean_agreement": self.mean_agreement()}


@dataclass
class ConflictReport:
    conflict_type: str
    agents: list[str] = field(default_factory=list)
    description: str = ""
    severity: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_type": self.conflict_type,
            "agents": self.agents,
            "description": self.description,
            "severity": self.severity,
        }


@dataclass
class ConsensusResult:
    decision: str
    confidence: float
    vote_counts: dict[str, int] = field(default_factory=dict)
    weighted_vote: dict[str, float] = field(default_factory=dict)
    strategy_used: str = ""
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "confidence": self.confidence,
            "vote_counts": self.vote_counts,
            "weighted_vote": self.weighted_vote,
            "strategy_used": self.strategy_used,
            "details": self.details,
        }


@dataclass
class DebateResult:
    agent_results: list[AgentResult] = field(default_factory=list)
    votes: list[Vote] = field(default_factory=list)
    agreement_matrix: AgreementMatrix = field(default_factory=AgreementMatrix)
    conflict_reports: list[ConflictReport] = field(default_factory=list)
    consensus: ConsensusResult | None = None
    debate_summary: str = ""
    processing_time_ms: float = 0.0
    stages: dict[str, float] = field(default_factory=dict)
    agents_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_results": [r.to_dict() for r in self.agent_results],
            "votes": [v.to_dict() for v in self.votes],
            "agreement_matrix": self.agreement_matrix.to_dict(),
            "conflict_reports": [c.to_dict() for c in self.conflict_reports],
            "consensus": self.consensus.to_dict() if self.consensus else None,
            "debate_summary": self.debate_summary,
            "processing_time_ms": self.processing_time_ms,
            "stages": self.stages,
            "agents_used": self.agents_used,
        }
