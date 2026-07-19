from __future__ import annotations

import streamlit as st


def render_footer() -> None:
    st.markdown("---")
    st.caption("Production-grade Streamlit application for Duplicate Question Detection with 9 models.")
