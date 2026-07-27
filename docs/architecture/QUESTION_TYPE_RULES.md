# Question Type Rules

*Version 1.0.0 — Phase 12.1*

---

## Detection Strategy

The rule engine uses a three-tier detection approach:

1. **Special pre-checks** — code, numeric, temporal (high-priority, early exit)
2. **Pattern matching** — all 19 types checked via regex patterns in priority order
3. **First word analysis** — fallback for questions starting with known interrogative words

Each tier adds candidates to a scored list. The highest-scoring candidate wins. Ties are resolved by a preferred type ordering.

---

## Pre-Check Rules

### Code Detection

```
if contains_code(raw):
    + troubleshooting keywords (fix, debug, error)  → troubleshooting  (0.85)
    + how-to keywords (write, create, implement)     → how_to           (0.75)
    otherwise                                        → code             (0.90)
if code-related keywords (function, class, api, etc) → code             (0.60)
```

### Numeric Detection

```
if how_many/much/long/far/old/often → numeric (0.85)
if contains_number + price/cost/count/amount keywords → numeric (0.75)
if "what is the price/cost/number..." → numeric (0.80)
```

### Temporal Detection

```
if contains_date:
    + starts with "when" → temporal (0.90)
    otherwise            → temporal (0.70)
if "what time"          → temporal (0.75)
```

---

## Pattern Matching Rules

Each question type has a set of regex patterns. When a pattern matches, a base score is assigned and adjusted:

### Score Adjustments

| Condition | Adjustment |
|---|---|
| Matched text >30% of total length | +0.10 |
| Matched text <5% of total length | -0.15 |
| Yes/No question without `?` | -0.20 |
| Recommendation + comparison signal present (vs, difference) | -0.25 |
| Comparison + comparison signal present | +0.10 |
| Mutually exclusive type also matches | -0.30 |

### Type-Specific Patterns

| Type | Key Patterns | Base Score |
|---|---|---|
| definition | `what is`, `define`, `what does X mean` | 0.75 |
| how_to | `how to`, `how do/does/can`, `way to`, `tutorial`, `guide` | 0.80 |
| comparison | `difference between`, `vs`, `compare`, `contrast`, `pros and cons` | 0.85 |
| explanation | `explain`, `what does X do`, `how does X work`, `what happens when` | 0.70 |
| reason_why | `why`, `what causes`, `how come`, `what is the reason` | 0.85 |
| opinion | `do you think`, `in your opinion`, `is it worth`, `should` | 0.80 |
| factoid | `who invented`, `who is/was`, `what year`, `what is the population` | 0.75 |
| yes_no | starts with `is/are/do/does/can/will` | 0.60 |
| numeric | `how many/much`, `what is the price/cost/number` | 0.80 |
| temporal | starts with `when`, `what time/date/year` | 0.80 |
| location | `where`, `what place/city/country` | 0.80 |
| person | `who`, `whom`, `what person/name/author` | 0.80 |
| organization | `what company/organization/university` | 0.70 |
| procedure | `what are the steps`, `process of`, `procedure for`, `algorithm for` | 0.75 |
| recommendation | `what is the best`, `which X should`, `recommend`, `suggest` | 0.80 |
| troubleshooting | `fix/solve/debug`, `error/bug/issue`, `not working`, `crash` | 0.85 |
| code | `def/class/import`, `function/variable/syntax` | 0.90 (direct), 0.60 (related) |
| list | `list`, `what are the types/kinds`, `name the`, `enumerate` | 0.75 |

---

## First Word Rules

When pattern matching produces no candidates, first-word rules provide fallback:

| First Word | Assigned Type | Confidence | Condition |
|---|---|---|---|
| what | definition | 0.65 | ≤8 clean tokens |
| what | explanation | 0.50 | >8 clean tokens |
| how | how_to | 0.75 | - |
| why | reason_why | 0.85 | - |
| is/are/do/does/can/will | yes_no | 0.60 | - |
| when | temporal | 0.80 | - |
| where | location | 0.80 | - |
| who | person | 0.80 | - |
| which | organization | 0.75 | + org keyword |
| which | organization | 0.45 | ambiguous |

---

## Tie Resolution

When multiple candidates have scores within 0.05 of each other, a preferred ordering breaks the tie:

1. code
2. troubleshooting
3. comparison (boosted if `vs`/`difference` present)
4. reason_why
5. yes_no
6. how_to
7. temporal
8. location
9. person
10. numeric
11. recommendation
12. opinion
13. factoid
14. definition
15. procedure
16. explanation
17. list
18. organization
19. other

---

## Mutually Exclusive Types

Some type combinations cannot co-occur and trigger score penalties:

| Type | Conflicts With |
|---|---|
| yes_no | definition, numeric, temporal, location, list |
| opinion | definition, factoid, numeric |
| list | yes_no, opinion |

---

## Complementary Pair Mappings

Used by pair analysis to detect semantically related question pairs:

```
definition ↔ how_to, explanation, procedure
how_to ↔ definition, troubleshooting, procedure, explanation
explanation ↔ definition, how_to, reason_why
reason_why ↔ explanation, troubleshooting
comparison ↔ recommendation
troubleshooting ↔ how_to, reason_why, explanation
code ↔ how_to, troubleshooting, definition, explanation
factoid ↔ definition, temporal, location, person
procedure ↔ how_to, definition, explanation
```
