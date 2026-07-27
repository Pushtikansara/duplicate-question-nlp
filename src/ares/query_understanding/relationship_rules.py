from __future__ import annotations

from ares.query_understanding.relationship_models import (
    ComparisonStatistics,
    Evidence,
    RelationshipInfo,
    TransformationChain,
    TransformationStep,
)
from ares.query_understanding.relationship_patterns import (
    ACTIVE_PASSIVE_PATTERN_Q1,
    ACTIVE_PASSIVE_PATTERN_Q2,
    CURRENCY_PATTERN,
    DUPLICATE_WORD_PATTERN,
    INSERTED_CLAUSE_PATTERN,
    NEGATION_WORDS,
    PERCENTAGE_PATTERN,
    PRONOUNS,
    VERSION_PATTERN,
)
from ares.query_understanding.relationship_utils import (
    check_abbreviation,
    check_antonym,
    check_spelling_variant,
    check_synonym,
    compute_jaccard,
    compute_shared_token_ratio,
    compute_token_overlap,
    edit_distance,
    find_dates,
    find_numbers,
    find_times,
    find_units,
    normalize_text,
    normalized_edit_distance,
    strip_punctuation,
    tokenize,
)

_STOPWORDS_BASIC = frozenset(
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
        "is",
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
        "we",
        "us",
        "our",
        "you",
        "your",
        "he",
        "him",
        "his",
        "she",
        "her",
        "it",
        "its",
        "they",
        "them",
        "their",
        "this",
        "that",
        "these",
        "those",
    }
)


def _make_evidence(
    rule_name: str,
    layer: int,
    pattern: str,
    tokens1: list[str],
    tokens2: list[str],
    conf: float,
) -> Evidence:
    return Evidence(
        rule_name=rule_name,
        rule_layer=layer,
        matched_pattern=pattern,
        tokens_q1=tokens1,
        tokens_q2=tokens2,
        confidence=conf,
    )


def _make_rel(
    rtype: str,
    conf: float,
    evidence: list[Evidence],
    human: str = "",
    dev: str = "",
) -> RelationshipInfo:
    return RelationshipInfo(
        relationship_type=rtype,
        confidence=conf,
        evidence=evidence,
        human_explanation=human,
        developer_explanation=dev or human,
    )


def _has_negation(tokens: list[str]) -> bool:
    return any(t.lower() in NEGATION_WORDS for t in tokens)


def _count_negations(tokens: list[str]) -> int:
    return sum(1 for t in tokens if t.lower() in NEGATION_WORDS)


def _diff_tokens(t1: list[str], t2: list[str]) -> tuple[list[str], list[str]]:
    set1 = {t.lower() for t in t1}
    set2 = {t.lower() for t in t2}
    q1_only = [t for t in t1 if t.lower() not in set2]
    q2_only = [t for t in t2 if t.lower() not in set1]
    return q1_only, q2_only


# ============================================================
# LAYER 1: Normalization
# ============================================================


def layer_1_normalize(q1: str, q2: str) -> tuple[str, str, list[str], list[str]]:
    n1 = normalize_text(q1)
    n2 = normalize_text(q2)
    t1 = tokenize(n1)
    t2 = tokenize(n2)
    return n1, n2, t1, t2


# ============================================================
# LAYER 2: Token comparison
# ============================================================


