# Relationship Analysis Examples

## Exact Match

| Q1 | Q2 | Result |
|----|----|--------|
| How to install Python? | How to install Python? | `exact_match` (100) |
| What is AI? | What is AI? | `exact_match` (100) |

## Near Match (typos)

| Q1 | Q2 | Result |
|----|----|--------|
| How to instal Python? | How to install Python? | `near_match` (95) |
| What is programing? | What is programming? | `near_match` (95) |

## Punctuation / Formatting

| Q1 | Q2 | Result |
|----|----|--------|
| Hello World | Hello, World! | `punctuation_only` (85+) |
| Hello World | hello world | `capitalization_only` (95) |
| Hello  World | Hello World | `whitespace_only` (95) |

## Negation

| Q1 | Q2 | Result |
|----|----|--------|
| How to install Python? | How to not install Python? | `negation_introduced` (30) |
| How to not install Python? | How to install Python? | `negation_removed` (30) |

## Numeric / Version

| Q1 | Q2 | Result |
|----|----|--------|
| Python 3.8 | Python 3.9 | `version_difference` (50) |
| 10 items | 20 items | `numeric_difference` (50) |
| 50% | 75% | `percentage_difference` (50) |
| $10 | $20 | `currency_difference` (50) |

## Lexical

| Q1 | Q2 | Result |
|----|----|--------|
| How to begin? | How to start? | `synonym_replacement` (80) |
| Is it big? | Is it small? | `antonym_detection` (25) |
| What is AI? | What is Artificial Intelligence? | `abbreviation_expansion` (70+) |
| What color? | What colour? | `spelling_variant` (85) |
| How do I do this? | How do you do this? | `pronoun_replacement` (70+) |

## Entity Changes

| Q1 | Q2 | Result |
|----|----|--------|
| How to install? | How to install Ubuntu? | `entity_addition` (50) |
| Python vs Java | Python vs C++ | `entity_replacement` (42) |

## Multi-Relationship Examples

| Q1 | Q2 | Relationships |
|----|----|--------------|
| How to install Ubuntu? | How do I install Ubuntu Linux? | entity_addition, pronoun_replacement |
| What is NLP? | What is Natural Language Processing? | entity_replacement, abbreviation |
| How to fix this issue? | How to repair this problem? | synonym_replacement × 2 |

## Risk Detection

| Q1 | Q2 | Risk |
|----|----|------|
| How to do this? | How to not do this? | `meaning_changed` |
| Python 3.8 | Python 3.9 | `version_conflict` |
| 10 items | 20 items | `numeric_conflict` |
