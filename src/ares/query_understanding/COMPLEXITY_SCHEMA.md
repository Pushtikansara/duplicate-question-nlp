# ComplexityAnalysis Schema

## Dataclass Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `overall_complexity_score` | float | 0.0 | Weighted composite score [0, 1] |
| `difficulty_level` | str | "Very Easy" | Human-readable difficulty |
| `lexical_complexity` | float | 0.0 | Average token length & long-word ratio |
| `syntactic_complexity` | float | 0.0 | Sentence length complexity |
| `semantic_complexity` | float | 0.0 | Ratio of uncommon/rare words |
| `entity_complexity` | float | 0.0 | Entity density tiers |
| `ambiguity_score` | float | 0.0 | Pronouns, vague words, mixed case |
| `readability_score` | float | 0.0 | Inverse Flesch Reading Ease |
| `comparison_difficulty` | float | 0.0 | Overlap, entity delta, type mismatch |
| `rare_token_density` | float | 0.0 | Uncommon long-word ratio |
| `entity_density` | float | 0.0 | Entity count / word count |
| `numeric_density` | float | 0.0 | Numeric token ratio |
| `abbreviation_density` | float | 0.0 | All-caps token ratio |
| `sentence_complexity` | float | 0.0 | Multi-sentence penalty |
| `question_length_score` | float | 0.0 | Length-based complexity |
| `token_diversity` | float | 0.0 | Unique / total token ratio |
| `confidence_estimate` | float | 1.0 | 1.0 - weighted risk |
| `risk_score` | float | 0.0 | Composite risk indicator |
| `reasoning_summary` | str | "" | Natural language summary |
| `processing_time` | float | 0.0 | Milliseconds |
| `version` | str | "1.0.0" | Schema version |

## JSON Serialization

`ComplexityAnalysis.to_dict()` returns a flat dict. `ComplexityAnalysis.from_dict(d)` restores it.

## Nested in QueryAnalysis

```json
{
  "complexity_analysis": {
    "overall_complexity_score": 0.12,
    "difficulty_level": "Very Easy",
    "lexical_complexity": 0.05,
    ...
  }
}
```