def layer_2_token_comparison(
    t1: list[str],
    t2: list[str],
    n1: str,
    n2: str,
    q1: str = "",
    q2: str = "",
) -> tuple[list[RelationshipInfo], ComparisonStatistics, list[str], list[str]]:
    relations: list[RelationshipInfo] = []
    stats = ComparisonStatistics()

    stats.token_count_q1 = len(t1)
    stats.token_count_q2 = len(t2)
    stats.char_count_q1 = len(n1)
    stats.char_count_q2 = len(n2)
    stats.word_count_q1 = len(t1)
    stats.word_count_q2 = len(t2)
    stats.token_overlap = compute_token_overlap(t1, t2)
    stats.token_overlap_ratio = stats.token_overlap / max(min(len(t1), len(t2)), 1)
    stats.edit_distance = edit_distance(n1, n2)
    stats.normalized_edit_distance = normalized_edit_distance(n1, n2)
    stats.jaccard_similarity = compute_jaccard(t1, t2)
    stats.length_difference = abs(len(t1) - len(t2))
    stats.shared_token_ratio = compute_shared_token_ratio(t1, t2)

    # Exact match check
    if n1 == n2 and t1 == t2:
        relations.append(
            _make_rel(
                "exact_match",
                1.0,
                [_make_evidence("exact_match", 2, "normalized_text_identical", t1, t2, 1.0)],
                "Both questions are identical",
                "normalized_text_identical",
            )
        )
        stats.normalized_edit_distance = 0.0
        return relations, stats, t1, t2

    # Near match
    if stats.normalized_edit_distance < 0.15:
        relations.append(
            _make_rel(
                "near_match",
                0.85,
                [_make_evidence("near_match", 2, f"edit_distance={stats.edit_distance}", t1, t2, 0.85)],
                "Questions are nearly identical with minor differences",
                f"edit_distance={stats.edit_distance}",
            )
        )

    # Capitalization only
    if n1 == n2 and t1 != t2:
        relations.append(
            _make_rel(
                "capitalization_only",
                0.95,
                [_make_evidence("cap_only", 2, "differs_in_case", t1, t2, 0.95)],
                "Only capitalization differs between questions",
            )
        )

    # Whitespace only
    if n1 == n2 and ("  " in q1 or "  " in q2 or q1.strip() != q1 or q2.strip() != q2) and n1.strip() == n2.strip():
        relations.append(
            _make_rel(
                "whitespace_only",
                0.95,
                [_make_evidence("whitespace_only", 2, "whitespace_diff", t1, t2, 0.95)],
                "Only whitespace differs between questions",
            )
        )

    # Punctuation only
    if strip_punctuation(n1) == strip_punctuation(n2) and n1 != n2:
        relations.append(
            _make_rel(
                "punctuation_only",
                0.90,
                [_make_evidence("punct_only", 2, "differs_in_punctuation", t1, t2, 0.90)],
                "Only punctuation differs between questions",
            )
        )

    return relations, stats, t1, t2


# ============================================================
# LAYER 3: Phrase comparison
# ============================================================


def layer_3_phrase_comparison(
    t1: list[str],
    t2: list[str],
    relations: list[RelationshipInfo],
    n1: str,
    n2: str,
) -> list[RelationshipInfo]:
    q1_only, q2_only = _diff_tokens(t1, t2)

    # Word order change
    set1 = {t.lower() for t in t1}
    set2 = {t.lower() for t in t2}
    if set1 == set2 and len(t1) == len(t2) and t1 != t2:
        relations.append(
            _make_rel(
                "word_order_change",
                0.80,
                [_make_evidence("word_order", 3, "same_tokens_diff_order", t1, t2, 0.80)],
                "Words are reordered but identical",
            )
        )

    # Duplicate tokens / repeated words
    for tokens, label in [(t1, "q1"), (t2, "q2")]:
        combined = " ".join(tokens)
        dup_matches = list(DUPLICATE_WORD_PATTERN.finditer(combined))
        if dup_matches:
            rtype = "duplicate_tokens" if label == "q1" else "repeated_words"
            evidence = [
                _make_evidence(f"duplicate_{label}", 3, m.group(), [m.group()], [m.group()], 0.7) for m in dup_matches
            ]
            relations.append(_make_rel(rtype, 0.70, evidence, f"Contains duplicate words in {label}"))

    # Inserted/removed clause
    for _tokens, label, n in [(t1, "q1", n1), (t2, "q2", n2)]:
        if INSERTED_CLAUSE_PATTERN.search(n):
            rtype = "inserted_clause" if label == "q2" else "removed_clause"
            relations.append(
                _make_rel(
                    rtype,
                    0.60,
                    [_make_evidence(f"clause_{label}", 3, "clause_detected", t1, t2, 0.60)],
                    f"Clause {'inserted' if rtype == 'inserted_clause' else 'removed'} in {label}",
                )
            )

    # Passive ↔ Active voice
    has_active = bool(ACTIVE_PASSIVE_PATTERN_Q1.search(n1))
    has_passive = bool(ACTIVE_PASSIVE_PATTERN_Q2.search(n2))
    has_passive2 = bool(ACTIVE_PASSIVE_PATTERN_Q2.search(n1))
    has_active2 = bool(ACTIVE_PASSIVE_PATTERN_Q1.search(n2))
    if (has_active and has_passive) or (has_passive2 and has_active2):
        relations.append(
            _make_rel(
                "sentence_structure_change",
                0.65,
                [_make_evidence("voice_change", 3, "active_passive_switch", t1, t2, 0.65)],
                "Voice changes between active and passive",
            )
        )

    # Lexical reformulation (high overlap but not exact)
    if (
        relations
        and not any(r.relationship_type == "exact_match" for r in relations)
        and compute_jaccard(t1, t2) > 0.5
        and len(t1) != len(t2)
        and not any(r.relationship_type == "lexical_reformulation" for r in relations)
    ):
        relations.append(
            _make_rel(
                "lexical_reformulation",
                0.60,
                [_make_evidence("lexical_reformulation", 3, "different_wording", t1, t2, 0.60)],
                "Same meaning expressed with different words",
            )
        )

    return relations


