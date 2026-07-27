# Complexity Analysis Examples

## Example 1: Very Easy Comparison

**Questions:** "What is Python?" vs "What is Java?"

```python
overall_complexity_score = 0.12
difficulty_level = "Very Easy"
lexical_complexity = 0.05
syntactic_complexity = 0.0
semantic_complexity = 0.25
entity_complexity = 0.0
ambiguity_score = 0.0
readability_score = 0.0
comparison_difficulty = 0.3
confidence_estimate = 1.0
risk_score = 0.12
```

## Example 2: Hard Comparison

**Questions:** "How does the implementation of gradient descent with momentum compare to Adam optimizer in deep learning?" vs "What are the key differences between supervised and unsupervised machine learning approaches for classification?"

```python
overall_complexity_score = 0.52
difficulty_level = "Hard"
lexical_complexity = 0.35
syntactic_complexity = 0.4
semantic_complexity = 0.72
entity_complexity = 0.0
ambiguity_score = 0.0
readability_score = 0.2
comparison_difficulty = 0.3
confidence_estimate = 0.94
risk_score = 0.12
```

## Example 3: Abbreviation-Heavy

**Raw text:** "What is the difference between AI, ML, NLP, and CNN?"

```python
from ares.query_understanding.complexity_rules import abbreviation_density
tokens = ["What", "is", "the", "difference", "between", "AI", "ML", "NLP", "and", "CNN"]
abbreviation_density(tokens)  # 0.3 (3/10 uppercase tokens)
```

## Example 4: Ambiguous

**Questions:** "What is it?" vs "How does this work?"

```python
ambiguity_score = 0.15  # pronouns detected
```

## Example 5: Entity-Heavy

With 8 entities across 2 short questions:

```python
entity_complexity = 1.0    # density > 0.5
entity_density = 1.0       # 8 entities / 2 words
```

## Example 6: Numeric-Heavy

**Questions:** "Compare 42 with 100 and 3.14 with 2.718" vs "What is 7 * 8 + 3?"

```python
numeric_density = 0.23
```

## Example 7: Very Short

**Questions:** "A?" vs "B?"

```python
question_length_score = 0.1  # both ≤ 10 chars
ambiguity_score = 0.15       # very short questions
```

## Example 8: Very Long

200+ character questions:

```python
question_length_score = 1.0  # > 150 chars
```
