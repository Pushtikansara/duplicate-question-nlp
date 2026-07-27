# Decision Trace Examples

## Example 1: Exact Match, Simple Case

### Input
```
Q1: "How to install Python?"
Q2: "How to install Python?"
```

### Decision Trace Summary
```
Pipeline Version: 1.4.0
Processing Time: 0.35ms
Summary: Pair type: potential_paraphrase | Primary: exact_match | Complexity: Very Easy | Routed to: fast_lexical
Overall Confidence: 0.8923
Overall Risk: low
Overall Complexity: Very Easy
```

### Confidence Breakdown
| Stage | Confidence |
|-------|------------|
| Question Type | 0.9500 |
| Entity | 1.0000 |
| Relationship | 1.0000 |
| Complexity | 0.9500 |
| Routing | 1.0000 |
| **Overall** | **0.8923** |

## Example 2: Entity Replacement, Medium Complexity

### Input
```
Q1: "What is the GDP of France?"
Q2: "What is the GDP of Germany?"
```

### Decision Trace Summary
```
Pipeline Version: 1.4.0
Processing Time: 0.52ms
Summary: Pair type: same_type | Primary: entity_replacement | Complexity: Medium | Routed to: cross_encoder
Overall Confidence: 0.6245
Overall Risk: medium
Overall Complexity: Medium
```

### Routing Trace
```
Selected Strategy: cross_encoder
Strategy Scores:
  cross_encoder: 0.8500
  ensemble: 0.0000
  fast_lexical: 0.0000
  baseline: 0.0000
  fallback: 0.0000
Triggered Rules:
  - entity_dense: High entity density requiring cross-encoder (score=0.8500)
  - entity_conflict: Entity replacement detected (score=0.8000)
Rejected: fast_lexical, ensemble, baseline, fallback
```

## Example 3: Negation Change, High Complexity

### Input
```
Q1: "Is Python better than Java for machine learning?"
Q2: "Python is not better than Java for machine learning"
```

### Decision Trace Summary
```
Pipeline Version: 1.4.0
Processing Time: 0.89ms
Summary: Pair type: potential_paraphrase | Primary: negation_introduced | Complexity: Hard | Routed to: cross_encoder
Overall Confidence: 0.5421
Overall Risk: high
Overall Complexity: Hard
```

### Warnings
- Risk flag: meaning_changed
- High ambiguity detected
- Very high complexity

### Recommendations
- Consider ensemble for higher confidence
- Review complex comparison for edge cases

## Example 4: Empty Input

### Input
```
Q1: ""
Q2: ""
```

### Decision Trace Summary
```
Pipeline Version: 1.4.0
Processing Time: 0.12ms
Summary: No analysis data
Overall Confidence: 0.0000
Overall Risk: high
Overall Complexity: Very Easy
```

## Example 5: Cross-Lingual

### Input
```
Q1: "How to install Python?"
Q2: "Comment installer Python?"
```

### Decision Trace
```
Summary: Pair type: different_type | Primary: lexical_reformulation | Complexity: Medium | Routed to: cross_encoder
Triggered Rules:
  - cross_lingual: Cross-lingual pair needs cross-encoder
```