# ============================================================
# LAYER 4: Entity comparison (delegated to entity detector)
# ============================================================


# ============================================================
# LAYER 5: Negation & Polarity
# ============================================================


def layer_5_negation(
    t1: list[str],
    t2: list[str],
) -> list[RelationshipInfo]:
    relations: list[RelationshipInfo] = []
    neg1 = _has_negation(t1)
    neg2 = _has_negation(t2)
    count1 = _count_negations(t1)
    count2 = _count_negations(t2)
    neg_tokens_1 = {t.lower() for t in t1 if t.lower() in NEGATION_WORDS}
    neg_tokens_2 = {t.lower() for t in t2 if t.lower() in NEGATION_WORDS}

    removed = neg_tokens_1 - neg_tokens_2
    added = neg_tokens_2 - neg_tokens_1

    if not neg1 and neg2:
        relations.append(
            _make_rel(
                "negation_introduced",
                0.90,
                [_make_evidence("negation_introduced", 5, "negation_found", t1, t2, 0.90)],
                f"Negation introduced in Q2: {', '.join(added)}",
            )
        )
    elif neg1 and not neg2:
        relations.append(
            _make_rel(
                "negation_removed",
                0.90,
                [_make_evidence("negation_removed", 5, "negation_found", t1, t2, 0.90)],
                f"Negation removed in Q2: {', '.join(removed)}",
            )
        )
    elif neg1 and neg2:
        if removed and not added:
            relations.append(
                _make_rel(
                    "negation_removed",
                    0.80,
                    [_make_evidence("negation_removed", 5, "partial_removal", t1, t2, 0.80)],
                    f"Some negations removed: {', '.join(removed)}",
                )
            )
        elif added and not removed:
            relations.append(
                _make_rel(
                    "negation_introduced",
                    0.80,
                    [_make_evidence("negation_introduced", 5, "partial_addition", t1, t2, 0.80)],
                    f"Some negations added: {', '.join(added)}",
                )
            )
        if removed and added:
            relations.append(
                _make_rel(
                    "question_polarity_change",
                    0.75,
                    [_make_evidence("polarity_change", 5, "negation_replaced", t1, t2, 0.75)],
                    "Negation tokens changed",
                )
            )
        if count1 >= 2 and count2 >= 2 and (removed or added):
            relations.append(
                _make_rel(
                    "double_negation",
                    0.80,
                    [_make_evidence("double_negation", 5, "multiple_negations", t1, t2, 0.80)],
                    "Both questions contain multiple negations",
                )
            )

    return relations


# ============================================================
# LAYER 6: Numeric, Date, Version, Currency, Percentage, Unit
# ============================================================


