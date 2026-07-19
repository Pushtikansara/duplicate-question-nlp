from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from duplicate_question_app.config import MODEL_CHOICES
from duplicate_question_app.performance_optimizer import (
    benchmark_inference,
    clear_all_caches,
    get_embedding_cache,
    get_preprocessing_cache,
)


def render() -> None:
    st.title("Performance Optimizer")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Cache embeddings, batch encode, memoize preprocessing. Benchmark inference latency.</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Cache Stats", "Benchmark", "Optimization Tips"])

    with tab1:
        st.subheader("Cache Statistics")
        emb_cache = get_embedding_cache()
        prep_cache = get_preprocessing_cache()

        col1, col2 = st.columns(2)
        with col1:
            stats = emb_cache.stats()
            st.metric("Embedding Cache Hits", stats.hits)
            st.metric("Embedding Cache Misses", stats.misses)
            st.metric("Hit Rate", f"{stats.hit_rate:.1%}")
            st.metric("Cache Size", f"{stats.size}/{stats.max_size}")
        with col2:
            stats = prep_cache.stats()
            st.metric("Preprocessing Cache Hits", stats.hits)
            st.metric("Preprocessing Cache Misses", stats.misses)
            st.metric("Hit Rate", f"{stats.hit_rate:.1%}")
            st.metric("Cache Size", f"{stats.size}/{stats.max_size}")

        if st.button("Clear All Caches"):
            clear_all_caches()
            st.success("Caches cleared!")

    with tab2:
        st.subheader("Benchmark Inference")
        model_names = st.multiselect("Models to benchmark", MODEL_CHOICES, default=MODEL_CHOICES[:3])
        n_pairs = st.slider("Number of test pairs", 10, 500, 50)
        iterations = st.slider("Iterations", 1, 10, 3)

        if st.button("Run Benchmark"):
            with st.spinner("Benchmarking..."):
                try:
                    test_pairs = [
                        ("How to install Python?", "How to setup Python?"),
                        ("Java vs JavaScript", "Difference between Java and JS"),
                        ("Docker uninstall", "Remove Docker"),
                        ("AWS vs Azure", "Compare AWS and Azure"),
                        ("TensorFlow vs PyTorch", "TF vs PyTorch comparison"),
                    ] * (n_pairs // 5 + 1)
                    test_pairs = test_pairs[:n_pairs]

                    results = benchmark_inference(test_pairs, model_names, iterations)
                    bench_df = pd.DataFrame(results).T
                    st.dataframe(bench_df, use_container_width=True)

                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(bench_df.index, bench_df["per_pair_ms"])
                    ax.set_ylabel("ms per pair")
                    ax.set_title("Inference Latency per Pair")
                    plt.xticks(rotation=45, ha="right")
                    st.pyplot(fig, clear_figure=True)
                except Exception as exc:
                    st.error(f"Benchmark failed: {exc}")

    with tab3:
        st.subheader("Optimization Tips")
        st.markdown("""
        - **Embedding Cache**: Reuses computed embeddings for repeated questions (major speedup for batch)
        - **Preprocessing Cache**: Memoizes text normalization results
        - **Batch Encoding**: Encodes multiple texts in a single forward pass
        - **Model Preloading**: Load all models at startup to avoid cold starts
        - **LRU Eviction**: Prevents unbounded memory growth
        - **Thread Safety**: All caches are thread-safe for concurrent requests
        """)
