# MADE: Multi-Agent Cognitive Debate Engine -- System Architecture

## Overview

MADE (Multi-Agent Cognitive Debate Engine) is a deterministic multi-agent system that evaluates question pair representations through eight specialist cognitive agents. Each agent independently analyzes semantic representations and reasoning results, then votes on whether a question pair is duplicate, not duplicate, or uncertain. The system converts individual agent evaluations into a structured voting process, detects conflicts between agent conclusions, and builds consensus through configurable strategies.

MADE operates as the final cognitive stage in the ARES (Advanced Reasoning and Evaluation System) pipeline, following the Cognitive Reasoning Engine (CRE). It does not introduce new reasoning but rather synthesizes, validates, and consolidates the outputs of upstream components through structured multi-perspective analysis.

## Architecture Diagram

```
                              +------------------------------------------+
                              |        ARES PIPELINE CONTEXT             |
                              |  Linguistic Intelligence -> CRE -> MADE  |
                              +------------------------------------------+
                                                |
                                                v
                     +----------------------------------------------------+
                     |              MADE ARCHITECTURE OVERVIEW            |
                     +----------------------------------------------------+
                     |                                                    |
                     |  +--------------------------------------------+   |
                     |  |           AGENT LAYER                      |   |
                     |  |  +--------+  +--------+  +--------+       |   |
                     |  |  |Intent  |  |Semantic|  |Entity  |       |   |
                     |  |  |Agent   |  |Agent   |  |Agent   |       |   |
                     |  |  +--------+  +--------+  +--------+       |   |
                     |  |  +--------+  +--------+  +--------+       |   |
                     |  |  |Relation|  |Conflict|  |Confid. |       |   |
                     |  |  |Agent   |  |Agent   |  |Agent   |       |   |
                     |  |  +--------+  +--------+  +--------+       |   |
                     |  |  +--------+  +--------+                    |   |
                     |  |  |Evidence|  |Consens.|  (7 agents +      |   |
                     |  |  |Agent   |  |Agent   |   1 meta-agent)   |   |
                     |  |  +--------+  +--------+                    |   |
                     |  +--------------------------------------------+   |
                     |         |        |          |                     |
                     |         v        v          v                     |
                     |  +--------------------------------------------+   |
                     |  |           VOTING LAYER                     |   |
                     |  |  +----------------+  +-----------------+   |   |
                     |  |  | MajorityVoting |  | WeightedVoting  |   |   |
                     |  |  +----------------+  +-----------------+   |   |
                     |  |  +-----------------------------+           |   |
                     |  |  | ConfidenceWeightedVoting    |           |   |
                     |  |  +-----------------------------+           |   |
                     |  +--------------------------------------------+   |
                     |         |                                         |
                     |         v                                         |
                     |  +--------------------------------------------+   |
                     |  |      PLUGIN PROCESSING PIPELINE            |   |
                     |  |  (AgentPlugin instances transform results) |   |
                     |  +--------------------------------------------+   |
                     |         |                                         |
                     |         v                                         |
                     |  +--------------------------------------------+   |
                     |  |    AGREEMENT MATRIX CONSTRUCTION           |   |
                     |  |  (pairwise agreement between all agents)   |   |
                     |  +--------------------------------------------+   |
                     |         |                                         |
                     |         v                                         |
                     |  +--------------------------------------------+   |
                     |  |     CONFLICT RESOLUTION LAYER              |   |
                     |  |  +------------------------------------+   |   |
                     |  |  | DefaultConflictDetector:           |   |   |
                     |  |  | - agent_disagreement               |   |   |
                     |  |  | - low_confidence                   |   |   |
                     |  |  | - opposite_conclusion              |   |   |
                     |  |  | - missing_evidence                 |   |   |
                     |  |  | - contradictory_evidence           |   |   |
                     |  |  | - agent_warnings                   |   |   |
                     |  |  +------------------------------------+   |   |
                     |  +--------------------------------------------+   |
                     |         |                                         |
                     |         v                                         |
                     |  +--------------------------------------------+   |
                     |  |         CONSENSUS LAYER                   |   |
                     |  |  +------------------------------------+   |   |
                     |  |  | DefaultConsensusStrategy:          |   |   |
                     |  |  |  1. Compute vote result (via       |   |   |
                     |  |  |     configured VotingStrategy)     |   |   |
                     |  |  |  2. Compute conflict severity      |   |   |
                     |  |  |     penalty from conflict reports  |   |   |
                     |  |  |  3. Adjust confidence:             |   |   |
                     |  |  |     confidence * (1 - penalty*0.3) |   |   |
                     |  |  |  4. Override to uncertain if       |   |   |
                     |  |  |     severity_penalty > 0.7         |   |   |
                     |  |  +------------------------------------+   |   |
                     |  +--------------------------------------------+   |
                     |         |                                         |
                     |         v                                         |
                     |  +--------------------------------------------+   |
                     |  |        DEBATE SUMMARY                     |   |
                     |  |  (consensus decision, confidence,         |   |
                     |  |   agent results, conflicts, timing)       |   |
                     |  +--------------------------------------------+   |
                     +----------------------------------------------------+
```