def layer_6_numeric(
    n1: str,
    n2: str,
    t1: list[str],
    t2: list[str],
) -> list[RelationshipInfo]:
    relations: list[RelationshipInfo] = []

    # Numbers
    nums1 = find_numbers(n1)
    nums2 = find_numbers(n2)
    if nums1 and nums2:
        for v1, _s1, _e1 in nums1:
            for v2, _s2, _e2 in nums2:
                try:
                    n1v = float(v1.replace(",", ""))
                    n2v = float(v2.replace(",", ""))
                    if abs(n1v - n2v) > 0.001:
                        relations.append(
                            _make_rel(
                                "numeric_difference",
                                0.85,
                                [
                                    _make_evidence(
                                        "numeric_diff",
                                        6,
                                        f"{v1} vs {v2}",
                                        [v1],
                                        [v2],
                                        0.85,
                                    )
                                ],
                                f"Numeric value differs: {v1} vs {v2}",
                            )
                        )
                except ValueError:
                    continue

    # Versions
    ver_matches1 = list(VERSION_PATTERN.finditer(n1))
    ver_matches2 = list(VERSION_PATTERN.finditer(n2))
    for m1 in ver_matches1:
        for m2 in ver_matches2:
            v1 = m1.group(2) or m1.group()
            v2 = m2.group(2) or m2.group()
            if v1 != v2:
                relations.append(
                    _make_rel(
                        "version_difference",
                        0.90,
                        [
                            _make_evidence(
                                "version_diff",
                                6,
                                f"{v1} vs {v2}",
                                [v1],
                                [v2],
                                0.90,
                            )
                        ],
                        f"Version differs: {v1} vs {v2}",
                    )
                )

    # Dates
    dates1 = find_dates(n1)
    dates2 = find_dates(n2)
    if dates1 and dates2:
        for d1, _, _ in dates1:
            for d2, _, _ in dates2:
                if d1 != d2:
                    relations.append(
                        _make_rel(
                            "date_difference",
                            0.85,
                            [
                                _make_evidence(
                                    "date_diff",
                                    6,
                                    f"{d1} vs {d2}",
                                    [d1],
                                    [d2],
                                    0.85,
                                )
                            ],
                            f"Date differs: {d1} vs {d2}",
                        )
                    )

    # Times
    times1 = find_times(n1)
    times2 = find_times(n2)
    if times1 and times2:
        for t1v, _, _ in times1:
            for t2v, _, _ in times2:
                if t1v != t2v:
                    relations.append(
                        _make_rel(
                            "time_difference",
                            0.85,
                            [
                                _make_evidence(
                                    "time_diff",
                                    6,
                                    f"{t1v} vs {t2v}",
                                    [t1v],
                                    [t2v],
                                    0.85,
                                )
                            ],
                            f"Time differs: {t1v} vs {t2v}",
                        )
                    )

    # Currency
    cur_matches1 = list(CURRENCY_PATTERN.finditer(n1))
    cur_matches2 = list(CURRENCY_PATTERN.finditer(n2))
    if cur_matches1 and cur_matches2:
        for m1 in cur_matches1:
            for m2 in cur_matches2:
                if m1.group() != m2.group():
                    relations.append(
                        _make_rel(
                            "currency_difference",
                            0.85,
                            [
                                _make_evidence(
                                    "currency_diff",
                                    6,
                                    f"{m1.group()} vs {m2.group()}",
                                    [m1.group()],
                                    [m2.group()],
                                    0.85,
                                )
                            ],
                            f"Currency differs: {m1.group()} vs {m2.group()}",
                        )
                    )

    # Percentage
    pct1 = list(PERCENTAGE_PATTERN.finditer(n1))
    pct2 = list(PERCENTAGE_PATTERN.finditer(n2))
    if pct1 and pct2:
        for m1 in pct1:
            for m2 in pct2:
                if m1.group() != m2.group():
                    relations.append(
                        _make_rel(
                            "percentage_difference",
                            0.85,
                            [
                                _make_evidence(
                                    "pct_diff",
                                    6,
                                    f"{m1.group()} vs {m2.group()}",
                                    [m1.group()],
                                    [m2.group()],
                                    0.85,
                                )
                            ],
                            f"Percentage differs: {m1.group()} vs {m2.group()}",
                        )
                    )

    # Units
    units1 = find_units(n1)
    units2 = find_units(n2)
    unit_diffs = _compare_units(units1, units2)
    for ud in unit_diffs:
        relations.append(
            _make_rel(
                "unit_difference",
                0.80,
                [
                    _make_evidence(
                        "unit_diff",
                        6,
                        ud.get("detail", ""),
                        [ud.get("q1_str", "")],
                        [ud.get("q2_str", "")],
                        0.80,
                    )
                ],
                ud.get("explanation", "Unit differs"),
            )
        )

    return relations


