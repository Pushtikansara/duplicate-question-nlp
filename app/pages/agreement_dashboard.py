from __future__ import annotations

import pandas as pd
import streamlit as st

from app.utils.constants import PATHS
from duplicate_question_app.agreement_dashboard import (
    analyze_model_agreement, compute_model_leaderboard, generate_agreement_summary
)


def render() -> None:
    st.title("Model Agreement Dashboard")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Deep agreement analysis: Agreement %, Confidence spread, Entropy, Variance, "
        "Strongest/Weakest/Most Influential models.</p>",
        unsafe_allow_html=True,
    )

    with st.form("agreement_dash_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Analyze Agreement", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Analyzing model agreement..."):
            try:
                dashboard = analyze_model_agreement(q1, q2, PATHS)
                summary = generate_agreement_summary(q1, q2, PATHS)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        st.subheader("Agreement Summary")
        for key, value in summary.items():
            if key != 'interpretation':
                st.caption(f"{key}: {value}")
        if 'interpretation' in summary:
            st.info(summary['interpretation'])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Agreement %", f"{dashboard.agreement_percentage:.0%}")
        col2.metric("Confidence Spread", f"{dashboard.confidence_spread:.1%}")
        col3.metric("Prediction Entropy", f"{dashboard.prediction_entropy:.3f}")
        col4.metric("Prob Variance", f"{dashboard.probability_variance:.4f}")

        st.subheader("Model Votes")
        vote_df = pd.DataFrame(dashboard.model_votes)
        st.dataframe(vote_df, use_container_width=True, hide_index=True)

        if dashboard.models_disagreeing:
            st.warning(f"Models disagreeing: {', '.join(dashboard.models_disagreeing)}")
        else:
            st.success("All models agree!")

        st.subheader("Calibration Status")
        cal_df = pd.DataFrame(list(dashboard.calibration_status.items()), columns=["Model", "Status"])
        st.dataframe(cal_df, use_container_width=True, hide_index=True)
