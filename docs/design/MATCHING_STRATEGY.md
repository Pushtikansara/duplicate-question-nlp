# Matching Strategy

## Concept Matching

Concepts are compared using their `normalized_form` field.

```
normalized_form_a == normalized_form_b  →  match
```

This allows synonyms to match when they share the same normalized form
(e.g., "installing" → "INSTALL" matches "install" → "INSTALL").

**Score:** Jaccard-like overlap: `|shared| / |total|`

## Relation Matching

Relations are matched through normalized concept identities:

1. Build a mapping: `concept_id → normalized_form`
2. Create relation signatures: `(source_normalized, relation_type, target_normalized)`
3. Compare signature sets between A and B

**Example:**
```
A: INSTALL acts_on PYTHON  →  (INSTALL, acts_on, PYTHON)
B: SETUP acts_on PYTHON     →  (SETUP, acts_on, PYTHON)
// No match — different source concepts
```

**With normalization:**
```
A: INSTALL acts_on PYTHON      →  (INSTALL, acts_on, PYTHON)
B: INSTALL_ALT acts_on PYTHON  →  (INSTALL, acts_on, PYTHON)
// Match! Both normalize to same signature
```

## Entity Matching

Entities are matched by lowercase name after stripping whitespace.

Entity type conflicts are flagged when the same name has different types.

**Score:** Jaccard-like overlap: `|shared| / |total|`

## Intent Matching

Intents are compared using:

1. **Intent summary** — exact match gives 1.0, substring gives 0.8, else 0.2
2. **Actions** — shared actions boost score by 0.15 each
3. **Objects** — shared objects boost score by 0.10 each

Final score is clamped to `[0.0, 1.0]`.

## Context Matching

Three components weighted equally:

- **Domain match (40%)** — exact domain match
- **Key overlap (30%)** — shared context dictionary keys
- **Value agreement (30%)** — matching values for shared keys

Constraints are measured separately via Jaccard overlap.

## Conflict Detection

### Opposite Action Pairs

A curated dictionary of 35+ opposite action pairs:

```
install ↔ uninstall
create ↔ delete
enable ↔ disable
start ↔ stop
...
```

### Contradictory Intent Detection

Checks if intent summaries contain opposite words while sharing context.

### Low Confidence Detection

Flags representations with `semantic_confidence < 0.3`.

## Confidence Fusion

Five dimensions with configurable weights:

| Dimension | Default Weight |
|-----------|---------------|
| concept_similarity | 0.25 |
| intent_similarity | 0.25 |
| relation_similarity | 0.20 |
| entity_similarity | 0.15 |
| context_similarity | 0.15 |

Weights are normalized to sum to 1.0 if they don't already.

## Decision Support

Recommendations use two thresholds:

- **duplicate_threshold** (default: 0.7) — effective similarity above this → DUPLICATE
- **uncertain_threshold** (default: 0.4) — effective similarity below this → NOT_DUPLICATE
- Between thresholds → UNCERTAIN

Effective similarity is reduced by conflict severity: `sim * (1.0 - max_conflict_severity * 0.5)`
