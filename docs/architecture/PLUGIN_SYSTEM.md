# Plugin System

## Overview

The Linguistic Intelligence Layer uses a simple interface-based plugin
architecture. Every analyzer implements an abstract base class (ABC),
making them interchangeable and testable in isolation.

## Analyzer Interface

Every analyzer in the system follows this pattern:

```python
from abc import ABC, abstractmethod

class SomeAnalyzer(ABC):
    @abstractmethod
    def analyze(self, text: str) -> SomeResult:
        ...
```

## Current Analyzers

| Analyzer | Interface | Default Implementation | Input | Output |
|----------|-----------|----------------------|-------|--------|
| QuestionClassifier | `QuestionClassifier` | `DefaultQuestionClassifier` | `text: str` | `(question_type, question_class, confidence)` |
| ComplexityAnalyzer | `ComplexityAnalyzer` | `DefaultComplexityAnalyzer` | `text: str` | `(TokenStats, SentenceStats, Complexity, Readability)` |
| KeywordExtractor | `KeywordExtractor` | `DefaultKeywordExtractor` | `text: str` | `(keywords, scores, lexical_features)` |
| DomainDetector | `DomainDetector` | `DefaultDomainDetector` | `text: str` | `(domain, confidence)` |
| ConfidenceEstimator | `ConfidenceEstimator` | `DefaultConfidenceEstimator` | `profile: LinguisticProfile` | `AnalysisConfidence` |
| QualityMetrics | `QualityMetrics` | `DefaultQualityMetrics` | `profile, latency_ms` | `QualityMetricsData` |

## Wiring

The `LinguisticProfileBuilder` accepts all analyzers via constructor injection:

```python
builder = LinguisticProfileBuilder(
    entity_adapter=my_custom_entity_adapter,
    question_classifier=my_custom_classifier,
    complexity_analyzer=my_custom_complexity,
    ...
)
```

## Adding a New Analyzer

1. Create an ABC in a new file under `_linguistic_intelligence/`
2. Implement the default version
3. Add the analyzer to `LinguisticProfileBuilder.build()` method
4. Add its results to the `LinguisticProfile` dataclass
5. Create unit tests
6. Update quality metrics to account for the new analyzer

## Plugin Discovery

The `PluginLoader` from Phase 1.2 supports scanning directories for
plugin modules. Future analyzers can be loaded dynamically from
the `plugins/` directory.
