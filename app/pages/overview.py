from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Project Overview")
    st.write(
        "This project identifies whether two questions express the same intent. The workflow evolved from data cleaning and classical NLP baselines to transformer fine-tuning and advanced embedding models."
    )

    overview_col1, overview_col2 = st.columns([1.2, 1])
    with overview_col1:
        st.subheader("Week-by-Week Progress")
        st.markdown("""
        - **Week 1:** Data collection, cleaning, exploratory data analysis, and preprocessing
        - **Week 2:** TF-IDF, Word2Vec, Sentence-BERT features, and classical ML baselines
        - **Week 3:** DistilBERT fine-tuning with a reusable inference pipeline
        - **Week 4:** Threshold tuning, class imbalance handling, and error analysis
        - **Week 5:** Streamlit application, dashboarding, deployment assets
        - **Phase 2:** BGE, E5, MPNet, DeBERTa, and Semantic Ensemble
        """)
    with overview_col2:
        st.subheader("Current App Behavior")
        st.markdown("""
        - Loads **Week 4 improved model** when its Hugging Face artifacts are present
        - Falls back to **Week 3 DistilBERT** automatically
        - **Week 2 models** loaded from joblib files
        - **Phase 2 models** loaded from HuggingFace/sentence-transformers
        - **Semantic Ensemble** averages predictions from all available models
        """)
