from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app._config.settings import get_app_paths

PATHS = get_app_paths(PROJECT_ROOT)

from app.services.cache import get_cache

_cache_manager = get_cache()
_model_cache = _cache_manager._model_cache


def _detect_question_columns(df: pd.DataFrame) -> tuple[str, str] | None:
    candidate_pairs = [
        ("q1", "q2"),
        ("question1", "question2"),
        ("sentence1", "sentence2"),
    ]
    for col1, col2 in candidate_pairs:
        if col1 in df.columns and col2 in df.columns:
            return col1, col2
    return None


_SEMANTIC_PIPELINE = None


def _get_semantic_pipeline():
    global _SEMANTIC_PIPELINE
    if _SEMANTIC_PIPELINE is None:
        from duplicate_question_app._semantic_intelligence.semantic_pipeline import SemanticPipelineService

        _SEMANTIC_PIPELINE = SemanticPipelineService()
    return _SEMANTIC_PIPELINE


_SEMANTIC_FUSION = None


def _get_decision_fusion(strategy: str = "fusion"):
    global _SEMANTIC_FUSION
    from duplicate_question_app._semantic_intelligence.fusion import DecisionFusion, FusionStrategy

    strategy_map = {
        "cross_encoder_only": FusionStrategy.CROSS_ENCODER_ONLY,
        "cross_encoder_dominant": FusionStrategy.CROSS_ENCODER_DOMINANT,
        "semantic_only": FusionStrategy.SEMANTIC_ONLY,
        "semantic_dominant": FusionStrategy.SEMANTIC_DOMINANT,
        "confidence_weighted": FusionStrategy.CONFIDENCE_WEIGHTED,
        "adaptive": FusionStrategy.ADAPTIVE,
        "learned_weighting": FusionStrategy.LEARNED_WEIGHTING,
    }
    fs = strategy_map.get(strategy, FusionStrategy.FUSION)
    _SEMANTIC_FUSION = DecisionFusion(strategy=fs)
    return _SEMANTIC_FUSION


def _get_prediction_mode() -> str:
    import streamlit as st

    return st.session_state.get("prediction_mode", "fusion")


def _get_assessment_dict(assessment) -> dict[str, Any] | None:
    if assessment is None:
        return None
    if hasattr(assessment, "to_dict"):
        ad = assessment.to_dict()
    elif isinstance(assessment, dict):
        ad = assessment
    else:
        return None
    return ad


def get_model_prediction(service: Any, selected_model: str, question1: str, question2: str) -> dict[str, Any]:
    from duplicate_question_app._config.settings import is_ensemble_model, is_new_embedding_model
    from duplicate_question_app._models.embeddings import get_ensemble_prediction, predict_with_sentence_transformer
    from duplicate_question_app._models.week2 import is_week2_model

    base_result = None
    if is_week2_model(selected_model):
        base_result = service.predict_single(question1, question2, selected_model)
    elif is_ensemble_model(selected_model):
        base_result = get_ensemble_prediction(question1, question2)
    elif is_new_embedding_model(selected_model):
        base_result = predict_with_sentence_transformer(selected_model, question1, question2)
    else:
        base_result = service.predict_single(question1, question2)

    mode = _get_prediction_mode()
    cross_encoder_score = float(base_result.get("prob_duplicate", 0.5))

    semantic_assessment = None
    semantic_pipeline_meta = {}
    semantic_similarity = 0.5
    confidence_from_assessment = 0.5

    if mode != "cross_encoder_only":
        semantic_pipeline = _get_semantic_pipeline()
        assessment, pipe_meta = semantic_pipeline.assess(question1, question2)
        semantic_assessment = _get_assessment_dict(assessment)
        semantic_pipeline_meta = pipe_meta
        confidence_from_assessment = assessment.confidence if assessment is not None else 0.5
        semantic_similarity = assessment.semantic_similarity if assessment is not None else 0.5

    fusion = _get_decision_fusion(mode)
    if mode == "semantic_only":
        fusion_result = fusion.fuse(cross_encoder_score=0.0, semantic_assessment=semantic_assessment)
        base_result["predicted_label"] = 1 if semantic_similarity >= 0.5 else 0
        base_result["prediction"] = "Duplicate" if semantic_similarity >= 0.5 else "Non-Duplicate"
        base_result["confidence"] = confidence_from_assessment
        base_result["prob_duplicate"] = semantic_similarity
    elif mode == "cross_encoder_only":
        fusion_result = fusion.fuse(cross_encoder_score=cross_encoder_score, semantic_assessment=None)
    else:
        fusion_result = fusion.fuse(cross_encoder_score=cross_encoder_score, semantic_assessment=semantic_assessment)

    base_result["semantic_assessment"] = semantic_assessment
    base_result["semantic_pipeline_meta"] = semantic_pipeline_meta
    base_result["semantic_similarity"] = semantic_similarity
    base_result["fusion_result"] = fusion_result
    base_result["prediction_mode"] = mode

    if mode != "cross_encoder_only":
        base_result["fusion_score"] = fusion_result.get("fusion_score", fusion_result.get("final_score"))
        base_result["final_prediction"] = fusion_result.get("final_prediction", base_result.get("prediction"))

    return base_result