## Layer Descriptions

### Agent Layer

The Agent Layer contains eight `CognitiveAgent` implementations, each responsible for evaluating question pair representations from a distinct analytical perspective. Agents are registered in an `AgentRegistry` singleton and are invoked sequentially by the `DebateEngine`. Each agent receives `SemanticRepresentation` for both questions, an optional `SemanticAssessment`, and an optional `ReasoningResult` from the upstream CRE. Each agent produces an `AgentResult` containing confidence, recommendation, evidence, and warnings.

Agent independence is a core architectural property: agents do not communicate with each other. Inter-agent synthesis happens exclusively through voting, agreement matrices, and conflict detection in downstream layers. This ensures reproducibility and eliminates emergent interaction effects.

### Voting Layer

The Voting Layer transforms `AgentResult` objects into `Vote` objects (excluding the `consensus_agent`). Votes are then processed by a `VotingStrategy` to produce a `ConsensusResult`. Three strategies are available:

- `MajorityVoting`: Counts votes per recommendation; highest count wins. Ties resolve to uncertain.
- `WeightedVoting`: Multiplies each agent's confidence by its configured weight; sums per recommendation.
- `ConfidenceWeightedVoting`: Sums confidence values per recommendation without additional weighting.

### Plugin Processing Pipeline

After voting, registered `AgentPlugin` instances may transform or augment `AgentResult` objects. Plugins have access to all upstream data (representations, assessment, reasoning result, and all agent results). New results generated by plugins are appended to the agent result list. Plugin failures are caught and logged without halting the debate.

### Conflict Resolution Layer

The `ConflictDetectionStrategy` analyzes all agent results and votes to produce `ConflictReport` objects. The `DefaultConflictDetector` identifies six conflict types:

1. `agent_disagreement`: Minority agents disagree with majority recommendation
2. `low_confidence`: Agent confidence below 0.4 threshold
3. `opposite_conclusion`: Agents arrive at directly opposing conclusions
4. `missing_evidence`: Agent produced no supporting or contradicting evidence
5. `contradictory_evidence`: Agent has both supporting and contradicting evidence
6. `agent_warnings`: Agent raised operational warnings

Each conflict type carries a severity score (0.0 to 1.0) and a list of implicated agents.

### Consensus Layer

The `ConsensusStrategy` combines voting results and conflict reports into a final `ConsensusResult`. The `DefaultConsensusStrategy`:

1. Delegates to the configured `VotingStrategy` for the base decision
2. Computes mean conflict severity penalty from all conflict reports
3. Adjusts confidence: `adjusted_confidence = vote_confidence * (1.0 - severity_penalty * 0.3)`
4. Overrides decision to `uncertain` if mean severity exceeds 0.7

## Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `DebateEngine` | Orchestrates the full debate pipeline; manages timing per stage |
| `AgentRegistry` | Singleton registry for agents and plugins; supports CRUD operations |
| `IntentAgent` | Evaluates question intent similarity from summaries and assessment |
| `SemanticAgent` | Evaluates semantic similarity using embeddings and concept overlap |
| `EntityAgent` | Analyzes entity overlap and conflicts between both questions |
| `RelationAgent` | Compares relationship structures and relational similarity |
| `ConflictAgent` | Detects conflicts in assessment and reasoning results |
| `ConfidenceAgent` | Analyzes confidence chain for over/under-confidence patterns |
| `EvidenceAgent` | Evaluates quality, balance, and deduplication of evidence |
| `ConsensusAgent` | Meta-agent; does not evaluate (consensus computed by engine) |
| `MajorityVoting` | Simple vote counting with tie resolution |
| `WeightedVoting` | Per-agent weight * confidence weighted decision |
| `ConfidenceWeightedVoting` | Confidence-as-weight decision |
| `DefaultConsensusStrategy` | Integrates voting + conflict penalty into final decision |
| `DefaultConflictDetector` | Detects all 6 conflict types from agent outputs |

## Data Flow Between Layers

```
SemanticRepresentation (A, B)
SemanticAssessment?
ReasoningResult?
         |
         v
   [Agent Layer]
   8 agents sequentially evaluate
         |
         v
   list[AgentResult]
         |
         v
   [Vote Builder]
   Excludes consensus_agent
   Creates list[Vote]
         |
         v
   [Plugin Pipeline]
   Optional transformations
         |
         v
   [Agreement Matrix Builder]
   Pairwise recommendation comparisons
         |
         v
   [Conflict Resolution Layer]
   DefaultConflictDetector
         |
         v
   list[ConflictReport]
         |
         v
   [Consensus Layer]
   DefaultConsensusStrategy
   (VotingStrategy + conflict penalty)
         |
         v
   ConsensusResult + DebateSummary
```

## Design Rationale

### Why Deterministic

Every agent in MADE is a pure function of its inputs. Given identical `SemanticRepresentation`, `SemanticAssessment`, and `ReasoningResult` inputs, every agent produces identical output. This property provides:

- **Reproducibility**: Every debate run produces identical results for identical inputs
- **Explainability**: Agent decisions can be traced through deterministic code paths
- **Testability**: 137 unit tests validate agent behavior without stochastic components
- **Debug Transparency**: Failures are deterministic and reproducible

### Why Multi-Agent

A single model or perspective cannot capture the full complexity of question pair analysis. Intent may match while semantics diverge; entities may overlap while relationships conflict. Multiple specialist agents allow:

- **Perspective Decomposition**: Each agent focuses on one cognitive dimension
- **Conflict Detection**: Disagreement between specialist perspectives reveals nuance
- **Confidence Calibration**: Cross-agent agreement provides implicit confidence signals
- **Graceful Degradation**: Agent failures are isolated and do not cascade

### Why Not LLM

The deliberate exclusion of LLMs from MADE is a research design choice:

- **Determinism**: LLM outputs are non-deterministic; MADE requires exact reproducibility
- **Cost**: 8 LLM agents per debate would introduce prohibitive per-query cost
- **Latency**: LLM inference would increase debate time by orders of magnitude
- **Hallucination**: Evidence generation requires factual faithfulness; LLM hallucination undermines this
- **Testability**: LLM-based agents cannot be unit-tested for exact output expectations

## Class Diagram

