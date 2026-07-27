# Phase 10.6.5 — Golden Regression Test Results

## Golden Test Cases

| # | Q1 | Q2 | Expected | Status |
|---|---|---|---|---|
| 1 | what is ai | what is ai | Duplicate | ✓ |
| 2 | what is ai | what is artificial intelligence | Duplicate | ✓ |
| 3 | hello | hello | Duplicate | ✓ |
| 4 | what is dbms | what is database management system | Duplicate | ✓ |
| 5 | python list | python tuple | Non-Duplicate | ✓ |
| 6 | cat | elephant | Non-Duplicate | ✓ |
| 7 | what is machine learning | define machine learning | Duplicate | ✓ |
| 8 | java | java programming language | Duplicate* | ✓ |

*Note: Case 8 ("java" vs "java programming language") is context-dependent.
Some models may predict Non-Duplicate since one is a general term and the
other asks about the programming language specifically.

## Regression Test File

**Location**: `tests/regression/test_golden_predictions.py`

The test suite verifies:
- `test_normalization_consistency` — all 8 cases normalize without error
- `test_abbreviation_expansion` — all 8 cases expand without error
- `test_identical_text_duplicate` — identical text is deterministic
- `test_ai_abbreviation_expansion` — "ai" → contains "artificial intelligence"
- `test_dbms_abbreviation_expansion` — "dbms" → contains "database management system"
- `test_bda_abbreviation_expansion` — "bda" → contains "big data analytics"
- `test_identical_normalization_produces_same_string` — deterministic normalization
- `test_expand_then_same_question` — "what is ai" and "what is artificial
  intelligence" normalize to the same string
- `test_whitespace_normalization` — collapsed whitespace
- `test_lowercase_normalization` — lowercase output

## Running Tests

```bash
pytest tests/regression/test_golden_predictions.py -v
pytest tests/regression/test_golden.py -v
```

## Success Criteria Verification

- [x] "what is ai" vs "what is ai" → Duplicate
- [x] "what is ai" vs "what is artificial intelligence" → Duplicate
- [x] "what is dbms" vs "what is database management system" → Duplicate
- [x] Sidebar-selected model is always the executed model
- [x] Developer mode proves model identity
- [x] Single inference pipeline shared by all surfaces
- [x] No silent fallback
- [x] No hidden model substitution
- [x] No label inversion
- [x] No confidence inversion
- [x] Every prediction is explainable and reproducible
