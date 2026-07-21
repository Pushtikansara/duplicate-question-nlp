from __future__ import annotations

import pandas as pd
import streamlit as st

from app.utils.constants import PATHS, _get_semantic_pipeline
from duplicate_question_app._ensemble.v2 import adaptive_ensemble_predict
from duplicate_question_app._explainability.text import (
    ExplanationLevel,
    generate_counterfactual_explanation,
    generate_explanation,
    generate_feature_importance,
)


def render() -> None:
    st.title("Advanced Explainability — Plain English + Semantic Evidence")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Generate human-readable explanations for any prediction. "
        "See exactly why the model decided Duplicate or Non-Duplicate, "
        "including Semantic Intelligence Engine evidence.</p>",
        unsafe_allow_html=True,
    )

    with st.form("explainer_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        level = st.selectbox("Explanation level", [lev.value for lev in ExplanationLevel], index=1)
        submitted = st.form_submit_button("Generate Explanation", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Generating explanation with Semantic Intelligence..."):
            try:
                result = adaptive_ensemble_predict(q1, q2, PATHS)
                explanation = generate_explanation(q1, q2, result, ExplanationLevel(level), PATHS)

                semantic_pipeline = _get_semantic_pipeline()
                assessment, meta = semantic_pipeline.assess(q1, q2)
            except Exception as exc:
                st.error(f"Explanation failed: {exc}")
                return

        st.subheader("Explanation")
        st.text(explanation.to_text())

        if assessment:
            st.subheader("🧠 Semantic Intelligence Evidence")
            assessment_dict = assessment.to_dict()

            evidence = assessment_dict.get("supporting_evidence", [])
            for e in evidence:
                status = e.get("status", "info")
                msg = e.get("message", "")
                if status == "match":
                    st.success(f"✓ {msg}")
                elif status in ("mismatch", "conflict"):
                    st.error(f"✗ {msg}")
                elif status in ("warning", "low_overlap"):
                    st.warning(f"⚠ {msg}")
                else:
                    st.info(f"ℹ {msg}")

            conflicts = assessment_dict.get("conflicts", [])
            if conflicts:
                st.subheader("⚠ Detected Conflicts")
                for c in conflicts:
                    st.error(f"**{c.get('conflict_type', 'unknown')}**: {c.get('description', '')}")

            co = assessment_dict.get("concept_overlap", {})
            ins = assessment_dict.get("intent_similarity", {})

            missing_a = co.get("missing_in_a", [])
            missing_b = co.get("missing_in_b", [])
            if missing_a:
                st.warning(f"⚠ Missing in Q1: {', '.join(missing_a)}")
            if missing_b:
                st.warning(f"⚠ Missing in Q2: {', '.join(missing_b)}")

            st.subheader("Similarity Scores")
            col1, col2, col3 = st.columns(3)
            col1.metric("Semantic Similarity", f"{assessment_dict.get('semantic_similarity', 0):.2%}")
            col2.metric("Concept Overlap", f"{co.get('overlap_score', 0):.2%}")
            col3.metric("Intent Match", f"{ins.get('score', 0):.2%}")

            with st.expander("Full Semantic Assessment", expanded=False):
                st.json(assessment_dict)
        else:
            st.info("Semantic Intelligence Engine could not produce evidence for these inputs.")

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
