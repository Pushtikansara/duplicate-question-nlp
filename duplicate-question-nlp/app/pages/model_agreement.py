from __future__ import annotations

import pandas as pd
import streamlit as st

from app.utils.constants import PATHS
from duplicate_question_app.explainability import generate_decision_trace


def render() -> None:
    st.title("Model Agreement & Decision Trace")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Analyze how all 9 models agree/disagree, view adaptive weights, "
        "lexical features, semantic features, and a full decision trace.</p>",
        unsafe_allow_html=True,
    )

    with st.form("agreement_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=80)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=80)
        submitted = st.form_submit_button("Analyze Agreement", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Collecting predictions from all 9 models..."):
            try:
                trace = generate_decision_trace(q1, q2, PATHS)
                td = trace.to_dict()
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        decision = td["decision"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Final Prediction", decision["final_prediction"])
        col2.metric("Probability", f"{decision['final_probability']:.2%}")
        col3.metric("Confidence", f"{decision['confidence']:.2%}")
        col4.metric("Ensemble Method", decision["ensemble_method"])

        agreement = td["model_agreement"]
        st.subheader("🤝 Model Agreement")
        agree_col, disagree_col, score_col, unan_col = st.columns(4)
        agree_col.metric("Models Agreeing", len(agreement["models_agreeing"]))
        disagree_col.metric("Models Disagreeing", len(agreement["models_disagreeing"]))
        score_col.metric("Agreement Score", f"{agreement['agreement_score']:.0%}")
        unan_col.metric("Unanimous", "✅ Yes" if agreement["is_unanimous"] else "❌ No")

        tab_models, tab_lexical, tab_semantic, tab_weights, tab_scores = st.tabs([
            "Per-Model Scores", "Lexical Features", "Semantic Features",
            "Adaptive Weights", "Per-Model Similarities",
        ])

        with tab_models:
            scores = td["per_model_scores"]
            rows = []
            for name, prob in scores.items():
                if prob is not None:
                    rows.append({"Model": name.replace("_", " ").title(), "Probability": prob})
            if rows:
                st.dataframe(pd.DataFrame(rows).sort_values("Probability", ascending=False),
                           use_container_width=True, hide_index=True)
            st.info("💡 Models with probability > 0.5 vote 'Duplicate', < 0.5 vote 'Non-Duplicate'.")

        with tab_lexical:
            lex = td["lexical_features"]
            cols = st.columns(4)
            cols[0].metric("Word Overlap", f"{lex['word_overlap']:.1%}")
            cols[1].metric("Char Overlap", f"{lex['char_overlap']:.1%}")
            cols[2].metric("Word Count Diff", lex["word_count_diff"])
            cols[3].metric("Char Count Diff", lex["char_count_diff"])
            if lex["word_overlap"] < 0.2:
                st.warning("⚠️ Low lexical overlap — semantic understanding is essential for this pair.")
            elif lex["word_overlap"] > 0.6:
                st.success("✅ High lexical overlap — lexical models (TF-IDF) are well-suited here.")

        with tab_semantic:
            sem = td["semantic_features"]
            cols = st.columns(3)
            cols[0].metric("Abbreviations", sem["abbreviation_count"])
            cols[1].metric("Synonyms", len(sem["synonyms"]))
            cols[2].metric("Semantic Depth", f"{td['semantic_depth']:.2f}")
            if sem["abbreviations"]:
                st.info(f"📝 Abbreviations detected: {', '.join(sem['abbreviations'])}")
            if sem["named_entities_q1"] or sem["named_entities_q2"]:
                st.caption(f"Named entities — Q1: {sem['named_entities_q1'][:3]}, Q2: {sem['named_entities_q2'][:3]}")

        with tab_weights:
            w = td["adaptive_weights"]
            if w:
                weight_df = pd.DataFrame([
                    ("Lexical (TF-IDF)", w.get("lexical", 0)),
                    ("Transformer (DistilBERT)", w.get("transformer", 0)),
                    ("Embedding (BGE/E5/MPNet)", w.get("embedding", 0)),
                    ("Cross-Encoder (DeBERTa)", w.get("cross_encoder", 0)),
                ], columns=["Model Group", "Weight"])
                st.bar_chart(weight_df.set_index("Model Group"))
                st.dataframe(weight_df, use_container_width=True, hide_index=True)
                st.info("💡 Weights adapt based on lexical overlap, abbreviation presence, and synonym detection.")

        with tab_scores:
            sims = td["per_model_scores"]
            sim_data = {}
            for k, v in sims.items():
                if "similarity" in k or "score" in k:
                    sim_data[k.replace("_", " ").title()] = v
            if any(v is not None for v in sim_data.values()):
                st.dataframe(
                    pd.DataFrame([(k, f"{v:.4f}") for k, v in sim_data.items() if v is not None],
                                 columns=["Metric", "Value"]),
                    use_container_width=True, hide_index=True,
                )
