from __future__ import annotations

import statistics

from ares.query_understanding.query_models import (
    ComplexityScore,
    QuestionMetadata,
    QuestionSimilarityFeatures,
    ReadabilityMetrics,
    SentenceStatistics,
    TokenStatistics,
)
from ares.query_understanding.utils import (
    capitalization_ratio,
    character_overlap,
    complex_word_count,
    contains_code,
    contains_date,
    contains_email,
    contains_emoji,
    contains_number,
    contains_url,
    count_syllables,
    find_emails,
    find_urls,
    flesch_reading_ease,
    is_stopword,
    jaccard_similarity,
    lowercase_word_ratio,
    numeric_count,
    punctuation_count,
    repeated_char_ratio,
    sentencize,
    symbol_count,
    tokenize,
    uppercase_word_ratio,
    whitespace_count,
)

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "by",
        "with",
        "from",
        "up",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "is",
        "am",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "can",
        "could",
        "shall",
        "should",
        "may",
        "might",
        "i",
        "me",
        "my",
        "myself",
        "we",
        "us",
        "our",
        "ours",
        "ourselves",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "her",
        "hers",
        "herself",
        "it",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
    }
)


def extract_question_metadata(text: str) -> QuestionMetadata:
    tokens = tokenize(text)
    sentences = sentencize(text)
    total_sentences = len(sentences)

    avg_word_len = statistics.mean([len(w) for w in tokens]) if tokens else 0.0
    avg_token_len = statistics.mean([len(w) for w in tokens]) if tokens else 0.0

    return QuestionMetadata(
        length=len(text),
        char_count=len(text),
        word_count=len(tokens),
        sentence_count=total_sentences,
        avg_word_length=round(avg_word_len, 2),
        language="en",
        contains_numbers=contains_number(text),
        contains_dates=contains_date(text),
        contains_urls=contains_url(text),
        contains_email=contains_email(text),
        contains_code=contains_code(text),
        contains_emoji=contains_emoji(text),
        contains_special_chars=bool(symbol_count(text) > 0),
        punctuation_count=punctuation_count(text),
        capitalization_ratio=round(capitalization_ratio(text), 4),
        repeated_char_ratio=round(repeated_char_ratio(text), 4),
        stopword_ratio=round(sum(1 for w in tokens if is_stopword(w)) / len(tokens), 4) if tokens else 0.0,
        avg_token_length=round(avg_token_len, 2),
        numeric_count=numeric_count(text),
        symbol_count=symbol_count(text),
        whitespace_count=whitespace_count(text),
        uppercase_word_ratio=round(uppercase_word_ratio(text), 4),
        lowercase_word_ratio=round(lowercase_word_ratio(text), 4),
    )


def extract_token_statistics(text: str) -> TokenStatistics:
    tokens = tokenize(text)
    if not tokens:
        return TokenStatistics()
    lengths = [len(t) for t in tokens]
    return TokenStatistics(
        total_tokens=len(tokens),
        unique_tokens=len(set(tokens)),
        avg_token_length=round(statistics.mean(lengths), 2),
        min_token_length=min(lengths),
        max_token_length=max(lengths),
        token_length_std=round(statistics.stdev(lengths), 2) if len(lengths) > 1 else 0.0,
    )


def extract_sentence_statistics(text: str) -> SentenceStatistics:
    sentences = sentencize(text)
    if not sentences:
        return SentenceStatistics()
    lengths = [len(tokenize(s)) for s in sentences]
    return SentenceStatistics(
        total_sentences=len(sentences),
        avg_sentence_length_words=round(statistics.mean(lengths), 2),
        min_sentence_length=min(lengths),
        max_sentence_length=max(lengths),
        sentence_length_std=round(statistics.stdev(lengths), 2) if len(lengths) > 1 else 0.0,
    )


def extract_readability(text: str) -> ReadabilityMetrics:
    tokens = tokenize(text)
    sentences = sentencize(text)
    if not tokens or not sentences:
        return ReadabilityMetrics()
    total_syllables = sum(count_syllables(w) for w in tokens)
    fre = flesch_reading_ease(total_syllables, len(tokens), len(sentences))
    cw_count = complex_word_count(tokens)
    return ReadabilityMetrics(
        flesch_reading_ease=round(fre, 2),
        avg_syllables_per_word=round(total_syllables / len(tokens), 2),
        complex_word_count=cw_count,
        complex_word_ratio=round(cw_count / len(tokens), 4) if tokens else 0.0,
    )


def extract_complexity(metadata: QuestionMetadata, readability: ReadabilityMetrics) -> ComplexityScore:
    lexical = min(1.0, readability.complex_word_ratio * 3)
    syntactic = min(1.0, metadata.avg_word_length / 10)
    technical = 0.0
    if metadata.contains_code:
        technical += 0.4
    if metadata.contains_urls:
        technical += 0.2
    if metadata.contains_numbers:
        technical += 0.15
    if metadata.contains_special_chars:
        technical += 0.1
    if metadata.contains_emoji:
        technical += 0.1
    technical = min(1.0, technical)
    semantic = 0.3
    overall = round((lexical + syntactic + semantic + technical) / 4, 4)
    return ComplexityScore(
        overall=overall,
        lexical=round(lexical, 4),
        syntactic=round(syntactic, 4),
        semantic=semantic,
        technical=round(technical, 4),
    )


def extract_similarity_features(
    text_a: str,
    text_b: str,
    meta_a: QuestionMetadata,
    meta_b: QuestionMetadata,
) -> QuestionSimilarityFeatures:
    tokens_a = set(tokenize(text_a.lower()))
    tokens_b = set(tokenize(text_b.lower()))

    stopwords_a = {w for w in tokens_a if w in STOPWORDS}
    stopwords_b = {w for w in tokens_b if w in STOPWORDS}

    return QuestionSimilarityFeatures(
        length_difference=abs(len(text_a) - len(text_b)),
        word_overlap_ratio=round(jaccard_similarity(tokens_a, tokens_b), 4),
        char_overlap_ratio=round(character_overlap(text_a, text_b), 4),
        unique_word_ratio=round(len(tokens_a - tokens_b) / len(tokens_a) if tokens_a else 0.0, 4),
        question_ratio=round(len(text_a) / len(text_b) if len(text_b) > 0 else 0.0, 4),
        stopword_overlap_ratio=round(jaccard_similarity(stopwords_a, stopwords_b), 4),
        punctuation_similarity=round(
            1.0
            - abs(meta_a.punctuation_count - meta_b.punctuation_count)
            / max(max(meta_a.punctuation_count, meta_b.punctuation_count), 1),
            4,
        ),
        capitalization_similarity=round(1.0 - abs(meta_a.capitalization_ratio - meta_b.capitalization_ratio), 4),
        numeric_overlap=meta_a.contains_numbers and meta_b.contains_numbers,
        contains_same_url=bool(
            contains_url(text_a) and contains_url(text_b) and any(u in text_b for u in find_urls(text_a))
        ),
        contains_same_email=bool(
            contains_email(text_a) and contains_email(text_b) and any(e in text_b for e in find_emails(text_a))
        ),
        contains_same_code=bool(contains_code(text_a) and contains_code(text_b)),
    )
