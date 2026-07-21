# LinguisticProfile

## Purpose

`LinguisticProfile` is the unified rich linguistic profile embedded into
`CognitiveRepresentation`. It answers all language understanding questions
that future ARES engines need without calling analyzers directly.

## Structure

```
LinguisticProfile
│
├── language: str                    # Detected language
├── language_confidence: float       # Confidence in detection
├── intent: str | None               # "installation", "definition", etc.
├── intent_confidence: float
├── question_type: str | None        # "wh-how", "yes-no", "declarative"
├── question_class: str | None       # "tutorial", "comparison", etc.
├── entities: list[dict]             # Detected entities with types
├── entity_count: int
├── keywords: list[Keyword]          # Scored keywords
├── keyword_scores: dict[str, float] # Quick lookup map
├── negation: bool                    # Negation present?
├── negation_count: int
├── contradiction: bool
├── contradiction_score: float
│
├── lexical_features
│   ├── lexical_density: float
│   ├── lexical_diversity: float
│   ├── noun_count, verb_count
│   ├── unique_nouns, unique_verbs
│   └── ...
│
├── token_statistics
│   ├── total, unique
│   ├── type_token_ratio
│   ├── avg_token_length
│   └── ...
│
├── sentence_statistics
│   ├── total, avg/min/max length
│   ├── question_sentences
│   └── exclamatory_sentences
│
├── complexity: ComplexityScore
│   ├── overall: float               # 0-1
│   ├── vocabulary_complexity
│   ├── syntactic_complexity
│   ├── flesch_reading_ease
│   ├── avg_sentence_words
│   └── ...
│
├── readability: ReadabilityScore
│   ├── flesch_reading_ease
│   ├── flesch_kincaid_grade
│   ├── coleman_liau_index
│   └── avg
│
├── domain: str | None
│   ├── domain_confidence: float
│   └── "programming", "data-science", etc.
│
├── quality_metrics
│   ├── coverage: float              # % analyzers with results
│   ├── completeness: float          # % fields populated
│   ├── quality_score: float         # Holistic score
│   ├── latency_ms
│   ├── warnings, errors
│   └── ...
│
├── analysis_confidence
│   ├── overall: float
│   ├── per_analyzer: dict[str, float]
│   └── ...
│
└── metadata: dict                   # Extensibility
```

## Quality Score

The quality score is computed as:
```
quality = coverage × 0.3 + completeness × 0.3 + confidence × 0.4
```

Where:
- **coverage**: How many of 7 analyzer categories produced results
- **completeness**: How many of 10 tracked fields are populated
- **confidence**: Overall analysis confidence (defaults to 0.5 minimum)