def run_batch_prediction(service: Any, selected_model: str, question_pairs: list[tuple[str, str]]) -> pd.DataFrame:
    import time

    from duplicate_question_app._config.settings import is_ensemble_model, is_new_embedding_model
    from duplicate_question_app._models.embeddings import (
        get_ensemble_prediction,
        predict_batch_sentence_transformer,
    )
    from duplicate_question_app._models.week2 import is_week2_model
    from duplicate_question_app._profiling import get_profiler

    semantic_pipeline = _get_semantic_pipeline() if _get_prediction_mode() != "cross_encoder_only" else None
    mode = _get_prediction_mode()

    results_list = []

    if is_week2_model(selected_model):
        base_results = service.predict_batch(question_pairs, selected_model)
        base_results = base_results.to_dict("records") if isinstance(base_results, pd.DataFrame) else list(base_results)
    elif is_ensemble_model(selected_model):
        base_results = []
        for q1, q2 in question_pairs:
            base_results.append(get_ensemble_prediction(q1, q2))
    elif is_new_embedding_model(selected_model):
        base_results = predict_batch_sentence_transformer(selected_model, question_pairs, batch_size=64)
    else:
        base_results = []
        for q1, q2 in question_pairs:
            base_results.append(service.predict_single(q1, q2))

    total = len(question_pairs)
    start_time = time.time()
    profiler = get_profiler()

    for idx, (q1, q2) in enumerate(question_pairs):
        row = base_results[idx] if idx < len(base_results) else {}
        row = dict(row) if isinstance(row, dict) else {}

        assessment = None
        assessment_dict = None
        semantic_sim = 0.5
        ce_score = float(row.get("prob_duplicate", 0.5))

        if semantic_pipeline is not None:
            t0 = time.perf_counter()
            assessment, pipe_meta = semantic_pipeline.assess(q1, q2)
            profiler.record("batch_semantic_assess", (time.perf_counter() - t0) * 1000)
            assessment_dict = _get_assessment_dict(assessment)
            semantic_sim = assessment.semantic_similarity if assessment is not None else 0.5

        fusion = _get_decision_fusion(mode)
        if mode == "semantic_only":
            fusion_result = fusion.fuse(cross_encoder_score=0.0, semantic_assessment=assessment_dict)
        elif mode == "cross_encoder_only":
            fusion_result = fusion.fuse(cross_encoder_score=ce_score, semantic_assessment=None)
        else:
            fusion_result = fusion.fuse(cross_encoder_score=ce_score, semantic_assessment=assessment_dict)

        row["semantic_similarity"] = semantic_sim
        row["fusion_score"] = fusion_result.get("fusion_score", fusion_result.get("final_score"))
        row["fusion_prediction"] = fusion_result.get("final_prediction", row.get("prediction"))
        row["semantic_assessment_json"] = str(assessment_dict) if assessment_dict else ""
        row["evidence_summary"] = _summarize_evidence(assessment_dict) if assessment_dict else ""
        row["prediction_mode"] = mode

        if assessment_dict:
            row["num_conflicts"] = len(assessment_dict.get("conflicts", []))
            row["concept_overlap"] = assessment_dict.get("concept_overlap", {}).get("overlap_score", 0.0)
            row["intent_match"] = assessment_dict.get("intent_similarity", {}).get("score", 0.0)
            row["entity_overlap"] = assessment_dict.get("entity_overlap", {}).get("overlap_score", 0.0)
        else:
            row["num_conflicts"] = 0
            row["concept_overlap"] = 0.0
            row["intent_match"] = 0.0
            row["entity_overlap"] = 0.0

        if mode != "cross_encoder_only":
            row["prob_duplicate"] = fusion_result.get("final_score", row.get("prob_duplicate", 0.5))
            row["confidence"] = fusion_result.get("final_score", row.get("confidence", 0.5))
            row["prediction"] = fusion_result.get("final_prediction", row.get("prediction", "Non-Duplicate"))
            row["predicted_label"] = 1 if row["prediction"] == "Duplicate" else 0

        results_list.append(row)

        elapsed = time.time() - start_time
        avg_latency = elapsed / (idx + 1)
        remaining = avg_latency * (total - idx - 1)
        if idx % max(1, total // 20) == 0 or idx == total - 1:
            import streamlit as st

            st.caption(
                f"Batch progress: {idx + 1}/{total} | Avg: {avg_latency * 1000:.0f}ms/pair | ETA: {remaining:.0f}s"
            )

    return pd.DataFrame(results_list)


def _summarize_evidence(assessment_dict: dict | None) -> str:
    if not assessment_dict:
        return ""
    evidence = assessment_dict.get("supporting_evidence", [])
    if not evidence:
        return ""
    parts = []
    for e in evidence[:5]:
        if isinstance(e, dict):
            parts.append(f"{e.get('status', '?')}: {e.get('message', '')}")
    return " | ".join(parts)
