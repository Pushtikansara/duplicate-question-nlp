from __future__ import annotations

from ares.query_understanding.type_models import QuestionTypeResult
from ares.query_understanding.type_patterns import (
    COMPLEMENTARY_PAIRS,
    COMPLEMENTARY_PATTERN_SCORES,
)
from ares.query_understanding.type_rules import classify_question
from ares.query_understanding.utils import (
    jaccard_similarity,
    normalize_text,
    tokenize,
)


class QuestionTypeDetector:
    def detect(
        self,
        question_1: str,
        question_2: str,
        normalized_1: str | None = None,
        normalized_2: str | None = None,
    ) -> QuestionTypeResult:
        if not question_1 and not question_2:
            return QuestionTypeResult(
                pair_type="unknown",
                classification_reason="both_inputs_empty",
            )

        norm_1 = normalized_1 if normalized_1 else normalize_text(question_1)
        norm_2 = normalized_2 if normalized_2 else normalize_text(question_2)

        q1_type, q1_conf, q1_reason = classify_question(question_1, norm_1)
        q2_type, q2_conf, q2_reason = classify_question(question_2, norm_2)

        pair_type, pair_conf, pair_reason = self._analyze_pair(
            q1_type,
            q2_type,
            question_1,
            question_2,
            norm_1,
            norm_2,
        )

        overall_conf = round((q1_conf + q2_conf + pair_conf) / 3, 4)

        reason_parts = []
        reason_parts.append(f"q1:{q1_type}:{q1_reason}")
        reason_parts.append(f"q2:{q2_type}:{q2_reason}")
        reason_parts.append(f"pair:{pair_type}:{pair_reason}")
        reason_str = " | ".join(reason_parts)

        return QuestionTypeResult(
            question_1_type=q1_type,
            question_2_type=q2_type,
            pair_type=pair_type,
            classification_confidence=overall_conf,
            classification_reason=reason_str,
        )

    def _analyze_pair(
        self,
        q1_type: str,
        q2_type: str,
        raw_1: str,
        raw_2: str,
        norm_1: str,
        norm_2: str,
    ) -> tuple[str, float, str]:
        if not raw_1.strip() or not raw_2.strip():
            return "unknown", 0.0, "one_or_both_empty"

        tokens_1 = set(tokenize(norm_1.lower()))
        tokens_2 = set(tokenize(norm_2.lower()))
        word_overlap = jaccard_similarity(tokens_1, tokens_2)

        char_overlap = _char_overlap(norm_1, norm_2)

        if q1_type == q2_type:
            if word_overlap >= 0.80 or char_overlap >= 0.85:
                return "potential_paraphrase", round(0.85 + word_overlap * 0.10, 4), f"high_overlap:{word_overlap:.2f}"
            elif word_overlap >= 0.40:
                return (
                    "potential_reformulation",
                    round(0.60 + word_overlap * 0.20, 4),
                    f"moderate_overlap:{word_overlap:.2f}",
                )
            else:
                return "same_type", 0.50, f"same_type:{q1_type}_low_overlap:{word_overlap:.2f}"

        if q2_type in COMPLEMENTARY_PAIRS.get(q1_type, set()):
            base_score = COMPLEMENTARY_PATTERN_SCORES.get((q1_type, q2_type), 0.60)
            overlap_bonus = min(0.15, word_overlap * 0.15)
            return "complementary", round(base_score + overlap_bonus, 4), f"complementary:{q1_type}+{q2_type}"

        if q1_type in COMPLEMENTARY_PAIRS.get(q2_type, set()):
            base_score = COMPLEMENTARY_PATTERN_SCORES.get((q2_type, q1_type), 0.60)
            overlap_bonus = min(0.15, word_overlap * 0.15)
            return "complementary", round(base_score + overlap_bonus, 4), f"complementary:{q2_type}+{q1_type}"

        return "different_type", 0.40, f"different:{q1_type}|{q2_type}"


def _char_overlap(t1: str, t2: str) -> float:
    if not t1 or not t2:
        return 0.0
    set1 = set(t1.replace(" ", ""))
    set2 = set(t2.replace(" ", ""))
    if not set1 or not set2:
        return 0.0
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union)
