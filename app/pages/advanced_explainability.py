from __future__ import annotations

import pandas as pd
import streamlit as st

from app.utils.constants import PATHS
from duplicate_question_app.adaptive_ensemble_v2 import adaptive_ensemble_predict
from duplicate_question_app.explainer import (
    ExplanationLevel,
    generate_counterfactual_explanation,
    generate_explanation,
    generate_feature_importance,
)


def render() -> None:
    st.title("Advanced Explainability — Plain English")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Generate human-readable explanations for any prediction. "
        "See exactly why the model decided Duplicate or Non-Duplicate.</p>",
        unsafe_allow_html=True,
    )

    with st.form("explainer_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        level = st.selectbox("Explanation level", [lev.value for lev in ExplanationLevel], index=1)
        submitted = st.form_submit_button("Generate Explanation", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Generating explanation..."):
            try:
                result = adaptive_ensemble_predict(q1, q2, PATHS)
                explanation = generate_explanation(q1, q2, result, ExplanationLevel(level), PATHS)
            except Exception as exc:
                st.error(f"Explanation failed: {exc}")
                return

        st.subheader("Explanation")
        st.text(explanation.to_text())

        st.subheader("Counterfactual Analysis")
        counterfactual = generate_counterfactual_explanation(q1, q2, result, PATHS)
        st.write(f"**Current**: {counterfactual['current_prediction']} ({counterfactual['current_probability']:.1%})")
        st.write(f"**Target**: {counterfactual['target_prediction']}")
        st.write(f"**Difficulty**: {counterfactual['difficulty']}")
        for change in counterfactual["required_changes"]:
            st.write(f"• **{change['factor']}**: {change['current']} → {change['action']} (Impact: {change['impact']})")

        st.subheader("Feature Importance")
        importance = generate_feature_importance(result)
        if importance:
            imp_df = pd.DataFrame(importance)
            st.dataframe(imp_df, use_container_width=True, hide_index=True)
