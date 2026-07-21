# Linguistic Pipeline

## Pipeline Flow

```
Input Text
    │
    ▼
┌──────────────────────────────────────────────────┐
│  validate()                                       │
│  normalize()                                      │
│  detect_language()                                │
│  tokenize()                                       │
│  structural_analysis()                            │
│  linguistic_analysis()                            │
│  metadata()                                       │
│  ─────────────────────────────────────────────    │
│  ▶ linguistic_intelligence()    ← NEW             │
│    │                                              │
│    ├── IntentAdapter.detect()                     │
│    ├── EntityAdapter.extract()                    │
│    ├── NegationAdapter.detect()                   │
│    ├── KeywordExtractor.extract()                 │
│    ├── QuestionClassifier.classify()              │
│    ├── ComplexityAnalyzer.analyze()               │
│    ├── DomainDetector.detect()                    │
│    ├── ConfidenceEstimator.estimate()             │
│    └── QualityMetrics.evaluate()                  │
│  ─────────────────────────────────────────────    │
│  assemble()  ← LinguisticProfile embedded         │
└──────────────────────────────────────────────────┘
    │
    ▼
CognitiveRepresentation
  ├── raw_text
  ├── normalized_text
  ├── language, language_confidence
  ├── tokens, sentences
  ├── linguistic (shallow features)
  ├── metadata
  ├── validation
  ├── linguistic_profile  ← NEW: rich profile
  ├── pipeline_version = "1.1.0"
  └── processing_time_ms
```

## Stage Timing

Each pipeline stage is timed independently and reported in
`PipelineResult.stages`:

```python
result.stages = {
    "validate": 0.12,       # ms
    "normalize": 0.45,      # ms
    "detect_language": 0.08,
    "tokenize": 0.15,
    "structural_analysis": 0.22,
    "linguistic_analysis": 0.31,
    "metadata": 0.05,
    "linguistic_intelligence": 3.21,  # ← added
}
```

## Backward Compatibility

- The `linguistic_profile` field on `CognitiveRepresentation` defaults to `None`
- All Phase 1.2 tests pass unchanged
- The Per-Engine adapter pattern ensures existing `_linguistics` modules are
  wrapped, not duplicated
- `pipeline_version` bumped from `1.0.0` to `1.1.0`
