from __future__ import annotations

import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1200px;}
        .stApp header {background: transparent !important;}
        .hero-card {
            padding: 1.5rem 1.8rem;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(37,99,235,0.10), rgba(14,165,233,0.06));
            border: 1px solid rgba(37,99,235,0.15);
            margin-bottom: 1.2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .dashboard-card {
            padding: 1.2rem 1.4rem;
            border-radius: 16px;
            border: 1px solid rgba(148,163,184,0.2);
            background: rgba(255,255,255,0.5);
            margin-bottom: 0.8rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            transition: box-shadow 0.2s ease;
        }
        .dashboard-card:hover {box-shadow: 0 4px 12px rgba(0,0,0,0.06);}
        .metric-value {font-size: 1.8rem; font-weight: 700; color: #1E293B;}
        .metric-label {font-size: 0.8rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;}
        .small-note {color: #64748B; font-size: 0.88rem;}
        .section-header {font-size: 1.1rem; font-weight: 600; color: #0F172A; margin: 1.2rem 0 0.6rem 0;}
        .status-badge {display: inline-block; padding: 0.15rem 0.6rem; border-radius: 12px; font-size: 0.78rem; font-weight: 500;}
        .status-ready {background: #DCFCE7; color: #166534;}
        .status-missing {background: #FEE2E2; color: #991B1B;}
        .status-download {background: #DBEAFE; color: #1E40AF;}
        </style>
        """,
        unsafe_allow_html=True,
    )