def _compare_units(
    units1: list[tuple[str, str, float, int, int]],
    units2: list[tuple[str, str, float, int, int]],
) -> list[dict]:
    results: list[dict] = []
    for u1 in units1:
        for u2 in units2:
            txt1, norm1, val1, _, _ = u1
            txt2, norm2, val2, _, _ = u2
            if norm1 == norm2:
                if abs(val1 - val2) > 0.001:
                    results.append(
                        {
                            "q1_str": txt1,
                            "q2_str": txt2,
                            "detail": f"{txt1} vs {txt2}",
                            "explanation": f"Unit value differs: {txt1} vs {txt2}",
                        }
                    )
            else:
                results.append(
                    {
                        "q1_str": txt1,
                        "q2_str": txt2,
                        "detail": f"{norm1} vs {norm2}",
                        "explanation": f"Unit type changes: {txt1} vs {txt2}",
                    }
                )
    return results


# ============================================================
# LAYER 7: Lexical substitution (synonyms, antonyms, abbrevs)
# ============================================================


def layer_7_lexical(
    t1: list[str],
    t2: list[str],
) -> list[RelationshipInfo]:
    relations: list[RelationshipInfo] = []
    q1_only, q2_only = _diff_tokens(t1, t2)

    for w1 in q1_only:
        for w2 in q2_only:
            if check_synonym(w1, w2):
                relations.append(
                    _make_rel(
                        "synonym_replacement",
                        0.75,
                        [_make_evidence("synonym", 7, f"{w1}->{w2}", [w1], [w2], 0.75)],
                        f"Synonym: '{w1}' replaced by '{w2}'",
                    )
                )
            if check_antonym(w1, w2):
                relations.append(
                    _make_rel(
                        "antonym_detection",
                        0.80,
                        [_make_evidence("antonym", 7, f"{w1}<->{w2}", [w1], [w2], 0.80)],
                        f"Antonym: '{w1}' vs '{w2}'",
                    )
                )
            if check_spelling_variant(w1, w2):
                relations.append(
                    _make_rel(
                        "spelling_variant",
                        0.85,
                        [_make_evidence("spelling", 7, f"{w1}<->{w2}", [w1], [w2], 0.85)],
                        f"Spelling variant: '{w1}' vs '{w2}'",
                    )
                )
            if check_abbreviation(w1, w2):
                relations.append(
                    _make_rel(
                        "abbreviation_expansion",
                        0.85,
                        [_make_evidence("abbrev", 7, f"{w1}<->{w2}", [w1], [w2], 0.85)],
                        f"Abbreviation: '{w1}' expanded to '{w2}'",
                    )
                )

    if q1_only or q2_only:
        for w in q1_only:
            if w in PRONOUNS:
                relations.append(
                    _make_rel(
                        "pronoun_replacement",
                        0.70,
                        [_make_evidence("pronoun_q1", 7, w, [w], [], 0.70)],
                        f"Pronoun '{w}' replaced in Q2",
                    )
                )
        for w in q2_only:
            if w in PRONOUNS:
                relations.append(
                    _make_rel(
                        "pronoun_replacement",
                        0.70,
                        [_make_evidence("pronoun_q2", 7, w, [], [w], 0.70)],
                        f"Pronoun '{w}' added in Q2",
                    )
                )

    return relations


# ============================================================
# LAYER 7b: Entity-level (delegated from layer 4)
# ============================================================


