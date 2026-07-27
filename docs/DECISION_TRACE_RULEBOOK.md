# Decision Trace Rulebook

## Overview

The Decision Trace Engine captures every rule that fires across all pipeline layers. Each rule produces evidence that explains what was detected and why.

## Layer 1: Question Type Rules

| Rule Name | Description | Evidence Produced |
|-----------|-------------|-------------------|
| `classify_q1:{type}` | Type classification for Q1 | Classification reason |
| `classify_q2:{type}` | Type classification for Q2 | Classification reason |
| `pair_analysis:{pair_type}` | Pair type determination | Pair classification reason |

## Layer 2: Entity Rules

| Rule Name | Description | Evidence Produced |
|-----------|-------------|-------------------|
| `entity_detected_q1:{type}:{text}` | Entity extracted from Q1 | Entity text, type, confidence |
| `entity_detected_q2:{type}:{text}` | Entity extracted from Q2 | Entity text, type, confidence |
| `entity_match:{match_type}:{text}` | Matched entity pair | Both texts, match type, similarity |

## Layer 3: Relationship Rules

| Rule Name | Description | Evidence Produced |
|-----------|-------------|-------------------|
| `rel:{relationship_type}:{confidence}` | Relationship detected | Evidence tokens, matched pattern |

Relationship types captured:
- `exact_match`, `near_match`, `capitalization_only`, `punctuation_only`, `whitespace_only`
- `word_order_change`, `sentence_structure_change`, `lexical_reformulation`
- `negation_introduced`, `negation_removed`, `double_negation`, `question_polarity_change`
- `entity_replacement`, `entity_addition`, `entity_removal`, `entity_reordering`
- `synonym_replacement`, `antonym_detection`, `pronoun_replacement`, `spelling_variant`
- `abbreviation_expansion`, `abbreviation_compression`, `acronym_match`
- `numeric_difference`, `version_difference`, `date_difference`, `time_difference`
- `currency_difference`, `percentage_difference`, `unit_difference`
- `duplicate_tokens`, `repeated_words`, `inserted_clause`, `removed_clause`

## Layer 4: Complexity Rules

| Rule Name | Description | Evidence Produced |
|-----------|-------------|-------------------|
| `complexity_{metric}` | Each complexity metric | Metric name and value |

Metrics captured:
- `lexical_complexity`, `syntactic_complexity`, `semantic_complexity`
- `entity_complexity`, `ambiguity_score`, `readability_score`
- `comparison_difficulty`

## Layer 5: Routing Rules

| Rule Name | Category | Description |
|-----------|----------|-------------|
| `exact_match_simple` | fast_path | Exact match with low complexity |
| `very_low_complexity` | fast_path | Very low overall complexity |
| `low_overlap_no_entities` | fast_path | Low overlap and no entities |
| `high_jaccard_low_complexity` | fast_path | High Jaccard with low complexity |
| `entity_dense` | cross_encoder | High entity density |
| `negation_conflict` | cross_encoder | Negation detected |
| `antonym_conflict` | cross_encoder | Antonym detected |
| `numeric_conflict` | cross_encoder | Numeric/version conflicts |
| `entity_conflict` | cross_encoder | Entity replacement |
| `date_conflict` | cross_encoder | Date/temporal conflicts |
| `high_ambiguity` | ensemble | High ambiguity |
| `high_risk` | ensemble | High risk score |
| `low_confidence` | ensemble | Low confidence estimate |
| `semantic_drift` | ensemble | High semantic drift |
| `complex_question` | cross_encoder | Very complex questions |
| `cross_lingual` | cross_encoder | Cross-lingual pair |
| `code_snippet` | cross_encoder | Code in questions |
| `very_short_exact` | baseline | Very short exact match |
| `high_overlap_baseline` | baseline | High overlap basic types |
| `fallback_default` | fallback | Unhandled cases |

## Evidence Detail Fields

Every piece of evidence includes:
- `rule_name`: Which rule triggered
- `rule_layer`: Layer number (1-5)
- `matched_pattern`: What pattern matched
- `evidence_tokens`: Token-level evidence
- `confidence`: Evidence confidence (0-1)
- `explanation`: Human-readable explanation of what was detected
- `affected_words`: Words directly involved
- `processing_layer`: Layer name

## Decision Path

The decision path tracks the flow through layers:
1. `question_type` → Classified pair type
2. `entity` → Entity counts and relationships
3. `relationship` → Primary relationship type
4. `complexity` → Difficulty level and score
5. `routing` → Final strategy selection