```
+----------------+       +------------------+
| CognitiveAgent |<------|  IntentAgent     |
| (ABC)          |       |  SemanticAgent   |
| + evaluate()   |       |  EntityAgent     |
| + name -> str  |       |  RelationAgent   |
| + weight -> f  |       |  ConflictAgent   |
+----------------+       |  ConfidenceAgent |
        ^                |  EvidenceAgent   |
        |                |  ConsensusAgent  |
        |                +------------------+
        |
+------------------+
| AgentPlugin      |
| (ABC)            |
| + process()      |
+------------------+
        ^
        |
+------------------+
| DefaultAgentPlugin|
+------------------+

+------------------+       +------------------+
| VotingStrategy   |<------| MajorityVoting   |
| (ABC)            |       | WeightedVoting   |
| + compute(votes) |       | ConfidenceWtVot. |
+------------------+       +------------------+

+----------------------+   +----------------------+
| ConsensusStrategy    |<--| DefaultConsensusStrat|
| (ABC)                |   | + voting_strategy    |
| + build(results,    |   +----------------------+
|     votes, conflicts)|
+----------------------+

+------------------------+ +------------------------+
| ConflictDetectionStrat | | DefaultConflictDetector|
| (ABC)                  | | + detect(results,     |
| + detect(results,     | |     votes)             |
|     votes)             | +------------------------+
+------------------------+

+------------------+       +------------------+
| ConfidenceAggr.  |<------| MeanAggregation  |
| (ABC)            |       | MinAggregation   |
| + aggregate(c,w) |       | MaxAggregation   |
+------------------+       | ProductAggregat. |
                           +------------------+

+------------------+       +------------------+
| DebateEngine     |       | AgentRegistry    |
| + registry       |       | + register()     |
| + consensus      |       | + unregister()   |
| + conflict_det   |       | + get()          |
| + debate()       |       | + get_all()      |
+------------------+       | + plugins        |
                           +------------------+

+------------------+       +------------------+
| AgentResult      |       | Vote             |
| + agent_name     |       | + agent_name     |
| + confidence     |       | + recommendation |
| + recommendation |       | + confidence     |
| + evidence       |       | + weight         |
| + warnings       |       +------------------+
+------------------+

+------------------+       +------------------+
| AgreementMatrix  |       | ConflictReport   |
| + matrix         |       | + conflict_type  |
| + get_agreement()|       | + agents         |
| + mean_agreement()|      | + description    |
+------------------+       | + severity       |
                           +------------------+
+------------------+       +------------------+
| ConsensusResult  |       | DebateResult     |
| + decision       |       | + agent_results  |
| + confidence     |       | + votes          |
| + vote_counts    |       | + agreement_mat  |
| + strategy_used  |       | + conflict_reps  |
| + weighted_vote  |       | + consensus      |
+------------------+       | + stages         |
                           +------------------+
```

## Extension Points

### Custom Agents
Implement `CognitiveAgent` ABC and register via `AgentRegistry.register()`. The agent's `name` property must return a unique string. The `evaluate()` method receives the full pipeline context.

### Custom Voting Strategies
Implement `VotingStrategy` ABC and inject into `DefaultConsensusStrategy` or directly into `DebateEngine` via consensus strategy configuration.

### Custom Conflict Detection
Implement `ConflictDetectionStrategy` ABC and set via `DebateEngine.set_conflict_detector()`.

### Custom Consensus Strategies
Implement `ConsensusStrategy` ABC and inject into `DebateEngine` constructor or via `set_consensus_strategy()`.

### Plugins
Implement `AgentPlugin` ABC. Plugins can transform, augment, or generate new agent results after initial evaluation. Register via `AgentRegistry.register_plugin()`.

## Future Research Directions

- **Adaptive Agent Weighting**: Learn optimal per-agent weights from historical debate outcomes
- **Hierarchical Debate**: Sub-debates on specific dimensions (entity-only, intent-only) feeding into main debate
- **Temporal Debate**: Track debate consistency across related query pairs over time
- **Probabilistic Conflict Modeling**: Replace fixed severity thresholds with learned conflict impact models
- **Agent Specialization Tuning**: Dynamic agent activation based on question domain or type detected upstream

## Limitations

- **Deterministic Bound**: Agents cannot learn from debate outcomes; no feedback loop exists
- **No Learning**: Weights, thresholds, and strategies are static and must be tuned externally
- **Fixed Strategies**: Only three voting strategies and one consensus strategy are provided
- **No Inter-Agent Communication**: Agents operate in isolation; no iterative debate or persuasion
- **Homogeneous Input**: All agents receive the same upstream data; there is no agent-specific information routing
- **Sequential Evaluation**: Agents evaluate sequentially rather than in parallel, though they are independent