def layer_7b_entity_relations(
    gt1: list[str],
    gt2: list[str],
) -> list[RelationshipInfo]:
    relations: list[RelationshipInfo] = []
    unique1 = list({t.lower(): t for t in reversed(gt1)}.values())
    unique2 = list({t.lower(): t for t in reversed(gt2)}.values())
    if not unique1 and not unique2:
        return relations
    q1_only, q2_only = _diff_tokens(unique1, unique2)

    if q1_only and not q2_only:
        relations.append(
            _make_rel(
                "entity_removal",
                0.75,
                [_make_evidence("entity_removal", 4, "entities in q1 only", q1_only[:5], [], 0.75)],
                f"Entities removed in Q2: {', '.join(q1_only[:5])}{'...' if len(q1_only) > 5 else ''}",
            )
        )
    if q2_only and not q1_only:
        relations.append(
            _make_rel(
                "entity_addition",
                0.75,
                [_make_evidence("entity_addition", 4, "entities in q2 only", [], q2_only[:5], 0.75)],
                f"Entities added in Q2: {', '.join(q2_only[:5])}{'...' if len(q2_only) > 5 else ''}",
            )
        )

    if q1_only and q2_only:
        relations.append(
            _make_rel(
                "entity_replacement",
                0.70,
                [_make_evidence("entity_replacement", 4, "entities differ", q1_only[:5], q2_only[:5], 0.70)],
                f"Entities replaced: {', '.join(q1_only[:5])} -> {', '.join(q2_only[:5])}",
            )
        )

    if len(unique1) == len(unique2):
        same_set = {t.lower() for t in unique1} == {t.lower() for t in unique2}
        if same_set:
            relations.append(
                _make_rel(
                    "entity_reordering",
                    0.60,
                    [_make_evidence("entity_reorder", 4, "same_entities_diff_order", unique1, unique2, 0.60)],
                    "Same entities in different order",
                )
            )

    return relations


# ============================================================
# LAYER 8: Transformation inference & risk evaluation
# ============================================================


def layer_8_synthesize(
    relations: list[RelationshipInfo],
    t1: list[str],
    t2: list[str],
    n1: str,
    n2: str,
    stats: ComparisonStatistics,
) -> tuple[float, float, TransformationChain, list[str], list[str]]:
    if not relations:
        score = round(max(0, 100 - stats.normalized_edit_distance * 100), 2)
        conf = max(0.3, 1.0 - stats.normalized_edit_distance)
        return score, conf, TransformationChain(final_intent="unknown"), [], []

    # Superficial relations override entity-level relations
    superficial = {"punctuation_only", "formatting_only", "capitalization_only", "whitespace_only"}
    has_superficial = any(r.relationship_type in superficial and r.confidence > 0.85 for r in relations)
    if has_superficial:
        relations = [r for r in relations if r.relationship_type not in {"entity_replacement", "entity_reordering"}]

    score = 0.0
    conf_sum = 0.0
    steps: list[TransformationStep] = []
    seen_types: set[str] = set()

    for r in sorted(relations, key=lambda x: x.confidence, reverse=True):
        if r.relationship_type == "exact_match":
            score = 100.0
            conf = 1.0
            steps.append(
                TransformationStep(
                    step_type="identical",
                    description="No transformation needed",
                    confidence=1.0,
                )
            )
            sem_flags = ["equivalent_intent"]
            return (
                score,
                conf,
                TransformationChain(
                    steps=steps,
                    final_intent="equivalent",
                    is_equivalent=True,
                ),
                sem_flags,
                [],
            )

        weight = {
            "near_match": 95,
            "punctuation_only": 98,
            "formatting_only": 97,
            "capitalization_only": 97,
            "whitespace_only": 99,
            "lexical_reformulation": 80,
            "word_order_change": 85,
            "sentence_structure_change": 75,
            "synonym_replacement": 80,
            "abbreviation_expansion": 80,
            "abbreviation_compression": 80,
            "acronym_match": 80,
            "spelling_variant": 90,
            "pronoun_replacement": 85,
            "reference_shift": 80,
            "inserted_clause": 70,
            "removed_clause": 70,
            "entity_replacement": 60,
            "entity_addition": 55,
            "entity_removal": 55,
            "entity_reordering": 80,
            "version_difference": 50,
            "numeric_difference": 50,
            "date_difference": 45,
            "time_difference": 45,
            "currency_difference": 45,
            "unit_difference": 50,
            "percentage_difference": 50,
            "negation_introduced": 30,
            "negation_removed": 30,
            "double_negation": 40,
            "question_polarity_change": 35,
            "antonym_detection": 25,
            "duplicate_tokens": 85,
            "repeated_words": 80,
        }.get(r.relationship_type, 50)

        score += weight * r.confidence
        conf_sum += r.confidence

        if r.relationship_type not in seen_types:
            seen_types.add(r.relationship_type)
            desc = r.human_explanation or r.relationship_type
            steps.append(
                TransformationStep(
                    step_type=r.relationship_type,
                    description=desc,
                    confidence=r.confidence,
                )
            )

    total_weight = (
        sum(
            {
                "exact_match": 1,
                "near_match": 1,
                "punctuation_only": 1,
                "formatting_only": 1,
                "capitalization_only": 1,
                "whitespace_only": 1,
            }.get(r.relationship_type, 1)
            for r in relations
        )
        or 1
    )

    avg_conf = conf_sum / len(relations) if relations else 0
    final_score = round(score / max(total_weight * 100, 1) * 100, 2)
    final_score = max(0, min(100, final_score))
    final_conf = round(avg_conf, 4)

    semantic_flags = _infer_semantic_flags(relations, stats)
    risk_flags = _evaluate_risks(relations, stats, semantic_flags)

    is_equiv = final_score >= 70 and "meaning_changed" not in risk_flags
    chain = TransformationChain(
        steps=steps,
        final_intent="equivalent" if is_equiv else "different",
        is_equivalent=is_equiv,
    )

    return final_score, final_conf, chain, semantic_flags, risk_flags


