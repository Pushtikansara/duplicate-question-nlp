from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from app.services.runtime import get_runtime_context
from app.utils.constants import _detect_question_columns
from duplicate_question_app._profiling import get_profiler
from duplicate_question_app._visualization.plots import create_batch_summary_figure


def render() -> None:
    st.title("Batch CSV Prediction")
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")
    prediction_mode = st.session_state.get("prediction_mode", "fusion")

    try:
        _, metadata, _ = get_runtime_context()
    except Exception as exc:
        st.error(f"Model could not be loaded: {exc}")
        return

    if isinstance(metadata, dict):
        model_label = metadata.get("model_label", "Unknown")
        decision_threshold = metadata.get("decision_threshold", 0.5)
    elif metadata:
        model_label = metadata.model_label
        decision_threshold = metadata.decision_threshold
    else:
        model_label = selected_model
        decision_threshold = 0.5

    mode_labels = {
        "cross_encoder_only": "CrossEncoder Only",
        "semantic_only": "Semantic Intelligence Only",
        "fusion": "Fusion (Recommended)",
        "cross_encoder_dominant": "CrossEncoder Dominant",
        "semantic_dominant": "Semantic Dominant",
        "confidence_weighted": "Confidence Weighted",
        "adaptive": "Adaptive",
    }

    col1, col2, col3 = st.columns(3)
    col1.caption(f"Model: **{model_label}**")
    col2.caption(f"Mode: **{mode_labels.get(prediction_mode, prediction_mode)}**")
    col3.caption(f"Threshold: **{decision_threshold:.2f}**")

    template_df = pd.DataFrame(
        {
            "q1": ["How do I learn Python?", "What is the capital of France?"],
            "q2": ["How can I learn Python programming?", "Which city is the largest in France?"],
        }
    )
    st.download_button(
        "Download CSV Template",
        data=template_df.to_csv(index=False).encode("utf-8"),
        file_name="duplicate_question_template.csv",
        mime="text/csv",
    )

    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is None:
        st.info("Upload a CSV file with `q1/q2`, `question1/question2`, or `sentence1/sentence2` columns.")
        return

    try:
        batch_df = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"Unable to read the uploaded CSV: {exc}")
        return

    column_pair = _detect_question_columns(batch_df)
    if column_pair is None:
        st.error("Could not find valid question columns in the uploaded CSV.")
        return

    question1_column, question2_column = column_pair
    prepared_df = batch_df.copy()
    prepared_df[question1_column] = prepared_df[question1_column].fillna("").astype(str).str.strip()
    prepared_df[question2_column] = prepared_df[question2_column].fillna("").astype(str).str.strip()
    valid_mask = prepared_df[question1_column].ne("") & prepared_df[question2_column].ne("")

    col1, col2, col3 = st.columns(3)
    col1.metric("Uploaded Rows", f"{len(batch_df):,}")
    col2.metric("Valid Rows", f"{int(valid_mask.sum()):,}")
    col3.metric("Skipped Rows", f"{int((~valid_mask).sum()):,}")

    if (~valid_mask).any():
        st.warning("Rows with empty question text will be skipped.")
    st.subheader("Preview")
    st.dataframe(batch_df.head(10), width="stretch")

    st.number_input(
        "Batch size", min_value=8, max_value=512, value=64, step=8, help="Number of pairs to process at once"
    )

    if st.button("Run Batch Prediction", use_container_width=True, type="primary"):
        if not valid_mask.any():
            st.error("No valid rows found.")
            return

        profiler = get_profiler()
        profiler.enable()

        try:
            question_pairs = list(
                zip(
                    prepared_df.loc[valid_mask, question1_column],
                    prepared_df.loc[valid_mask, question2_column],
                    strict=False,
                )
            )

            total = len(question_pairs)
            progress_bar = st.progress(0, text="Starting batch prediction...")
            status_text = st.empty()
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
            metrics_col1.metric("Total Pairs", total)
            eta_metric = metrics_col2.empty()
            avg_lat_metric = metrics_col3.empty()
            throughput_metric = metrics_col4.empty()

            start_time = time.time()
            results_list = []

            from app.utils.constants import (
                _get_assessment_dict,
                _get_decision_fusion,
                _get_prediction_mode,
                _get_semantic_pipeline,
            )
            from ares.inference.dispatcher import InferenceDispatcher

            mode = _get_prediction_mode()
            semantic_pipeline = _get_semantic_pipeline() if mode != "cross_encoder_only" else None

            base_results = []
            for q1, q2 in question_pairs:
                result = InferenceDispatcher.predict(
                    model_name=selected_model,
                    question1=q1,
                    question2=q2,
                )
                base_results.append(
                    {
                        "predicted_label": result.predicted_label,
                        "prediction": result.prediction,
                        "confidence": result.confidence,
                        "prob_duplicate": result.prob_duplicate,
                        "prob_non_duplicate": result.prob_non_duplicate,
                        "model_label": result.model_name,
                        "latency_ms": result.latency_ms,
                    }
                )

            for idx, (q1, q2) in enumerate(question_pairs):
                row = base_results[idx] if idx < len(base_results) else {}
                row = dict(row) if isinstance(row, dict) else {}

                assessment = None
                assessment_dict = None
                semantic_sim = 0.5
                ce_score = float(row.get("prob_duplicate", 0.5))

                if semantic_pipeline is not None:
                    assessment, pipe_meta = semantic_pipeline.assess(q1, q2)
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
                throughput = (idx + 1) / elapsed if elapsed > 0 else 0

                progress = (idx + 1) / total
                progress_bar.progress(progress, text=f"Processing pair {idx + 1}/{total}")
                status_text.caption(
                    f"Status: {idx + 1}/{total} pairs | Avg: {avg_latency * 1000:.0f}ms | ETA: {remaining:.0f}s"
                )
                eta_metric.metric("ETA", f"{remaining:.0f}s" if remaining > 0 else "Done")
                avg_lat_metric.metric("Avg Latency", f"{avg_latency * 1000:.0f}ms")
                throughput_metric.metric("Throughput", f"{throughput:.1f} pairs/s")

            progress_bar.progress(1.0, text="Complete!")
            status_text.success(f"Processed {total} pairs in {time.time() - start_time:.1f}s")

            valid_results_df = pd.DataFrame(results_list)

        except Exception as exc:
            st.error(f"Batch prediction failed: {exc}")
            return

        merged_results = batch_df.copy()
        merged_results["batch_status"] = "Skipped: empty question text"
        valid_index = prepared_df.index[valid_mask]
        merged_results.loc[valid_index, "batch_status"] = "Predicted"
        for column in valid_results_df.columns:
            merged_results[column] = pd.NA
            merged_results.loc[valid_index, column] = (
                valid_results_df[column].to_numpy()
                if hasattr(valid_results_df[column], "to_numpy")
                else valid_results_df[column].values
            )

        st.success(f"Generated predictions for {len(merged_results):,} question pairs.")
        st.dataframe(merged_results, width="stretch")

        pred_df = merged_results[merged_results["batch_status"] == "Predicted"]
        if not pred_df.empty:
            has_ce = "prob_duplicate" in pred_df.columns
            has_sem = "semantic_similarity" in pred_df.columns
            has_fusion = "fusion_score" in pred_df.columns

            sem_cols = []
            if has_sem:
                sem_cols.append("semantic_similarity")
            if has_ce:
                sem_cols.append("prob_duplicate")
            if has_fusion:
                sem_cols.append("fusion_score")

            if len(sem_cols) >= 2:
                st.subheader("Score Distribution")
                st.line_chart(pred_df[sem_cols])

            if "num_conflicts" in pred_df.columns:
                st.subheader("Conflict Statistics")
                conflict_counts = pred_df["num_conflicts"].value_counts().sort_index()
                st.bar_chart(conflict_counts)

        summary_figure = create_batch_summary_figure(pred_df)
        st.pyplot(summary_figure, clear_figure=True)

        export_cols = [question1_column, question2_column, "batch_status", "prediction"]
        extra_cols = [
            "fusion_score",
            "fusion_prediction",
            "semantic_similarity",
            "num_conflicts",
            "concept_overlap",
            "intent_match",
            "entity_overlap",
            "evidence_summary",
        ]
        for c in extra_cols:
            if c in merged_results.columns:
                export_cols.append(c)

        export_df = merged_results[[c for c in export_cols if c in merged_results.columns]]
        st.download_button(
            "Download Prediction Results",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="duplicate_question_predictions.csv",
            mime="text/csv",
        )


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
