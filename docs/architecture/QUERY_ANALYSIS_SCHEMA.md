# Query Analysis Schema

*Version 1.0.0 — Phase 12.0*

---

## Purpose

Defines the data model produced by the Query Understanding module. Every incoming question pair is transformed into a `QueryAnalysis` object containing structured metadata about both questions and their relationship.

The schema is independent of the prediction engine. It exists solely to describe the input.

---

## Root Object: `QueryAnalysis`

| Field | Type | Description |
|---|---|---|
| `original_question_1` | `str` | Raw input as received |
| `original_question_2` | `str` | Raw input as received |
| `normalized_question_1` | `str` | Lowercased, whitespace-collapsed |
| `normalized_question_2` | `str` | Lowercased, whitespace-collapsed |
| `metadata_1` | `QuestionMetadata` | Per-question properties |
| `metadata_2` | `QuestionMetadata` | Per-question properties |
| `similarity` | `QuestionSimilarityFeatures` | Cross-question comparison |
| `token_stats_1` | `TokenStatistics` | Token-level distribution |
| `token_stats_2` | `TokenStatistics` | Token-level distribution |
| `sentence_stats_1` | `SentenceStatistics` | Sentence-level distribution |
| `sentence_stats_2` | `SentenceStatistics` | Sentence-level distribution |
| `readability_1` | `ReadabilityMetrics` | Flesch Reading Ease and syllable data |
| `readability_2` | `ReadabilityMetrics` | Flesch Reading Ease and syllable data |
| `complexity_1` | `ComplexityScore` | Multi-axis complexity (lexical, syntactic, semantic, technical) |
| `complexity_2` | `ComplexityScore` | Multi-axis complexity (lexical, syntactic, semantic, technical) |
| `confidence` | `float` | Always 1.0 (no ML confidence applied) |
| `timestamp` | `str` | ISO 8601 UTC timestamp |
| `processing_time_ms` | `float` | Wall-clock time in milliseconds |
| `version` | `str` | Schema version (`"1.0.0"`) |

---

## Sub-Objects

### `QuestionMetadata`

| Field | Type | Description |
|---|---|---|
| `length` | `int` | Character count of normalized text |
| `char_count` | `int` | Same as `length` |
| `word_count` | `int` | Token count (whitespace-split) |
| `sentence_count` | `int` | Sentence count (split on `.!?`) |
| `avg_word_length` | `float` | Mean characters per word |
| `language` | `str` | Detected language code (`"en"`, `"es"`, `"fr"`, `"de"`, `"zh"`, `"ar"`, `"ru"`, `"unknown"`) |
| `contains_numbers` | `bool` | Regex match for numeric tokens |
| `contains_dates` | `bool` | Regex match for date patterns |
| `contains_urls` | `bool` | Regex match for URLs |
| `contains_email` | `bool` | Regex match for email addresses |
| `contains_code` | `bool` | Regex match for code keywords |
| `contains_emoji` | `bool` | Emoji library or unicode-range match |
| `contains_special_chars` | `bool` | Any non-alphanumeric, non-whitespace character |
| `punctuation_count` | `int` | Count of punctuation characters |
| `capitalization_ratio` | `float` | Uppercase / alphabetic character ratio (0-1) |
| `repeated_char_ratio` | `float` | Repeated consecutive chars / total length (0-1) |
| `stopword_ratio` | `float` | Stopwords / total tokens (0-1) |
| `avg_token_length` | `float` | Mean characters per token |
| `numeric_count` | `int` | Count of numeric tokens |
| `symbol_count` | `int` | Count of non-alphanumeric, non-whitespace characters |
| `whitespace_count` | `int` | Count of whitespace sequences |
| `uppercase_word_ratio` | `float` | All-caps words / total words (0-1) |
| `lowercase_word_ratio` | `float` | All-lowercase words / total words (0-1) |

### `QuestionSimilarityFeatures`

| Field | Type | Description |
|---|---|---|
| `length_difference` | `int` | Absolute difference in character count |
| `word_overlap_ratio` | `float` | Jaccard similarity of word sets (0-1) |
| `char_overlap_ratio` | `float` | Jaccard similarity of character sets (0-1) |
| `unique_word_ratio` | `float` | Words unique to Q1 / Q1 word count (0-1) |
| `question_ratio` | `float` | Q1 length / Q2 length |
| `stopword_overlap_ratio` | `float` | Jaccard similarity of stopword sets (0-1) |
| `punctuation_similarity` | `float` | 1 − normalized punctuation count difference (0-1) |
| `capitalization_similarity` | `float` | 1 − absolute capitalization ratio difference (0-1) |
| `numeric_overlap` | `bool` | Both questions contain numbers |
| `contains_same_url` | `bool` | Both contain URLs and at least one URL matches |
| `contains_same_email` | `bool` | Both contain emails and at least one email matches |
| `contains_same_code` | `bool` | Both contain code snippets |

### `TokenStatistics`

| Field | Type | Description |
|---|---|---|
| `total_tokens` | `int` | Token count |
| `unique_tokens` | `int` | Distinct token count |
| `avg_token_length` | `float` | Mean token length in characters |
| `min_token_length` | `int` | Shortest token |
| `max_token_length` | `int` | Longest token |
| `token_length_std` | `float` | Standard deviation of token lengths |

### `SentenceStatistics`

| Field | Type | Description |
|---|---|---|
| `total_sentences` | `int` | Sentence count |
| `avg_sentence_length_words` | `float` | Mean words per sentence |
| `min_sentence_length` | `int` | Shortest sentence in words |
| `max_sentence_length` | `int` | Longest sentence in words |
| `sentence_length_std` | `float` | Standard deviation of sentence lengths |

### `ReadabilityMetrics`

| Field | Type | Description |
|---|---|---|
| `flesch_reading_ease` | `float` | Flesch Reading Ease score (0-100) |
| `avg_syllables_per_word` | `float` | Mean syllables per word |
| `complex_word_count` | `int` | Words with >6 chars and >=3 syllables |
| `complex_word_ratio` | `float` | Complex words / total words (0-1) |

### `ComplexityScore`

| Field | Type | Description |
|---|---|---|
| `overall` | `float` | Mean of lexical, syntactic, semantic, technical (0-1) |
| `lexical` | `float` | Derived from complex word ratio |
| `syntactic` | `float` | Derived from average word length |
| `semantic` | `float` | Fixed at 0.3 (placeholder for future semantic analysis) |
| `technical` | `float` | Aggregated from code, URL, number, special char, emoji flags |

---

## Serialization

```python
analysis = analyzer.analyze(q1, q2)

# To dict
data = analysis.to_dict()

# To JSON string
json_str = analysis.to_json()

# From dict
restored = QueryAnalysis.from_dict(data)
```

The JSON output uses `json.dumps(indent=2, ensure_ascii=False)` for readability and unicode preservation.

---

## Future Schema Extensions

The schema is designed to accommodate these additions without breaking changes:

- `intent` — question intent classification
- `question_type` — what/why/how/when/where/who category
- `toxicity` — toxicity scores per question
- `entities` — named entity recognition results
- `sentiment` — per-question sentiment scores
- `abbreviations` — expanded abbreviation mappings
- `embedding` — optional embedding vector (lazy-loaded)
