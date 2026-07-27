# Query Understanding Architecture

*Version 1.0.0 — Phase 12.0*

---

## Purpose

The Query Understanding module is the perceptual front-end of the ARES inference system. Its sole responsibility is converting raw question pairs into structured semantic metadata before any prediction, routing, or reasoning occurs.

The module follows a strict principle: **understand, don't predict**. It computes no embeddings, calls no ML models, and makes no classification decisions. It produces metadata only.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Incoming Question Pair                    │
│              "How to learn Python?" / "Learn Python fast"    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     QueryPipeline.run()                      │
│                                                             │
│   ┌──────────┐   ┌──────────────┐   ┌─────────────────┐    │
│   │ Validate  │──▶│  Normalize   │──▶│ Feature Extract │    │
│   └──────────┘   └──────────────┘   └────────┬────────┘    │
│                                              │              │
│                                              ▼              │
│                               ┌─────────────────────────┐   │
│                               │   Metadata Generation   │   │
│                               └──────────┬──────────────┘   │
│                                          │                  │
│                                          ▼                  │
│                               ┌─────────────────────────┐   │
│                               │    QueryAnalysis         │   │
│                               │     (dataclass)          │   │
│                               └─────────────────────────┘   │
│                                          │                  │
│                                          ▼                  │
│                               ┌─────────────────────────┐   │
│                               │   Optional: Report      │   │
│                               └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌───────────────────────┐
              │   Structured Object   │
              │   JSON-serializable   │
              │   No prediction done  │
              └───────────────────────┘
```

---

## Module Layout

```
src/ares/query_understanding/
├── __init__.py              # Public API exports
├── query_models.py          # Data models (dataclasses)
├── query_features.py        # Feature extraction functions
├── query_analyzer.py        # Main analyzer orchestrator
├── query_pipeline.py        # Pipeline runner (validate → normalize → analyze)
├── query_report.py          # Human-readable report formatter
└── utils.py                 # Shared utilities (patterns, tokenization, language)
```

---

## Data Flow

### Step 1: Validation (`utils.validate_input`)
- Ensures both inputs are strings
- Allows empty strings (analysis will return minimal object)

### Step 2: Normalization (`utils.normalize_text`)
- Lowercases text
- Collapses whitespace
- Strips leading/trailing spaces
- Does NOT remove punctuation or stopwords

### Step 3: Feature Extraction (`query_features`)
- **Question Metadata**: length, word count, sentence count, language, content flags
- **Token Statistics**: unique tokens, token length distribution
- **Sentence Statistics**: sentence count, length distribution
- **Readability Metrics**: Flesch Reading Ease, syllable counts
- **Complexity Scores**: lexical, syntactic, technical, overall
- **Similarity Features**: overlap ratios, shared content types

### Step 4: Assembly (`QueryAnalyzer.analyze`)
- Calls all feature extractors
- Builds and returns a complete `QueryAnalysis` object

### Step 5: Reporting (optional, `QueryReport`)
- Formats the analysis into human-readable text
- Two modes: full report and short summary

---

## Design Principles

### Independence
- No imports from the prediction engine
- No ML model loading
- No embedding computation
- No external API calls

### Purity
- Deterministic output for same inputs
- No mutable global state
- All functions are stateless

### Robustness
- Handles empty, malformed, and non-string inputs
- Graceful fallbacks for missing features
- Unicode-safe throughout

### Extensibility
- New features can be added to `query_features.py` without touching other modules
- New analysis dimensions can be added as new dataclass fields
- The pipeline can be subclassed for custom ordering

---

## Future Extensions

The architecture is designed for these future additions:

- **Embedding-based similarity** (when needed, add as optional feature)
- **Intent classification** (add `intent` field to metadata)
- **Question type detection** (add `question_type` field)
- **Toxicity detection** (add `toxicity` field)
- **Abbreviation expansion** (integrate with existing preprocessing)
- **Multi-query batching** (already supported via `run_batch`)
- **Pluggable feature extractors** (DI pattern for custom extractors)
