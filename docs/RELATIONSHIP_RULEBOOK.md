# Relationship Rulebook

## Layer 1: Normalization

Rules applied to both questions before comparison:

1. NFKC Unicode normalization
2. Lowercase conversion
3. Multi-space collapse
4. Contraction expansion (don't → do not, what's → what is, etc.)

## Layer 2: Token Comparison

| Rule | Condition | Confidence |
|------|-----------|------------|
| `exact_match` | Normalized text and tokens identical | 1.0 |
| `near_match` | Normalized edit distance < 0.15 | 0.85 |
| `capitalization_only` | Same text after lowercasing | 0.95 |
| `whitespace_only` | Same after stripping whitespace | 0.95 |
| `punctuation_only` | Same after removing punctuation | 0.90 |

## Layer 3: Phrase Comparison

| Rule | Condition | Confidence |
|------|-----------|------------|
| `word_order_change` | Same tokens, different order | 0.80 |
| `duplicate_tokens` | Repeated adjacent words in Q1 | 0.70 |
| `repeated_words` | Repeated adjacent words in Q2 | 0.70 |
| `inserted_clause` | Clause detected in Q2 not in Q1 | 0.60 |
| `removed_clause` | Clause in Q1 removed in Q2 | 0.60 |
| `sentence_structure_change` | Active/passive voice switch | 0.65 |
| `lexical_reformulation` | Jaccard > 0.5, different length | 0.60 |

## Layer 4: Entity Comparison

Delegates to `EntityDetector`. Detects:

- `entity_addition`: Entities in Q2 not in Q1
- `entity_removal`: Entities in Q1 not in Q2
- `entity_replacement`: Different entities in both
- `entity_reordering`: Same entities, different order

## Layer 5: Negation & Polarity

Uses negation word set. Detects:

| Rule | Condition | Confidence |
|------|-----------|------------|
| `negation_introduced` | Negation in Q2 only | 0.90 |
| `negation_removed` | Negation in Q1 only | 0.90 |
| `double_negation` | Both have 2+ negations | 0.80 |
| `question_polarity_change` | Different negation tokens | 0.75 |

## Layer 6: Numeric, Temporal, Units

| Rule | Condition | Confidence |
|------|-----------|------------|
| `numeric_difference` | Different numeric values | 0.85 |
| `version_difference` | Different version strings | 0.90 |
| `date_difference` | Different date values | 0.85 |
| `time_difference` | Different time values | 0.85 |
| `currency_difference` | Different currency amounts | 0.85 |
| `percentage_difference` | Different percentages | 0.85 |
| `unit_difference` | Different unit values or types | 0.80 |

## Layer 7: Lexical Substitution

| Rule | Condition | Confidence |
|------|-----------|------------|
| `synonym_replacement` | Word in synonym dictionary | 0.75 |
| `antonym_detection` | Word in antonym dictionary | 0.80 |
| `abbreviation_expansion` | Word in abbreviation map | 0.85 |
| `spelling_variant` | Word in spelling variant map | 0.85 |
| `pronoun_replacement` | Word in pronoun set | 0.70 |

## Layer 8: Synthesis

Combines all detected relationships into:

- **relationship_score** (0-100): Weighted combination of all relationships
- **semantic_flags**: Inferred semantic meaning
- **risk_flags**: Potential risks and conflicts
- **transformation_chain**: Step-by-step transformation from Q1 to Q2
