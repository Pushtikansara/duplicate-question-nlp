from __future__ import annotations

import pandas as pd
import streamlit as st

from duplicate_question_app._linguistics.lexical import compute_lexical_penalty, get_lexical_penalty


def render() -> None:
    st.title("Lexical Penalty Engine")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Analyze lexical mismatches: different nouns, verbs, named entities, software names, "
        "programming languages, and products. Penalties applied when key terms differ.</p>",
        unsafe_allow_html=True,
    )

    with st.form("lexical_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Analyze Lexical Mismatch", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Analyzing lexical mismatch..."):
            try:
                penalty, details = get_lexical_penalty(q1, q2)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2 = st.columns(2)
        col1.metric("Lexical Penalty", f"{penalty:.2%}")
        col2.metric("Details", details)

        result = compute_lexical_penalty(q1, q2)

        tab1, tab2, tab3 = st.tabs(["Q1 Tokens", "Q2 Tokens", "Overlap Scores"])
        with tab1:
            for k, v in result.q1_tokens.items():
                if v:
                    st.write(f"**{k}**: {sorted(v)}")
        with tab2:
            for k, v in result.q2_tokens.items():
                if v:
                    st.write(f"**{k}**: {sorted(v)}")
        with tab3:
            df = pd.DataFrame([{"Type": k, "Overlap": f"{v:.2%}"} for k, v in result.overlap_scores.items()])
            st.dataframe(df, use_container_width=True, hide_index=True)

        if result.penalties:
            st.subheader("Penalties Applied")
            for ptype, pval in result.penalties.items():
                st.write(f"• {ptype.value}: {pval:.2%}")
            for detail in result.details:
                st.caption(detail)