def _infer_semantic_flags(
    relations: list[RelationshipInfo],
    stats: ComparisonStatistics,
) -> list[str]:
    flags: list[str] = []
    types = {r.relationship_type for r in relations}

    if stats.jaccard_similarity >= 0.8:
        flags.append("equivalent_intent")
    if "entity_replacement" in types:
        flags.append("different_entity")
    if "entity_addition" in types:
        flags.append("more_specific")
    if "entity_removal" in types:
        flags.append("less_specific")
    if "numeric_difference" in types or "version_difference" in types:
        flags.append("numeric_shift")
    if "date_difference" in types or "time_difference" in types:
        flags.append("temporal_shift")
    if "negation_introduced" in types or "negation_removed" in types:
        flags.append("negation_shift")
    if "question_polarity_change" in types:
        flags.append("polarity_change")
    if "pronoun_replacement" in types:
        flags.append("perspective_change")
    if "abbreviation_expansion" in types:
        flags.append("technical_level_change")
    if "synonym_replacement" in types:
        flags.append("formality_change")
    if stats.length_difference >= 3:
        flags.append("scope_change")
    if stats.length_difference >= 5:
        flags.append("broader_query" if stats.token_count_q2 > stats.token_count_q1 else "narrower_query")
    if "antonym_detection" in types:
        flags.append("certainty_change")

    return flags


def _evaluate_risks(
    relations: list[RelationshipInfo],
    stats: ComparisonStatistics,
    semantic_flags: list[str],
) -> list[str]:
    flags: list[str] = []
    types = {r.relationship_type for r in relations}

    if "negation_introduced" in types or "negation_removed" in types:
        flags.append("meaning_changed")
    if "antonym_detection" in types:
        flags.append("meaning_changed")
    if "question_polarity_change" in types:
        flags.append("negation_conflict")
    if "version_difference" in types:
        flags.append("version_conflict")
    if "numeric_difference" in types or "currency_difference" in types:
        flags.append("numeric_conflict")
    if "date_difference" in types or "time_difference" in types:
        flags.append("temporal_conflict")
    if "entity_replacement" in types:
        flags.append("entity_conflict")

    if stats.edit_distance > 20:
        flags.append("high_semantic_drift")
    elif stats.edit_distance <= 2 and not types - {"punctuation_only", "whitespace_only", "capitalization_only"}:
        flags.append("low_semantic_drift")

    if 30 <= stats.jaccard_similarity <= 70:
        flags.append("ambiguous_difference")

    if stats.jaccard_similarity > 0.8 and "entity_replacement" in types:
        flags.append("possible_false_positive")
    if stats.jaccard_similarity < 0.3 and not types - {"entity_replacement", "entity_addition", "entity_removal"}:
        flags.append("possible_false_negative")

    return flags
