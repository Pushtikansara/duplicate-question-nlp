# Relationship Analysis Engine

The Relationship Analysis Engine is a deterministic, rule-based module that analyzes **how** two questions differ. It operates independently from prediction, routing, and inference.

## Purpose

Instead of answering "are these questions duplicates?" this module answers:

- **HOW** do these questions differ?
- **WHY** do they differ?
- **WHAT** is the semantic distance between them?
- **WHETHER** differences are likely to change meaning?

## Architecture

```
Input: question_1, question_2
    │
    ▼
Layer 1 — Normalization
    │  (lowercase, NFKC, contraction expansion)
    ▼
Layer 2 — Token Comparison
    │  (edit distance, jaccard, overlap, exact/near match)
    ▼
Layer 3 — Phrase Comparison
    │  (word order, duplicate words, clause changes)
    ▼
Layer 4 — Entity Comparison
    │  (via EntityDetector)
    ▼
Layer 5 — Negation & Polarity
    │  (negation tokens, additions/removals)
    ▼
Layer 6 — Numeric & Temporal
    │  (versions, dates, times, currency, units, percentages)
    ▼
Layer 7 — Lexical Substitution
    │  (synonyms, antonyms, abbreviations, spelling, pronouns)
    ▼
Layer 8 — Synthesis
    │  (scoring, risk evaluation, semantic flags, transformation chain)
    ▼
Output: RelationshipAnalysis
```

## Key Properties

- **Deterministic**: Same inputs always produce same output
- **Explainable**: Every relationship includes evidence and reasoning
- **Modular**: Each layer is independently testable
- **Extensible**: New relationships and patterns can be added without modifying existing code
- **Production Ready**: <5ms average latency, no external dependencies, no LLM
- **Independent**: Operates before prediction, never modifies prediction results
