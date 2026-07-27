from __future__ import annotations

import time

from ares.query_understanding.complexity_models import (
    ComplexityAnalysis,
    score_to_difficulty,
)
from ares.query_understanding.complexity_rules import (
    abbreviation_density,
    ambiguity_score,
    comparison_difficulty,
    confidence_estimate,
    entity_complexity,
    entity_density,
    flesch_reading_ease,
    lexical_complexity,
    numeric_density,
    question_length_score,
    rare_token_density,
    readability_complexity,
    risk_score,
    semantic_complexity,
    sentence_complexity,
    syntactic_complexity,
    token_diversity,
)
from ares.query_understanding.entity_models import EntityResult
from ares.query_understanding.query_models import (
    QuestionMetadata,
    QuestionSimilarityFeatures,
)
from ares.query_understanding.relationship_models import RelationshipAnalysis
from ares.query_understanding.utils import normalize_text as utils_normalize_text


def _tokenize(text: str) -> list[str]:
    return [t for t in text.split() if t]


class ComplexityAnalyzer:
    version: str = "1.0.0"

    def analyze(
        self,
        question_1: str,
        question_2: str,
        metadata_1: QuestionMetadata | None = None,
        metadata_2: QuestionMetadata | None = None,
        similarity: QuestionSimilarityFeatures | None = None,
        entity_analysis: EntityResult | None = None,
        relationship_analysis: RelationshipAnalysis | None = None,
    ) -> ComplexityAnalysis:
        start = time.time()

        n1 = utils_normalize_text(question_1) if isinstance(question_1, str) else ""
        n2 = utils_normalize_text(question_2) if isinstance(question_2, str) else ""

        if not n1 or not n2:
            elapsed = (time.time() - start) * 1000
            return ComplexityAnalysis(processing_time=round(elapsed, 2), version=self.version)

        t1 = _tokenize(n1)
        t2 = _tokenize(n2)

        sent_count_1 = max(1, n1.count(".") + n1.count("!") + n1.count("?"))
        sent_count_2 = max(1, n2.count(".") + n2.count("!") + n2.count("?"))

        fre1 = flesch_reading_ease(n1)
        fre2 = flesch_reading_ease(n2)

        lc1 = lexical_complexity(t1)
        lc2 = lexical_complexity(t2)
        lex = round((lc1 + lc2) / 2, 4)

        sc1 = syntactic_complexity(t1, sent_count_1)
        sc2 = syntactic_complexity(t2, sent_count_2)
        syn = round((sc1 + sc2) / 2, 4)

        sm1 = semantic_complexity(t1)
        sm2 = semantic_complexity(t2)
        sem = round((sm1 + sm2) / 2, 4)

        e1_count = len(entity_analysis.entities_1) if entity_analysis else 0
        e2_count = len(entity_analysis.entities_2) if entity_analysis else 0
        total_entities = e1_count + e2_count
        total_words = len(t1) + len(t2)
        ent = round(entity_complexity(total_entities, max(total_words, 1)), 4)

        amb1 = ambiguity_score(t1, n1)
        amb2 = ambiguity_score(t2, n2)
        amb = round((amb1 + amb2) / 2, 4)

        read1 = readability_complexity(fre1)
        read2 = readability_complexity(fre2)
        read = round((read1 + read2) / 2, 4)

        rare = round((rare_token_density(t1) + rare_token_density(t2)) / 2, 4)
        ed = round((entity_density(e1_count, max(len(t1), 1)) + entity_density(e2_count, max(len(t2), 1))) / 2, 4)
        nd = round((numeric_density(t1) + numeric_density(t2)) / 2, 4)
        ad = round((abbreviation_density(t1) + abbreviation_density(t2)) / 2, 4)
        senc = round((sentence_complexity(t1, sent_count_1) + sentence_complexity(t2, sent_count_2)) / 2, 4)
        qls = round((question_length_score(question_1) + question_length_score(question_2)) / 2, 4)
        td = round((token_diversity(t1) + token_diversity(t2)) / 2, 4)

        overlap_ratio = similarity.word_overlap_ratio if similarity else 0.0
        type_mismatch = False
        if relationship_analysis and relationship_analysis.relationship_types:
            types = {r.relationship_type for r in relationship_analysis.relationship_types}
            type_mismatch = "negation_introduced" in types or "negation_removed" in types
        cd = round(
            comparison_difficulty(
                overlap_ratio=overlap_ratio,
                entity_delta=abs(e1_count - e2_count),
                type_mismatch=type_mismatch,
                relationship_count=len(relationship_analysis.relationship_types) if relationship_analysis else 0,
            ),
            4,
        )

        ce = round(confidence_estimate(amb, rare, ent), 4)
        rs = round(risk_score(cd, amb, ent), 4)

        overall = round((lex * 0.15 + syn * 0.10 + sem * 0.15 + ent * 0.15 + amb * 0.15 + read * 0.10 + cd * 0.20), 4)
        overall = max(0.0, min(1.0, overall))

        difficulty = score_to_difficulty(overall)

        parts = []
        if overall < 0.2:
            parts.append("Very simple comparison")
        elif overall < 0.4:
            parts.append("Moderately simple comparison")
        elif overall < 0.6:
            parts.append("Moderate complexity comparison")
        elif overall < 0.8:
            parts.append("Complex comparison")
        else:
            parts.append("Very complex comparison")
        if amb > 0.3:
            parts.append("with ambiguity concerns")
        if ent > 0.4:
            parts.append("requiring entity resolution")

        elapsed = round((time.time() - start) * 1000, 2)

        return ComplexityAnalysis(
            overall_complexity_score=overall,
            difficulty_level=difficulty,
            lexical_complexity=lex,
            syntactic_complexity=syn,
            semantic_complexity=sem,
            entity_complexity=ent,
            ambiguity_score=amb,
            readability_score=read,
            comparison_difficulty=cd,
            rare_token_density=rare,
            entity_density=ed,
            numeric_density=nd,
            abbreviation_density=ad,
            sentence_complexity=senc,
            question_length_score=qls,
            token_diversity=td,
            confidence_estimate=ce,
            risk_score=rs,
            reasoning_summary=". ".join(parts),
            processing_time=elapsed,
            version=self.version,
        )
