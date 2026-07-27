from __future__ import annotations

import re

from ares.query_understanding.entity_models import Entity, EntityPairMatch


def match_entities(
    entities_1: list[Entity],
    entities_2: list[Entity],
) -> tuple[list[EntityPairMatch], list[Entity], list[Entity]]:
    if not entities_1 or not entities_2:
        return [], list(entities_1), list(entities_2)

    used_2: set[int] = set()
    matches: list[EntityPairMatch] = []

    for i, e1 in enumerate(entities_1):
        best_match: tuple[int, float, str] | None = None
        for j, e2 in enumerate(entities_2):
            if j in used_2:
                continue
            match_type, score = _compare_entities(e1, e2)
            if score > 0:
                if best_match is None or score > best_match[1]:
                    best_match = (j, score, match_type)

        if best_match is not None:
            j, score, match_type = best_match
            used_2.add(j)
            matches.append(
                EntityPairMatch(
                    entity_1=e1,
                    entity_2=entities_2[j],
                    match_type=match_type,
                    similarity=round(score, 4),
                )
            )

    matched_2_indices = set()
    for m in matches:
        for j, e2 in enumerate(entities_2):
            if e2 is m.entity_2:
                matched_2_indices.add(j)

    unique_1 = [e for i, e in enumerate(entities_1) if not any(m.entity_1 is e for m in matches)]
    unique_2 = [e for j, e in enumerate(entities_2) if j not in matched_2_indices]

    return matches, unique_1, unique_2


def _compare_entities(e1: Entity, e2: Entity) -> tuple[str, float]:
    t1 = e1.text.strip()
    t2 = e2.text.strip()
    n1 = e1.normalized or t1.lower()
    n2 = e2.normalized or t2.lower()

    if not t1 or not t2:
        return ("no_match", 0.0)

    if n1 == n2 and t1 == t2:
        return ("exact_match", 1.0)

    if n1 == n2 and t1 != t2:
        return ("case_difference", 0.9)

    if _is_abbreviation(n1, n2) or _is_abbreviation(n2, n1):
        return ("abbreviation", 0.8)

    if e1.entity_type == e2.entity_type == "VERSION":
        return _compare_versions(t1, t2)

    if e1.entity_type == e2.entity_type == "NUMBER":
        return _compare_numbers(t1, t2)

    if _is_partial_match(n1, n2):
        return ("partial_match", 0.6)

    if _is_partial_match(n2, n1):
        return ("partial_match", 0.6)

    return ("no_match", 0.0)


def _is_abbreviation(a: str, b: str) -> bool:
    a_clean = re.sub(r"[^a-z0-9]", "", a)
    b_clean = re.sub(r"[^a-z0-9]", "", b)
    if not a_clean or not b_clean:
        return False
    if a_clean == b_clean:
        return False

    if len(a_clean) >= 2 and len(b_clean) >= 3:
        words_b = b.split()
        if len(words_b) >= 2:
            initials = "".join(w[0] for w in words_b if w).lower()
            if initials and a_clean == initials:
                return True

    short, long = (a_clean, b_clean) if len(a_clean) <= len(b_clean) else (b_clean, a_clean)
    if len(short) >= 2 and len(long) >= 4:
        if short[0] == long[0] and short[-1] == long[-1]:
            if set(short).issubset(set(long)):
                return True
    return False


def _is_partial_match(a: str, b: str) -> bool:
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return False
    intersection = words_a & words_b
    if not intersection:
        return False
    smaller = min(len(words_a), len(words_b))
    return len(intersection) / smaller >= 0.5


def _compare_versions(v1: str, v2: str) -> tuple[str, float]:
    try:
        parts1 = [int(p) for p in re.split(r"[.-]", v1) if p.isdigit()]
        parts2 = [int(p) for p in re.split(r"[.-]", v2) if p.isdigit()]
        if parts1 == parts2:
            return ("exact_match", 1.0)
        if parts1 and parts2 and parts1[0] == parts2[0]:
            return ("version_difference", 0.7)
    except (ValueError, IndexError):
        pass
    return ("no_match", 0.0)


def _compare_numbers(n1: str, n2: str) -> tuple[str, float]:
    try:
        v1 = float(n1.replace(",", "").replace(" ", ""))
        v2 = float(n2.replace(",", "").replace(" ", ""))
        if v1 == v2:
            return ("exact_match", 1.0)
        return ("numeric_difference", 0.5)
    except (ValueError, AttributeError):
        pass
    return ("no_match", 0.0)
