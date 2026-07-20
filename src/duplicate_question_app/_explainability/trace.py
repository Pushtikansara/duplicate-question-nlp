"""Model Explainability & Decision Trace — provides detailed reasoning
for every prediction, including per-model scores, feature contributions,
semantic features, and a full decision trace.

Every prediction includes:
- Cross Encoder Score (DeBERTa)
- BGE / E5 / MPNet Cosine Similarities
- TF-IDF Features (top contributing n-grams)
- Lexical Features (word overlap, character n-grams)
- Model Weights (adaptive ensemble)
- Final Probability
- Threshold
- Reason
- Confidence
- Decision Trace (full audit trail)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from duplicate_question_app._config.settings import AppPaths, get_app_paths
from duplicate_question_app._ensemble.agreement import get_agreement_report
from duplicate_question_app._ensemble.v1 import compute_adaptive_weights, get_adaptive_ensemble_prediction
from duplicate_question_app._inference.transformer import DuplicateQuestionInferenceService, load_model_and_tokenizer
from duplicate_question_app._models.embeddings import (
    get_sentence_transformer_model,
)
from duplicate_question_app._models.week2 import Week2InferenceService, check_week2_artifacts
from duplicate_question_app._preprocessing import normalize_question


@dataclass
class DecisionTrace:
    """Full decision trace for a single prediction."""

    # Input
    question1_original: str
    question2_original: str
    question1_normalized: str
    question2_normalized: str

    # Per-model scores
    tfidf_similarity: float | None = None  # TF-IDF cosine similarity
    bge_similarity: float | None = None  # BGE cosine similarity
    e5_similarity: float | None = None  # E5 cosine similarity
    mpnet_similarity: float | None = None  # MPNet cosine similarity
    cross_encoder_score: float | None = None  # DeBERTa NLI entailment ratio
    distilbert_w3_prob: float | None = None  # Week 3 probability
    distilbert_w4_prob: float | None = None  # Week 4 probability
    lr_prob: float | None = None  # Logistic Regression probability
    svm_prob: float | None = None  # SVM probability

    # Lexical features
    lexical_overlap: float = 0.0  # Word overlap ratio
    char_overlap: float = 0.0  # Character n-gram overlap
    word_count_diff: int = 0  # Word count difference
    char_count_diff: int = 0  # Character count difference
    top_tfidf_terms_q1: list[tuple[str, float]] = field(default_factory=list)
    top_tfidf_terms_q2: list[tuple[str, float]] = field(default_factory=list)

    # Semantic features
    abbreviation_count: int = 0
    abbreviations_list: list[str] = field(default_factory=list)
    synonyms_detected: list[str] = field(default_factory=list)
    named_entities_q1: list[str] = field(default_factory=list)
    named_entities_q2: list[str] = field(default_factory=list)

    # Adaptive weights
    adaptive_weights: dict[str, float] = field(default_factory=dict)
    semantic_depth: float = 0.0

    # Agreement
    num_models_voted: int = 0
    models_agreeing: list[str] = field(default_factory=list)
    models_disagreeing: list[str] = field(default_factory=list)
    agreement_score: float = 0.0
    is_unanimous: bool = False
    is_borderline: bool = False

    # Final decision
    final_probability: float = 0.5
    final_prediction: str = "Non-Duplicate"
    confidence: float = 0.0
    threshold: float = 0.5
    ensemble_method: str = "trimmed-mean"
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "questions": {
                "q1_original": self.question1_original,
                "q2_original": self.question2_original,
                "q1_normalized": self.question1_normalized,
                "q2_normalized": self.question2_normalized,
            },
            "per_model_scores": {
                "tfidf_similarity": self.tfidf_similarity,
                "bge_similarity": self.bge_similarity,
                "e5_similarity": self.e5_similarity,
                "mpnet_similarity": self.mpnet_similarity,
                "cross_encoder_score": self.cross_encoder_score,
                "distilbert_w3_prob": self.distilbert_w3_prob,
                "distilbert_w4_prob": self.distilbert_w4_prob,
                "lr_prob": self.lr_prob,
                "svm_prob": self.svm_prob,
            },
            "lexical_features": {
                "word_overlap": self.lexical_overlap,
                "char_overlap": self.char_overlap,
                "word_count_diff": self.word_count_diff,
                "char_count_diff": self.char_count_diff,
            },
            "semantic_features": {
                "abbreviation_count": self.abbreviation_count,
                "abbreviations": self.abbreviations_list,
                "synonyms": self.synonyms_detected,
                "named_entities_q1": self.named_entities_q1,
                "named_entities_q2": self.named_entities_q2,
            },
            "adaptive_weights": self.adaptive_weights,
            "semantic_depth": self.semantic_depth,
            "model_agreement": {
                "num_models_voted": self.num_models_voted,
                "models_agreeing": self.models_agreeing,
                "models_disagreeing": self.models_disagreeing,
                "agreement_score": self.agreement_score,
                "is_unanimous": self.is_unanimous,
                "is_borderline": self.is_borderline,
            },
            "decision": {
                "final_probability": self.final_probability,
                "final_prediction": self.final_prediction,
                "confidence": self.confidence,
                "threshold": self.threshold,
                "ensemble_method": self.ensemble_method,
                "latency_ms": self.latency_ms,
            },
        }


def extract_lexical_features(q1_norm: str, q2_norm: str) -> dict[str, Any]:
    """Extract lexical features from two normalized questions."""
    w1 = set(q1_norm.split())
    w2 = set(q2_norm.split())

    union = w1 | w2
    intersection = w1 & w2

    word_overlap = len(intersection) / max(1, len(union))

    # Character 3-gram overlap
    c1 = {q1_norm[i : i + 3] for i in range(len(q1_norm) - 2)}
    c2 = {q2_norm[i : i + 3] for i in range(len(q2_norm) - 2)}
    char_union = c1 | c2
    char_intersection = c1 & c2
    char_overlap = len(char_intersection) / max(1, len(char_union))

    return {
        "word_overlap": word_overlap,
        "char_overlap": char_overlap,
        "word_count_diff": abs(len(q1_norm.split()) - len(q2_norm.split())),
        "char_count_diff": abs(len(q1_norm) - len(q2_norm)),
    }


def extract_semantic_features(q1: str, q2: str) -> dict[str, Any]:
    """Extract semantic features from two questions."""
    abbrevs = re.findall(r"\b[A-Z]{2,5}\b", q1) + re.findall(r"\b[A-Z]{2,5}\b", q2)
    entities_q1 = re.findall(r"\b[A-Z][a-z]+\b", q1)
    entities_q2 = re.findall(r"\b[A-Z][a-z]+\b", q2)

    synonyms = set()
    synonym_pairs = [
        ("learn", "study"),
        ("benefits", "advantages"),
        ("tutorial", "guide"),
        ("difference", "distinction"),
        ("explain", "what is"),
        ("how to", "way to"),
    ]
    q1_lower, q2_lower = q1.lower(), q2.lower()
    for w1, w2 in synonym_pairs:
        if (w1 in q1_lower and w2 in q2_lower) or (w2 in q1_lower and w1 in q2_lower):
            synonyms.add(f"{w1}/{w2}")

    return {
        "abbreviation_count": len(set(abbrevs)),
        "abbreviations_list": list(set(abbrevs))[:5],
        "synonyms_detected": list(synonyms),
        "named_entities_q1": entities_q1[:5],
        "named_entities_q2": entities_q2[:5],
    }


def generate_decision_trace(
    q1: str,
    q2: str,
    paths: AppPaths | None = None,
) -> DecisionTrace:
    """Generate a full decision trace for a question pair.

    This is the main entry point. It collects all model scores, lexical
    and semantic features, adaptive weights, model agreement, and the
    final decision into a single DecisionTrace object.
    """
    import time

    start_time = time.time()

    if paths is None:
        from pathlib import Path

        paths = get_app_paths(Path(__file__).resolve().parents[3])

    q1_norm = normalize_question(q1, expand_abbrevs=True)
    q2_norm = normalize_question(q2, expand_abbrevs=True)

    trace = DecisionTrace(
        question1_original=q1,
        question2_original=q2,
        question1_normalized=q1_norm,
        question2_normalized=q2_norm,
    )

    # Lexical features
    lex = extract_lexical_features(q1_norm, q2_norm)
    trace.lexical_overlap = lex["word_overlap"]
    trace.char_overlap = lex["char_overlap"]
    trace.word_count_diff = lex["word_count_diff"]
    trace.char_count_diff = lex["char_count_diff"]

    # Semantic features
    sem = extract_semantic_features(q1, q2)
    trace.abbreviation_count = sem["abbreviation_count"]
    trace.abbreviations_list = sem["abbreviations_list"]
    trace.synonyms_detected = sem["synonyms_detected"]
    trace.named_entities_q1 = sem["named_entities_q1"]
    trace.named_entities_q2 = sem["named_entities_q2"]

    # Per-model scores (use cached get_sentence_transformer_model to avoid double loading)
    try:
        st_model = get_sentence_transformer_model("BGE-base-en-v1.5")
        emb = st_model.encode(q1_norm, normalize_embeddings=True)
        emb2 = st_model.encode(q2_norm, normalize_embeddings=True)
        trace.bge_similarity = float(emb @ emb2)
    except (ImportError, RuntimeError):
        pass

    try:
        st_model = get_sentence_transformer_model("E5-base-v2")
        emb = st_model.encode(f"query: {q1_norm}", normalize_embeddings=True)
        emb2 = st_model.encode(f"passage: {q2_norm}", normalize_embeddings=True)
        trace.e5_similarity = float(emb @ emb2)
    except (ImportError, RuntimeError):
        pass

    try:
        st_model = get_sentence_transformer_model("MPNet-base-v2")
        emb = st_model.encode(q1_norm, normalize_embeddings=True)
        emb2 = st_model.encode(q2_norm, normalize_embeddings=True)
        trace.mpnet_similarity = float(emb @ emb2)
    except (ImportError, RuntimeError):
        pass

    # Cross-encoder score
    try:
        ce = get_sentence_transformer_model("DeBERTa-v3 Cross-Encoder")
        scores = ce.predict([(q1_norm, q2_norm)], apply_softmax=True)[0]
        if len(scores) >= 3:
            contra, entail = float(scores[0]), float(scores[2])
            trace.cross_encoder_score = entail / (contra + entail) if (contra + entail) > 0.01 else 0.5
    except (ImportError, RuntimeError):
        pass

    # Week 2 models
    try:
        if all(check_week2_artifacts(paths).values()):
            w2 = Week2InferenceService(paths)
            _, prob_dup = w2.predict_proba(q1, q2, "TF-IDF + Logistic Regression (Week 2)")
            trace.lr_prob = prob_dup
            _, prob_dup = w2.predict_proba(q1, q2, "TF-IDF + Linear SVM (Week 2)")
            trace.svm_prob = prob_dup
    except FileNotFoundError:
        pass

    # Week 3/4 transformer models
    for m_name in ["DistilBERT (Week 3)", "Improved DistilBERT (Week 4)"]:
        try:
            model, tok, meta = load_model_and_tokenizer(paths, model_version=m_name)
            svc = DuplicateQuestionInferenceService(model, tok, meta)
            _, prob_dup = svc.predict_proba(q1, q2)
            if "Week 3" in m_name:
                trace.distilbert_w3_prob = prob_dup
            else:
                trace.distilbert_w4_prob = prob_dup
        except (FileNotFoundError, RuntimeError):
            pass

    # TF-IDF similarity (cosine similarity between TF-IDF vectors)
    try:
        if all(check_week2_artifacts(paths).values()):
            w2 = Week2InferenceService(paths)

            tfidf = w2._load_tfidf()
            v1 = tfidf.transform([q1_norm])
            v2 = tfidf.transform([q2_norm])
            from sklearn.metrics.pairwise import cosine_similarity

            trace.tfidf_similarity = float(cosine_similarity(v1, v2)[0, 0])
    except FileNotFoundError:
        pass

    # Adaptive weights
    try:
        weights = compute_adaptive_weights(q1, q2)
        trace.adaptive_weights = {
            "lexical": weights.lexical_weight,
            "transformer": weights.transformer_weight,
            "embedding": weights.embedding_weight,
            "cross_encoder": weights.cross_encoder_weight,
        }
        trace.semantic_depth = weights.semantic_depth
    except (ImportError, RuntimeError):
        pass

    # Agreement analysis
    try:
        report = get_agreement_report(q1, q2, paths)
        trace.num_models_voted = report.num_models_voted
        trace.models_agreeing = report.models_agreeing
        trace.models_disagreeing = report.models_disagreeing
        trace.agreement_score = report.agreement_score
        trace.is_unanimous = report.unanimous
        trace.is_borderline = report.is_borderline
    except FileNotFoundError:
        pass

    # Final decision (use adaptive ensemble)
    try:
        ensemble_result = get_adaptive_ensemble_prediction(q1, q2, paths)
        trace.final_probability = ensemble_result["prob_duplicate"]
        trace.final_prediction = ensemble_result["prediction"]
        trace.confidence = ensemble_result["confidence"]
        trace.threshold = ensemble_result["threshold"]
        trace.ensemble_method = "adaptive-weighted"
    except FileNotFoundError:
        # Fall back to trimmed mean
        try:
            report = get_agreement_report(q1, q2, paths)
            trace.final_probability = report.ensemble_prob
            trace.final_prediction = "Duplicate" if report.majority_label == 1 else "Non-Duplicate"
            trace.confidence = report.confidence_mean
        except FileNotFoundError:
            pass

    trace.latency_ms = (time.time() - start_time) * 1000
    return trace
