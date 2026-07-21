# Semantic Intelligence Engine (SIE)

## Overview

The Semantic Intelligence Engine (SIE) is Phase 2.0 of the ARES cognitive architecture.
It is the first component in the pipeline that compares two meanings rather than two strings.

SIE consumes exactly two `SemanticRepresentation` objects and produces a single `SemanticAssessment`.

## Position in Pipeline

```
Raw Text
    ↓
Perception Engine
    ↓
Linguistic Intelligence
    ↓
Semantic Knowledge Representation
    ↓
SemanticRepresentation
    ↓
Semantic Intelligence Engine  ←  HERE
    ↓
SemanticAssessment
    ↓
Cross Encoder
    ↓
Decision Fusion
```

## Core Principle

No component in SIE may access raw text directly.
Only `SemanticRepresentation` objects are consumed.
This ensures the engine operates purely on meaning rather than surface form.

## Architecture

SIE follows a modular, dependency-injected architecture with 10 sub-components:

| Component | Responsibility |
|-----------|---------------|
| ConceptMatcher | Compares normalized concepts, measures overlap, detects missing concepts |
| EntityMatcher | Compares entities, detects conflicts and missing entities |
| RelationMatcher | Compares semantic relations through normalized concept identities |
| IntentMatcher | Compares semantic intent, actions, and objects |
| ContextMatcher | Compares domain, context dictionaries, and constraints |
| ConflictDetector | Detects opposite actions, domain mismatch, contradictory intent |
| EvidenceBuilder | Generates structured, explainable evidence items |
| ConfidenceFusion | Computes holistic confidence from all intermediate scores |
| SemanticSimilarity | Computes overall semantic similarity |
| DecisionSupport | Produces final recommendation (DUPLICATE / NOT_DUPLICATE / UNCERTAIN) |

## Engineering

- SOLID principles throughout
- ABC interfaces for every component
- Dependency injection for testability
- Plugin architecture via the `plugins/` package
- Comprehensive type hints
- Dataclasses for all data objects
- Repository coding style

## Files

```
_semantic_intelligence/
    __init__.py
    interfaces.py
    engine.py
    semantic_assessment.py
    semantic_similarity.py
    concept_matcher.py
    entity_matcher.py
    relation_matcher.py
    intent_matcher.py
    context_matcher.py
    conflict_detector.py
    evidence_builder.py
    confidence_fusion.py
    decision_support.py
    plugins/
        __init__.py
```

## Output

`SemanticAssessment` contains:

- `semantic_similarity` — holistic similarity score
- `concept_overlap` — ConceptOverlap with shared/missing concepts
- `entity_overlap` — EntityOverlap with shared/missing/conflicting entities
- `intent_similarity` — IntentSimilarity with score, confidence, reason
- `relation_similarity` — RelationSimilarity with matching/missing relations
- `context_similarity` — ContextSimilarity with domain match status
- `conflicts` — list of detected conflicts
- `supporting_evidence` — list of structured evidence items
- `confidence` — holistic confidence score
- `confidence_detail` — per-component scores and weights
- `recommendation` — DUPLICATE, NOT_DUPLICATE, or UNCERTAIN
- `recommendation_reason` — human-readable explanation
- `processing_metadata` — timing and component usage
