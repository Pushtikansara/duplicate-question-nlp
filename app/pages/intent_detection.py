from __future__ import annotations

import streamlit as st

from duplicate_question_app.intent_detector import get_intent_details


def render() -> None:
    st.title("Question Intent Detection")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Classify question intent (Definition, Comparison, Installation, Tutorial, Troubleshooting, etc.). "
        "Mismatched intents reduce duplicate probability.</p>",
        unsafe_allow_html=True,
    )

    with st.form("intent_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Analyze Intent", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Detecting intent..."):
            try:
                details = get_intent_details(q1, q2)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2, col3 = st.columns(3)
        col1.metric("Intent Penalty", f"{details['mismatch_penalty']:.2%}")
        col2.metric("Q1 Intent", details["q1_intent"].replace("_", " ").title())
        col3.metric("Q2 Intent", details["q2_intent"].replace("_", " ").title())

        st.caption(f"Compatible: {'✅ Yes' if details['compatible'] else '❌ No'}")
        st.caption(f"Reason: {details['mismatch_reason']}")

        with st.expander("Details"):
            st.json(
                {
                    "q1_scores": details["q1_all_scores"],
                    "q2_scores": details["q2_all_scores"],
                    "q1_patterns": details["q1_patterns"],
                    "q2_patterns": details["q2_patterns"],
                }
            )
