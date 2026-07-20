from __future__ import annotations

import streamlit as st

from duplicate_question_app._linguistics.contradiction import detect_contradiction


def render() -> None:
    st.title("Contradiction Detection")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Detect contradictory meaning between questions using pattern matching and NLI models. "
        "Contradictions strongly indicate non-duplicate.</p>",
        unsafe_allow_html=True,
    )

    with st.form("contradiction_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Detect Contradiction", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Detecting contradictions..."):
            try:
                result = detect_contradiction(q1, q2)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2, col3 = st.columns(3)
        col1.metric("Has Contradiction", "✅ Yes" if result.has_contradiction else "❌ No")
        col2.metric("Contradiction Score", f"{result.contradiction_score:.2%}")
        col3.metric("Types", len(result.contradiction_types))

        if result.details:
            st.subheader("Contradiction Details")
            for detail in result.details.split("; "):
                st.write(f"• {detail}")

        if result.nli_scores:
            st.subheader("NLI Scores")
            st.json(result.nli_scores)
