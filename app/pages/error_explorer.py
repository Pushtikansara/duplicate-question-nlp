from __future__ import annotations

import pandas as pd
import streamlit as st

from app.utils.constants import PATHS
from duplicate_question_app.agreement_engine import get_agreement_report
from duplicate_question_app.error_analyzer import categorize_error, classify_hardness


def render() -> None:
    st.title("Hard Example Mining")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Test specific question pairs to see error categorization and hardness classification.</p>",
        unsafe_allow_html=True,
    )

    with st.form("hard_example_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=80)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=80)
        has_ground_truth = st.checkbox("I know the ground truth label")
        true_label = None
        if has_ground_truth:
            true_label = st.selectbox("Ground truth", ["Non-Duplicate", "Duplicate"])
            true_label = 0 if true_label == "Non-Duplicate" else 1
        submitted = st.form_submit_button("Analyze", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Analyzing..."):
            try:
                report = get_agreement_report(q1, q2, PATHS)
                errors = categorize_error(q1, q2, report.predicted_label, true_label, report.prob_mean)
                hardness = classify_hardness(
                    report.prob_mean, report.confidence_mean, report.agreement_score, report.predicted_label, true_label
                )
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Prediction", report.prediction)
        col2.metric("Hardness", hardness.upper())
        col3.metric("Agreement", f"{report.agreement_score:.0%}")
        col4.metric("Models Voting", report.num_models_voted)

        st.subheader("Error Categories")
        for err in errors:
            if err.detected:
                status = "⚠️" if err.name != "No Error Detected" else "✅"
                st.markdown(f"{status} **{err.name}** — {err.description}")
                if err.details:
                    st.caption(f"   Details: {err.details}")

        st.subheader("Model Votes")
        vote_data = [
            {
                "Model": v.model_name,
                "Prob": f"{v.prob_duplicate:.4f}",
                "Vote": "Duplicate" if v.predicted_label == 1 else "Non-Duplicate",
            }
            for v in report.votes
            if v.error is None
        ]
        st.dataframe(pd.DataFrame(vote_data), use_container_width=True, hide_index=True)
