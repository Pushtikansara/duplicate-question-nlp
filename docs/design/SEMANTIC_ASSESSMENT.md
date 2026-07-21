# SemanticAssessment

## Purpose

`SemanticAssessment` is the unified output dataclass of the Semantic Intelligence Engine.
It captures every aspect of the comparison between two `SemanticRepresentation` objects.

All downstream ARES components (Cross Encoder, Decision Fusion, Explainability Engine)
consume ONLY this object.

## Structure

```
SemanticAssessment
├── semantic_similarity: float        # 0.0 – 1.0
├── concept_overlap: ConceptOverlap
│   ├── overlap_score: float
│   ├── shared_concepts: list[str]
│   ├── missing_in_a: list[str]
│   ├── missing_in_b: list[str]
│   ├── total_a: int
│   ├── total_b: int
│   └── detail: dict
├── entity_overlap: EntityOverlap
│   ├── overlap_score: float
│   ├── shared_entities: list[str]
│   ├── missing_in_a: list[str]
│   ├── missing_in_b: list[str]
│   ├── conflicts: list[str]
│   ├── total_a: int
│   ├── total_b: int
│   └── detail: dict
├── intent_similarity: IntentSimilarity
│   ├── score: float
│   ├── confidence: float
│   ├── reason: str
│   └── detail: dict
├── relation_similarity: RelationSimilarity
│   ├── score: float
│   ├── matching_relations: list[dict]
│   ├── missing_in_a: list[dict]
│   ├── missing_in_b: list[dict]
│   ├── total_a: int
│   ├── total_b: int
│   └── detail: dict
├── context_similarity: ContextSimilarity
│   ├── score: float
│   ├── domain_match: bool
│   ├── domain_a: str | None
│   ├── domain_b: str | None
│   ├── shared_context_keys: list[str]
│   ├── constraints_match: bool
│   └── detail: dict
├── conflicts: list[Conflict]
│   ├── conflict_type: str
│   ├── description: str
│   ├── severity: float
│   ├── source: str
│   └── detail: dict
├── supporting_evidence: list[EvidenceItem]
│   ├── category: str
│   ├── status: str
│   ├── message: str
│   ├── confidence: float
│   └── detail: dict
├── confidence: float
├── confidence_detail: dict
│   ├── raw_scores: dict
│   ├── weighted_scores: dict
│   └── weights: dict
├── recommendation: Recommendation  # DUPLICATE | NOT_DUPLICATE | UNCERTAIN
├── recommendation_reason: str
└── processing_metadata: ProcessingMetadata
    ├── processing_time_ms: float
    ├── stages: dict[str, float]
    └── components_used: list[str]
```

## Serialization

Every `SemanticAssessment` supports `.to_dict()` for JSON-compatible serialization.

## Conflict Types

| Type | Description | Default Severity |
|------|-------------|-----------------|
| `opposite_actions` | Actions contradict each other (install vs uninstall) | 0.9 |
| `domain_mismatch` | Domains differ | 0.7 |
| `contradictory_intent` | Intent summaries contradict | 0.85 |
| `low_semantic_confidence` | A representation has low confidence | 0.5 |

## Evidence Status Values

| Status | Meaning |
|--------|---------|
| `match` | Components agree |
| `mismatch` | Components disagree |
| `partial` | Partial agreement |
| `conflict` | Direct conflict detected |
| `warning` | Missing or incomplete information |
| `info` | Informational |
| `uncertain` | Cannot determine |
| `low_confidence` | Low confidence in this dimension |
