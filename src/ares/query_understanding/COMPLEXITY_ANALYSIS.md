# Complexity Analysis Engine

## Overview

The Complexity Analysis Engine estimates how difficult it is to compare two questions. It uses deterministic rules and statistical measures — no ML, no LLMs, no external APIs — to produce a multi-dimensional complexity score in under 3ms.

## Architecture

### 8-Layer Analysis

1. **Question Statistics** — Length, character count, word count
2. **Lexical Statistics** — Token length distribution, rare word detection
3. **Readability** — Flesch Reading Ease score
4. **Entity Density** — Entity count relative to word count
5. **Relationship Complexity** — Number and type of detected relationships
6. **Ambiguity Estimation** — Pronouns, vague wording, short/incomplete questions
7. **Confidence Estimation** — Derived from ambiguity, rare tokens, entity conflicts
8. **Overall Synthesis** — Weighted combination of all sub-scores

### Scoring

Each dimension produces a score in [0.0, 1.0]. The overall score is a weighted average:

| Component | Weight |
|-----------|--------|
| Lexical Complexity | 0.15 |
| Syntactic Complexity | 0.10 |
| Semantic Complexity | 0.15 |
| Entity Complexity | 0.15 |
| Ambiguity Score | 0.15 |
| Readability Score | 0.10 |
| Comparison Difficulty | 0.20 |

### Difficulty Levels

| Score Range | Level |
|-------------|-------|
| < 0.10 | Very Easy |
| 0.10 – 0.24 | Easy |
| 0.25 – 0.44 | Medium |
| 0.45 – 0.64 | Hard |
| ≥ 0.65 | Very Hard |

## Integration

The `ComplexityAnalyzer` is automatically invoked by `QueryAnalyzer.analyze()`. The result is stored in `QueryAnalysis.complexity_analysis` as a `ComplexityAnalysis` dataclass.

```python
from ares.query_understanding import QueryAnalyzer

analyzer = QueryAnalyzer()
result = analyzer.analyze("What is Python?", "What is Java?")
ca = result.complexity_analysis
print(ca.difficulty_level)  # "Very Easy"
print(ca.overall_complexity_score)  # e.g. 0.12
```

## Performance

- Average runtime: < 1ms per pair
- No transformers, LLMs, or external APIs
- Pure Python deterministic computation
