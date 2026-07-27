# Semantic Validation — Phase 10.5.5

## Module

`ares/inference/semantic_validator.py` — post-inference reasoning layer.

## Detection Logic

| Pattern | Detection | Penalty |
|---------|-----------|---------|
| Same entity, different disambiguating context | `_detect_same_entity_different_context` | 0.35 |
| Entity overlap (both questions share an entity word) | `_count_entity_overlap` | 0.10 |
| Polyseme presence | `_is_likely_polyseme` | 0.25 |
| **Maximum penalty** | capped at | 0.50 |

## Recognized Ambiguous Entities

python (programming_language/snake)
java (programming_language/island/coffee)
apple (company/fruit)
amazon (company/rainforest/river)
windows (operating_system/building_feature)
git (version_control/slang)
ruby (programming_language/gemstone)
go (programming_language/verb)
rust (programming_language/corrosion)
coral (reef_organism/color)
iris (flower/eye_part/dataset)
titanic (ship/dataset/movie)

## Example

```
Q1: "Python programming"
Q2: "Python snake"
→ Same entity "python" but different context
→ Confidence reduced by 0.35
→ Recommend human review
```

## Integration

Runs after prediction (Phase 2.5 in demo pipeline):
1. Incoming q1, q2 checked against entity map
2. Penalty computed if ambiguity detected
3. `adjusted_confidence` used in reflection
4. Result stored in `prediction_result.semantic_validation`

## Non-Goals

- No model retraining
- No weight modification
- No retraining data
