from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from duplicate_question_app._inference.cache import get_cache
from duplicate_question_app._profiling import get_profiler
from duplicate_question_app._semantic_intelligence.semantic_pipeline import SemanticPipelineService


def _render_cache_status() -> None:
    cache = get_cache()
    stats = cache.stats()
    st.subheader("Cache Status")
    cache_rows = []
    for name, stat in stats.items():
        cache_rows.append(
            {
                "Cache": name.replace("_", " ").title(),
                "Size": stat.size,
                "Hits": stat.hits,
                "Misses": stat.misses,
                "Hit Rate": f"{stat.hit_rate:.1%}",
            }
        )
    st.dataframe(pd.DataFrame(cache_rows), use_container_width=True, hide_index=True)


def _render_profiling_data() -> None:
    profiler = get_profiler()
    report = profiler.get_report()
    if report:
        st.subheader("Pipeline Timings")
        st.dataframe(pd.DataFrame(report), use_container_width=True, hide_index=True)


def render() -> None:
    st.title("Semantic Debugger")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Inspect every internal object produced by the Semantic Intelligence Engine pipeline: "
        "LinguisticProfile, SemanticRepresentation, SemanticAssessment, and DecisionFusion.</p>",
        unsafe_allow_html=True,
    )

    pipeline = SemanticPipelineService()

    with st.form("debug_form"):
        question1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        question2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        col1, col2 = st.columns(2)
        with col1:
            use_cache = st.checkbox("Use Cache", value=True, help="Use LRU cache for semantic representations")
        with col2:
            show_raw = st.checkbox("Show Raw JSON", value=False)
        submitted = st.form_submit_button("Run Semantic Pipeline", use_container_width=True)

    _render_cache_status()
    _render_profiling_data()

    if submitted and question1.strip() and question2.strip():
        with st.spinner("Running full semantic pipeline..."):
            t0 = time.perf_counter()
            assessment, rep_a, rep_b, meta = pipeline.assess_with_representations(
                question1, question2, use_cache=use_cache
            )
            total_ms = (time.perf_counter() - t0) * 1000

        if assessment is None:
            st.error(f"Pipeline failed: {meta.get('error', 'unknown error')}")
            return

        st.success(f"Pipeline completed in {meta.get('total_ms', total_ms):.1f} ms")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Semantic Similarity", f"{assessment.semantic_similarity:.2%}")
        col2.metric("Holistic Confidence", f"{assessment.confidence:.2%}")
        col3.metric("Recommendation", assessment.recommendation.value)
        col4.metric("Processing Time", f"{assessment.processing_metadata.processing_time_ms:.1f}ms")

        st.info(f"**Reason**: {assessment.recommendation_reason}")

        tab_rep_a, tab_rep_b, tab_assessment, tab_fusion, tab_meta, tab_weights = st.tabs(
            [
                "Representation A",
                "Representation B",
                "Semantic Assessment",
                "Decision Fusion",
                "Metadata",
                "Confidence Breakdown",
            ]
        )

        with tab_rep_a:
            if rep_a:
                st.subheader("Concepts")
                if rep_a.concepts:
                    concepts_df = pd.DataFrame(
                        [
                            {"id": c.id, "label": c.label, "normalized": c.normalized_form, "confidence": c.confidence}
                            for c in rep_a.concepts
                        ]
                    )
                    st.dataframe(concepts_df, use_container_width=True)
                else:
                    st.info("No concepts")

                st.subheader("Entities")
                if rep_a.entities:
                    st.dataframe(pd.DataFrame(rep_a.entities), use_container_width=True)
                else:
                    st.info("No entities")

                st.subheader("Relationships")
                if rep_a.relationships:
                    rels_df = pd.DataFrame(
                        [
                            {
                                "source": r.source_id,
                                "target": r.target_id,
                                "type": r.relation_type,
                                "confidence": r.confidence,
                            }
                            for r in rep_a.relationships
                        ]
                    )
                    st.dataframe(rels_df, use_container_width=True)
                else:
                    st.info("No relationships")

                st.subheader("Semantic Graph")
                if rep_a.semantic_graph:
                    st.json(
                        rep_a.semantic_graph.to_dict()
                        if hasattr(rep_a.semantic_graph, "to_dict")
                        else str(rep_a.semantic_graph)
                    )
                else:
                    st.info("No semantic graph")

                st.subheader("Processing Metadata")
                pm = rep_a.processing_metadata
                st.json(
                    {
                        "total_concepts": pm.total_concepts,
                        "total_relations": pm.total_relations,
                        "total_roles": pm.total_roles,
                        "ambiguity_count": pm.ambiguity_count,
                        "processing_time_ms": pm.processing_time_ms,
                        "stages": pm.stages,
                    }
                )

                if show_raw:
                    st.subheader("Raw Object")
                    st.json(rep_a.to_dict())
            else:
                st.error("Representation A could not be built.")

        with tab_rep_b:
            if rep_b:
                st.subheader("Concepts")
                if rep_b.concepts:
                    concepts_df = pd.DataFrame(
                        [
                            {"id": c.id, "label": c.label, "normalized": c.normalized_form, "confidence": c.confidence}
                            for c in rep_b.concepts
                        ]
                    )
                    st.dataframe(concepts_df, use_container_width=True)
                else:
                    st.info("No concepts")

                st.subheader("Entities")
                if rep_b.entities:
                    st.dataframe(pd.DataFrame(rep_b.entities), use_container_width=True)
                else:
                    st.info("No entities")

                st.subheader("Relationships")
                if rep_b.relationships:
                    rels_df = pd.DataFrame(
                        [
                            {
                                "source": r.source_id,
                                "target": r.target_id,
                                "type": r.relation_type,
                                "confidence": r.confidence,
                            }
                            for r in rep_b.relationships
                        ]
                    )
                    st.dataframe(rels_df, use_container_width=True)
                else:
                    st.info("No relationships")

                st.subheader("Semantic Graph")
                if rep_b.semantic_graph:
                    st.json(
                        rep_b.semantic_graph.to_dict()
                        if hasattr(rep_b.semantic_graph, "to_dict")
                        else str(rep_b.semantic_graph)
                    )
                else:
                    st.info("No semantic graph")

                if show_raw:
                    st.subheader("Raw Object")
                    st.json(rep_b.to_dict())
            else:
                st.error("Representation B could not be built.")

        with tab_assessment:
            assessment_dict = assessment.to_dict()

            st.subheader("Similarity Scores")
            scores = {
                "Semantic Similarity": assessment.semantic_similarity,
                "Concept Overlap": assessment.concept_overlap.overlap_score,
                "Entity Overlap": assessment.entity_overlap.overlap_score,
                "Intent Similarity": assessment.intent_similarity.score,
                "Relation Similarity": assessment.relation_similarity.score,
                "Context Similarity": assessment.context_similarity.score,
                "Confidence": assessment.confidence,
            }
            scores_df = pd.DataFrame([{"Component": k, "Score": v} for k, v in scores.items()])
            st.dataframe(scores_df, use_container_width=True)

            st.subheader("Conflicts")
            if assessment.conflicts:
                conflicts_df = pd.DataFrame(
                    [
                        {
                            "type": c.conflict_type,
                            "description": c.description,
                            "severity": c.severity,
                            "source": c.source,
                        }
                        for c in assessment.conflicts
                    ]
                )
                st.dataframe(conflicts_df, use_container_width=True)
            else:
                st.success("No conflicts detected.")

            st.subheader("Supporting Evidence")
            for e in assessment.supporting_evidence:
                status_icon = {
                    "match": "✅",
                    "mismatch": "❌",
                    "conflict": "⚔️",
                    "warning": "⚠️",
                    "info": "ℹ️",
                    "low_overlap": "⚠️",
                    "low_confidence": "⚠️",
                    "partial": "🔶",
                    "uncertain": "❓",
                }.get(e.status, "ℹ️")
                st.markdown(
                    f"{status_icon} **{e.category}** [{e.status}]: {e.message} (confidence: {e.confidence:.2f})"
                )

            if show_raw:
                st.subheader("Raw Assessment JSON")
                st.json(assessment_dict)

        with tab_fusion:
            from duplicate_question_app._semantic_intelligence.fusion import DecisionFusion, FusionStrategy

            strategy_options = {
                "fusion": "Fusion (Balanced)",
                "cross_encoder_dominant": "CrossEncoder Dominant",
                "semantic_dominant": "Semantic Dominant",
                "confidence_weighted": "Confidence Weighted",
                "adaptive": "Adaptive",
            }
            strat = st.selectbox(
                "Fusion Strategy",
                options=list(strategy_options.keys()),
                format_func=lambda k: strategy_options[k],
                key="debug_fusion_strat",
            )

            ce_score = st.slider("Simulated CrossEncoder Score", 0.0, 1.0, 0.7, 0.05)
            strategy_map = {
                "fusion": FusionStrategy.FUSION,
                "cross_encoder_dominant": FusionStrategy.CROSS_ENCODER_DOMINANT,
                "semantic_dominant": FusionStrategy.SEMANTIC_DOMINANT,
                "confidence_weighted": FusionStrategy.CONFIDENCE_WEIGHTED,
                "adaptive": FusionStrategy.ADAPTIVE,
            }
            fusion = DecisionFusion(strategy=strategy_map[strat])
            assessment_dict_fusion = assessment.to_dict()
            fusion_result = fusion.fuse(ce_score, assessment_dict_fusion)

            st.subheader("Fusion Result")
            st.json(fusion_result)

            st.subheader("Fusion Weights Used")
            weights = fusion_result.get("weights_used", {})
            if weights:
                weights_df = pd.DataFrame([{"Component": k, "Weight": v} for k, v in weights.items()])
                weights_df["Percentage"] = weights_df["Weight"].apply(lambda x: f"{x:.1%}")
                st.dataframe(weights_df, use_container_width=True)

            component_scores = fusion_result.get("component_scores", {})
            if component_scores:
                st.subheader("Component Scores")
                scores_df2 = pd.DataFrame(
                    [{"Component": k.replace("_", " ").title(), "Score": v} for k, v in component_scores.items()]
                )
                st.dataframe(scores_df2, use_container_width=True)

            st.info(f"**Explanation**: {fusion_result.get('explanation', 'N/A')}")

            st.metric("Final Score", f"{fusion_result.get('final_score', 0):.2%}")
            st.metric("Final Prediction", fusion_result.get("final_prediction", "Unknown"))

        with tab_meta:
            st.subheader("Pipeline Timing Metadata")
            meta_df = pd.DataFrame([{"Stage": k, "Time (ms)": v} for k, v in meta.get("stages", {}).items()])
            if not meta_df.empty:
                st.dataframe(meta_df, use_container_width=True)

            st.subheader("Processing Metadata (from Assessment)")
            pm = assessment.processing_metadata
            st.json(
                {
                    "processing_time_ms": pm.processing_time_ms,
                    "stages": pm.stages,
                    "components_used": pm.components_used,
                }
            )

        with tab_weights:
            st.subheader("Confidence Breakdown")
            confidence_detail = assessment.confidence_detail if hasattr(assessment, "confidence_detail") else {}
            if confidence_detail:
                st.json(confidence_detail)
                raw_scores = confidence_detail.get("raw_scores", {})
                weighted_scores = confidence_detail.get("weighted_scores", {})
                weights = confidence_detail.get("weights", {})

                if raw_scores:
                    st.markdown("**Raw Scores**")
                    raw_df = pd.DataFrame([{"Component": k, "Score": v} for k, v in raw_scores.items()])
                    st.dataframe(raw_df, use_container_width=True)

                if weights:
                    st.markdown("**Weights**")
                    w_df = pd.DataFrame([{"Component": k, "Weight": f"{v:.1%}"} for k, v in weights.items()])
                    st.dataframe(w_df, use_container_width=True)

                if weighted_scores:
                    st.markdown("**Weighted Scores**")
                    ws_df = pd.DataFrame([{"Component": k, "Score": v} for k, v in weighted_scores.items()])
                    st.dataframe(ws_df, use_container_width=True)
            else:
                st.info("No confidence detail available")

    else:
        st.info("Enter two questions and click 'Run Semantic Pipeline' to see the debug view.")
