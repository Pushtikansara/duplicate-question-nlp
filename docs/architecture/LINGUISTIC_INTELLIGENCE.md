# Linguistic Intelligence Layer

## Overview

The Linguistic Intelligence Layer (LIL) is Phase 1.3 of the ARES architecture.
It sits between the Cognitive Perception Engine (Phase 1.2) and the future
Semantic Intelligence Engine (Phase 1.4).

## Architecture

```
Raw Text
    │
    ▼
┌─────────────────────────────┐
│  Cognitive Perception Engine│  (Phase 1.2)
│  - normalize()              │
│  - detect_language()        │
│  - tokenize()              │
│  - structural_analysis()    │
│  - linguistic_analysis()    │
│  - metadata()              │
└─────────────┬───────────────┘
              │ CognitiveRepresentation (partial)
              ▼
┌─────────────────────────────┐
│  Linguistic Intelligence    │  (Phase 1.3 — THIS LAYER)
│  Layer                      │
│                             │
│  ┌───────────────────────┐  │
│  │ LinguisticProfile     │  │
│  │ Builder               │  │
│  │                       │  │
│  │ • QuestionClassifier  │  │
│  │ • ComplexityAnalyzer  │  │
│  │ • KeywordExtractor    │  │
│  │ • DomainDetector      │  │
│  │ • ConfidenceEstimator │  │
│  │ • QualityMetrics      │  │
│  │ • EntityAdapter       │  │
│  │ • NegationAdapter     │  │
│  │ • IntentAdapter       │  │
│  │ • LexicalAdapter     │  │
│  └───────────────────────┘  │
└─────────────┬───────────────┘
              │ LinguisticProfile
              ▼
┌─────────────────────────────┐
│  CognitiveRepresentation    │
│  (with linguistic_profile)  │
└─────────────┬───────────────┘
              │
              ▼
     Future ARES Engines
     (Semantic, Reasoning, etc.)
```

## Design Principles

1. **Unified Profile**: All linguistic analyses are consolidated into a single
   `LinguisticProfile` object embedded in `CognitiveRepresentation`.

2. **No Direct Access**: Future engines MUST NOT call linguistic analyzers
   directly. They consume only `CognitiveRepresentation`.

3. **Plugin Architecture**: Every analyzer implements `BaseAnalyzer` interface.
   New analyzers are pluggable without modifying the pipeline.

4. **Dependency Injection**: The `LinguisticProfileBuilder` accepts all
   analyzers via constructor injection, making it fully testable.

5. **Adapter Pattern**: Existing `_linguistics` engines (entity, negation,
   intent, lexical) are wrapped through adapters — never duplicated.

## Files

| File | Purpose |
|------|---------|
| `profile.py` | LinguisticProfile data model (18 dataclasses) |
| `profile_builder.py` | Orchestrator that runs all analyzers |
| `question_classifier.py` | WH/yes-no/declarative/imperative classification |
| `complexity_analyzer.py` | Flesch scores, TTR, syntactic complexity |
| `keyword_extractor.py` | TF-based keyword scoring with position bonuses |
| `domain_detector.py` | Heuristic domain classification |
| `confidence_estimator.py` | Per-analyzer and holistic confidence |
| `quality_metrics.py` | Coverage, completeness, quality score |
| `adapters/perception_adapters.py` | Re-exports Phase 1.2 adapters |
| `plugins/__init__.py` | Plugin extension point directory |
