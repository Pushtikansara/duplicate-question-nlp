# Relationship Analysis Schema

## Core Types

### RelationshipInfo

| Field | Type | Description |
|-------|------|-------------|
| `relationship_type` | `str` | One of 39 supported relationship types |
| `confidence` | `float` | 0–1 confidence score |
| `evidence` | `list[Evidence]` | Rule evidence supporting detection |
| `human_explanation` | `str` | Human-readable explanation |
| `developer_explanation` | `str` | Developer-oriented explanation |

### Evidence

| Field | Type | Description |
|-------|------|-------------|
| `rule_name` | `str` | Name of the rule that fired |
| `rule_layer` | `int` | Layer number (1-8) |
| `matched_pattern` | `str` | Pattern that matched |
| `tokens_q1` | `list[str]` | Tokens from Q1 involved |
| `tokens_q2` | `list[str]` | Tokens from Q2 involved |
| `confidence` | `float` | Evidence confidence |

### TransformationChain

| Field | Type | Description |
|-------|------|-------------|
| `steps` | `list[TransformationStep]` | Ordered transformation steps |
| `final_intent` | `str` | `"equivalent"` or `"different"` |
| `is_equivalent` | `bool` | Whether questions are semantically equivalent |

### TransformationStep

| Field | Type | Description |
|-------|------|-------------|
| `step_type` | `str` | Type of transformation |
| `description` | `str` | Human-readable description |
| `tokens_q1` | `list[str]` | Source tokens (optional) |
| `tokens_q2` | `list[str]` | Target tokens (optional) |
| `confidence` | `float` | Step confidence |

### ComparisonStatistics

| Field | Type | Description |
|-------|------|-------------|
| `token_count_q1` | `int` | Token count for Q1 |
| `token_count_q2` | `int` | Token count for Q2 |
| `char_count_q1` | `int` | Character count for Q1 |
| `char_count_q2` | `int` | Character count for Q2 |
| `token_overlap` | `int` | Number of shared tokens |
| `token_overlap_ratio` | `float` | Overlap / min(len(q1), len(q2)) |
| `edit_distance` | `int` | Levenshtein distance |
| `normalized_edit_distance` | `float` | Edit distance / max length |
| `jaccard_similarity` | `float` | Jaccard similarity on tokens |
| `length_difference` | `int` | |len(t1) - len(t2)| |
| `shared_token_ratio` | `float` | Shared tokens / min sets |

### RelationshipAnalysis

| Field | Type | Description |
|-------|------|-------------|
| `relationship_types` | `list[RelationshipInfo]` | All detected relationships |
| `relationship_score` | `float` | Overall similarity score (0-100) |
| `relationship_confidence` | `float` | Overall confidence (0-1) |
| `relationship_summary` | `str` | One-line summary |
| `semantic_flags` | `list[str]` | Semantic interpretation flags |
| `risk_flags` | `list[str]` | Risk indicators |
| `transformation_chain` | `TransformationChain` | Step-by-step transformation |
| `comparison_statistics` | `ComparisonStatistics` | Text comparison stats |
| `processing_time` | `float` | Milliseconds to compute |
| `version` | `str` | Schema version |

## Derived Scores

- **primary_relationship()**: Highest-confidence relationship type
- **risk_score()**: 0–100 based on risk flags
- **semantic_distance()**: 0–100 based on relationship types and score
