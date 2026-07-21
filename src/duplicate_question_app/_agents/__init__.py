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
from duplicate_question_app._agents.agent_registry import AgentRegistry, get_agent_registry
from duplicate_question_app._agents.agent_result import (
    AgentResult,
    AgreementMatrix,
    ConflictReport,
    ConsensusResult,
    DebateResult,
    Vote,
)
from duplicate_question_app._agents.confidence_aggregation import (
    MaxAggregation,
    MeanAggregation,
    MinAggregation,
    ProductAggregation,
)
from duplicate_question_app._agents.conflict_resolution import DefaultConflictDetector
from duplicate_question_app._agents.consensus import DefaultConsensusStrategy
from duplicate_question_app._agents.debate_engine import DebateEngine
from duplicate_question_app._agents.interfaces import (
    AgentPlugin,
    CognitiveAgent,
    ConfidenceAggregationStrategy,
    ConflictDetectionStrategy,
    ConsensusStrategy,
    VotingStrategy,
)
from duplicate_question_app._agents.voting import ConfidenceWeightedVoting, MajorityVoting, WeightedVoting

__all__ = [
    "AgentResult",
    "Vote",
    "AgreementMatrix",
    "ConflictReport",
    "ConsensusResult",
    "DebateResult",
    "CognitiveAgent",
    "VotingStrategy",
    "ConsensusStrategy",
    "ConflictDetectionStrategy",
    "AgentPlugin",
    "ConfidenceAggregationStrategy",
    "IntentAgent",
    "SemanticAgent",
    "EntityAgent",
    "RelationAgent",
    "ConflictAgent",
    "ConfidenceAgent",
    "EvidenceAgent",
    "ConsensusAgent",
    "AgentRegistry",
    "get_agent_registry",
    "DebateEngine",
    "MajorityVoting",
    "WeightedVoting",
    "ConfidenceWeightedVoting",
    "DefaultConsensusStrategy",
    "MeanAggregation",
    "MinAggregation",
    "MaxAggregation",
    "ProductAggregation",
    "DefaultConflictDetector",
]
