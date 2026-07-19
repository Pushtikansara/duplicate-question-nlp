from __future__ import annotations

import pandas as pd
import streamlit as st

from app.utils.constants import PATHS
from duplicate_question_app.adaptive_ensemble_v2 import adaptive_ensemble_predict


def render() -> None:
    st.title("Adaptive Ensemble V2 — Dynamic Confidence Routing")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Next-generation ensemble with dynamic weight routing based on input features. "
        "Weights adapt: high lexical mismatch → boost cross-encoder/TF-IDF; "
        "high semantic agreement → boost transformers.</p>",
        unsafe_allow_html=True,
    )

    with st.form("ensemble_v2_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Run Adaptive Ensemble V2", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Running adaptive ensemble..."):
            try:
                result = adaptive_ensemble_predict(q1, q2, PATHS)
            except Exception as exc:
                st.error(f"Prediction failed: {exc}")
                return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Prediction", result["prediction"])
        col2.metric("Probability", f"{result['prob_duplicate']:.2%}")
        col3.metric("Confidence", f"{result['confidence']:.2%}")
        col4.metric("Latency", f"{result['latency_ms']:.1f} ms")

        st.subheader("Dynamic Weights")
        weights = result["adaptive_weights"]
        weight_df = pd.DataFrame([
            ("TF-IDF", weights.get("tfidf_weight", 0)),
            ("Transformer", weights.get("transformer_weight", 0)),
            ("Embedding", weights.get("embedding_weight", 0)),
            ("Cross-Encoder", weights.get("cross_encoder_weight", 0)),
        ], columns=["Model Group", "Weight"])
        st.bar_chart(weight_df.set_index("Model Group"))
        st.dataframe(weight_df, use_container_width=True, hide_index=True)

        st.subheader("Feature Analysis")
        features = result["features"]
        feat_df = pd.DataFrame([
            ("Lexical Overlap", features.get("lexical_overlap", 0)),
            ("Semantic Depth", features.get("semantic_depth", 0)),
            ("Entity Penalty", features.get("entity_penalty", 0)),
            ("Intent Penalty", features.get("intent_penalty", 0)),
            ("Negation Penalty", features.get("negation_penalty", 0)),
            ("Contradiction Penalty", features.get("contradiction_penalty", 0)),
            ("Lexical Penalty", features.get("lexical_penalty", 0)),
            ("Model Agreement", features.get("model_agreement", 0)),
            ("Prob Std", features.get("prob_std", 0)),
            ("Is Borderline", features.get("is_borderline", False)),
        ], columns=["Feature", "Value"])
        st.dataframe(feat_df, use_container_width=True, hide_index=True)

        st.subheader("Model Contributions")
        contrib = result.get("feature_breakdown", {})
        if contrib:
            contrib_df = pd.DataFrame([
                {"Model": k, "Prob": v.get("prob_dup", v.get("prob_duplicate", 0)), "Weight": v.get("weight", 0), "Weighted": v.get("weighted_contribution", 0)}
                for k, v in contrib.items()
            ])
            st.dataframe(contrib_df, use_container_width=True, hide_index=True)

        st.info(f"Reason: {result.get('reason', 'N/A')}")
