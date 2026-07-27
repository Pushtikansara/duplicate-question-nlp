# Decision Trace Schema

## Core Types

### DecisionTrace

| Field | Type | Description |
|-------|------|-------------|
| `pipeline_version` | `str` | Pipeline version identifier |
| `processing_time_ms` | `float` | Trace generation time in milliseconds |
| `summary` | `str` | One-line human-readable summary |
| `confidence` | `float` | Overall confidence (0-1) |
| `overall_risk` | `str` | Risk level ("low", "medium", "high") |
| `overall_complexity` | `str` | Difficulty level string |
| `question_type_trace` | `QuestionTypeTrace` | Question type explainability |
| `entity_trace` | `EntityTrace` | Entity detection explainability |
| `relationship_trace` | `RelationshipTrace` | Relationship analysis explainability |
| `complexity_trace` | `ComplexityTrace` | Complexity analysis explainability |
| `routing_trace` | `RoutingTrace` | Router decision explainability |
| `triggered_rules` | `list[str]` | All rule names that fired across pipeline |
| `rejected_rules` | `list[str]` | Strategies rejected during routing |
| `supporting_evidence` | `list[EvidenceDetail]` | All evidence across all layers |
| `confidence_breakdown` | `ConfidenceBreakdown` | Per-stage confidence values |
| `decision_path` | `DecisionPath` | Ordered flow of decisions |
| `warnings` | `list[str]` | Risk warnings |
| `recommendations` | `list[str]` | Suggested actions |
| `metadata` | `dict` | Additional context |

### EvidenceDetail

| Field | Type | Description |
|-------|------|-------------|
| `rule_name` | `str` | Name of the rule that fired |
| `rule_layer` | `int` | Processing layer number |
| `matched_pattern` | `str` | Pattern that was matched |
| `evidence_tokens` | `list[str]` | Tokens involved in evidence |
| `confidence` | `float` | Evidence confidence |
| `explanation` | `str` | Human-readable explanation |
| `affected_words` | `list[str]` | Words affected by this rule |
| `processing_layer` | `str` | Layer name |

### QuestionTypeTrace

| Field | Type | Description |
|-------|------|-------------|
| `question_1_type` | `str` | Classified type of Q1 |
| `question_2_type` | `str` | Classified type of Q2 |
| `pair_type` | `str` | Classified pair type |
| `confidence` | `float` | Classification confidence |
| `reason` | `str` | Classification reason string |
| `evidence` | `list[EvidenceDetail]` | Supporting evidence |
| `rules_fired` | `list[str]` | Rules triggered |

### EntityTrace

| Field | Type | Description |
|-------|------|-------------|
| `entity_count_q1` | `int` | Entities found in Q1 |
| `entity_count_q2` | `int` | Entities found in Q2 |
| `shared_count` | `int` | Matched entity pairs |
| `overlap_score` | `float` | Entity overlap score |
| `entity_relationship` | `str` | Entity relationship type |
| `confidence` | `float` | Entity analysis confidence |
| `evidence` | `list[EvidenceDetail]` | Entity extraction evidence |
| `rules_fired` | `list[str]` | Entity rules triggered |

### RelationshipTrace

| Field | Type | Description |
|-------|------|-------------|
| `relationship_count` | `int` | Number of relationships detected |
| `primary_relationship` | `str` | Highest-confidence relationship |
| `relationship_score` | `float` | Overall score (0-100) |
| `confidence` | `float` | Relationship confidence |
| `semantic_flags` | `list[str]` | Semantic interpretation flags |
| `risk_flags` | `list[str]` | Risk indicators |
| `evidence` | `list[EvidenceDetail]` | Relationship evidence |
| `rules_fired` | `list[str]` | Relationship rules triggered |

### ComplexityTrace

| Field | Type | Description |
|-------|------|-------------|
| `overall_score` | `float` | Overall complexity (0-1) |
| `difficulty_level` | `str` | Difficulty label |
| `lexical` | `float` | Lexical complexity |
| `syntactic` | `float` | Syntactic complexity |
| `semantic` | `float` | Semantic complexity |
| `entity_complexity` | `float` | Entity complexity |
| `ambiguity` | `float` | Ambiguity score |
| `readability` | `float` | Readability complexity |
| `comparison_difficulty` | `float` | Comparison difficulty |
| `confidence` | `float` | Complexity confidence estimate |
| `risk_score` | `float` | Complexity risk score |
| `reasoning` | `str` | Human-readable reasoning |
| `evidence` | `list[EvidenceDetail]` | Complexity evidence |
| `rules_fired` | `list[str]` | Complexity rules triggered |

### RoutingTrace

| Field | Type | Description |
|-------|------|-------------|
| `selected_strategy` | `str` | Winning strategy |
| `confidence` | `float` | Routing confidence |
| `risk_level` | `str` | Risk level for selected strategy |
| `priority` | `str` | Priority level |
| `strategy_scores` | `dict[str, float]` | Scores per strategy |
| `triggered_rules` | `list[dict]` | Rules that triggered |
| `rejected_rules` | `list[str]` | Strategies not selected |
| `reason_codes` | `list[str]` | Machine-readable reason codes |
| `evidence` | `list[EvidenceDetail]` | Routing evidence |

### ConfidenceBreakdown

| Field | Type | Description |
|-------|------|-------------|
| `question_type` | `float` | Question type confidence |
| `entity` | `float` | Entity analysis confidence |
| `relationship` | `float` | Relationship confidence |
| `complexity` | `float` | Complexity confidence |
| `routing` | `float` | Routing confidence |
| `overall` | `float` | Weighted overall confidence |

### DecisionPath

| Field | Type | Description |
|-------|------|-------------|
| `layers_traversed` | `list[str]` | Ordered layer names |
| `current_layer` | `str` | Active processing layer |
| `decision_flow` | `list[str]` | Human-readable decision steps |
