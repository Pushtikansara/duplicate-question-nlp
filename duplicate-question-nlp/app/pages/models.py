from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.runtime import get_model_resolution, get_runtime_context, load_model_config, render_model_runtime_message
from app.services.builder import build_model_status_table
from duplicate_question_app.config import is_new_embedding_model
from duplicate_question_app.week2_inference import is_week2_model


def render() -> None:
    st.title("Model Information")
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")

    try:
        resolution = get_model_resolution()
    except Exception as exc:
        st.error(f"Model info could not be loaded: {exc}")
        return

    if is_week2_model(selected_model):
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Model", selected_model)
        col2.metric("Decision Threshold", "0.50")
        col3.metric("Model Type", "Classical ML (TF-IDF + Linear Model)")
        st.dataframe(pd.DataFrame([{"Model Type": "TF-IDF + Logistic Regression / Linear SVM", "Feature Extraction": "TF-IDF with ngram_range=(1,2), max_features=5000", "Training Data": "Full Quora dataset (404,290 pairs)", "Label": "is_duplicate (binary)"}]), use_container_width=True, hide_index=True)
    elif is_new_embedding_model(selected_model):
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Model", selected_model)
        col2.metric("Decision Threshold", "0.50")
        col3.metric("Model Type", "Embedding / Cross-Encoder")
        st.info(f"{selected_model} is loaded via HuggingFace / sentence-transformers. It runs on CPU.")
    else:
        try:
            _, metadata, _ = get_runtime_context()
        except Exception:
            metadata = None
        if metadata and not isinstance(metadata, dict):
            model_config = load_model_config(metadata.model_dir)
            col1, col2, col3 = st.columns(3)
            col1.metric("Active Model", metadata.model_label)
            col2.metric("Decision Threshold", f"{metadata.decision_threshold:.2f}")
            col3.metric("Threshold Source", metadata.threshold_source)
            render_model_runtime_message(metadata)
            if model_config:
                st.subheader("Architecture Summary")
                config_subset = {"Architecture": ", ".join(model_config.get("architectures") or []), "Model Type": model_config.get("model_type"), "Number of Labels": model_config.get("num_labels"), "Vocabulary Size": model_config.get("vocab_size"), "Hidden Size": model_config.get("dim", model_config.get("hidden_size"))}
                st.dataframe(pd.DataFrame([config_subset]), use_container_width=True, hide_index=True)
        else:
            st.info(f"Model info for {selected_model} is not yet available.")

    st.subheader("Artifact Readiness")
    st.dataframe(build_model_status_table(resolution), use_container_width=True, hide_index=True)
