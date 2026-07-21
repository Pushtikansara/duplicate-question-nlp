from __future__ import annotations

import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --primary: #2563EB;
            --primary-light: #3B82F6;
            --primary-dark: #1D4ED8;
            --primary-bg: rgba(37,99,235,0.08);
            --primary-border: rgba(37,99,235,0.15);
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #64748B;
            --bg-card: rgba(255,255,255,0.8);
            --bg-page: #F8FAFC;
            --border-light: rgba(148,163,184,0.2);
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.04);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.06);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
        }

        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 1200px;
        }
        .stApp header {background: transparent !important;}

        /* ===== Sidebar ===== */
        div[data-testid="stSidebar"] {
            background: #FFFFFF;
            border-right: 1px solid var(--border-light);
            min-width: 280px;
        }
        div[data-testid="stSidebar"] .stButton button {
            text-align: left;
            padding: 0.4rem 0.75rem;
            font-size: 0.85rem;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            border-radius: var(--radius-sm);
            transition: all 0.15s ease;
            font-weight: 400;
            margin-bottom: 1px;
        }
        div[data-testid="stSidebar"] .stButton button:hover {
            background: var(--primary-bg);
            color: var(--primary);
        }
        div[data-testid="stSidebar"] .stButton button[type="primary"] {
            background: var(--primary-bg);
            color: var(--primary);
            font-weight: 500;
        }
        div[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
            background: rgba(37,99,235,0.15);
        }
        div[data-testid="stSidebar"] .stSelectbox {
            margin-bottom: 0.5rem;
        }

        /* ===== Radio Navigation ===== */
        div[data-testid="stSidebar"] div[data-testid="stRadio"] label {
            padding: 0.3rem 0.5rem;
            font-size: 0.85rem;
            border-radius: 6px;
            transition: all 0.1s;
        }
        div[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
            background: var(--primary-bg);
        }
        div[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"] {
            background: rgba(37,99,235,0.12);
            font-weight: 500;
        }

        /* ===== Cards ===== */
        .hero-card {
            padding: 1.5rem 1.8rem;
            border-radius: var(--radius-xl);
            background: linear-gradient(135deg, rgba(37,99,235,0.10), rgba(14,165,233,0.06));
            border: 1px solid var(--primary-border);
            margin-bottom: 1.2rem;
            box-shadow: var(--shadow-sm);
        }
        .dashboard-card {
            padding: 1.2rem 1.4rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-light);
            background: var(--bg-card);
            margin-bottom: 0.8rem;
            box-shadow: var(--shadow-sm);
            transition: box-shadow 0.2s ease, transform 0.15s ease;
        }
        .dashboard-card:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-1px);
        }
        .feature-card {
            padding: 1.5rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-light);
            background: var(--bg-card);
            text-align: center;
            transition: all 0.2s ease;
        }
        .feature-card:hover {
            border-color: var(--primary-border);
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }
        .feature-card .icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .feature-card .title {
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        .feature-card .desc {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }

        /* ===== Metrics ===== */
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--text-primary);
        }
        .metric-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* ===== Typography ===== */
        .small-note {
            color: var(--text-muted);
            font-size: 0.85rem;
        }
        .section-header {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 1.5rem 0 0.75rem 0;
            padding-bottom: 0.35rem;
            border-bottom: 2px solid var(--primary-bg);
        }
        .page-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }
        .page-subtitle {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
        }

        /* ===== Status Badges ===== */
        .status-badge {
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        .status-ready {
            background: #DCFCE7;
            color: #166534;
        }
        .status-missing {
            background: #FEE2E2;
            color: #991B1B;
        }
        .status-download {
            background: #DBEAFE;
            color: #1E40AF;
        }

        /* ===== DataFrames ===== */
        div[data-testid="stDataFrame"] {
            border-radius: var(--radius-sm);
            border: 1px solid var(--border-light);
        }
        div[data-testid="stDataFrame"] thead tr th {
            background: var(--primary-bg);
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        /* ===== Tabs ===== */
        button[data-baseweb="tab"] {
            font-size: 0.85rem;
            font-weight: 500;
        }
        div[data-baseweb="tab-list"] {
            gap: 0.25rem;
            padding: 0 0 0.25rem 0;
            overflow-x: auto;
            flex-wrap: nowrap;
        }

        /* ===== Buttons ===== */
        .stButton button[kind="primary"] {
            border-radius: var(--radius-sm);
            font-weight: 500;
        }
        .stButton button[kind="secondary"] {
            border-radius: var(--radius-sm);
        }

        /* ===== Expandable Sections ===== */
        .streamlit-expanderHeader {
            font-size: 0.9rem;
            font-weight: 600;
        }

        /* ===== Form Elements ===== */
        div[data-testid="stForm"] {
            border: 1px solid var(--border-light);
            border-radius: var(--radius-md);
            padding: 1.5rem;
            background: var(--bg-card);
        }
        div[data-testid="stForm"] .stTextArea textarea {
            border-radius: var(--radius-sm);
            border: 1px solid #E2E8F0;
        }
        div[data-testid="stForm"] .stTextArea textarea:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(37,99,235,0.15);
        }

        /* ===== Alerts ===== */
        div[data-testid="stAlert"] {
            border-radius: var(--radius-sm);
            font-size: 0.85rem;
        }

        /* ===== Progress Bar ===== */
        div[data-testid="stProgress"] > div {
            border-radius: 8px;
        }

        /* ===== Selectbox ===== */
        div[data-baseweb="select"] > div {
            border-radius: var(--radius-sm);
        }

        /* ===== Input ===== */
        input[type="text"], input[type="number"], input[type="search"] {
            border-radius: var(--radius-sm) !important;
        }

        /* ===== Spacing improvements ===== */
        div.row-widget.stColumns {
            gap: 0.75rem;
        }
        section.main div[data-testid="column"] {
            gap: 0.5rem;
        }
        div.stMetric {
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-sm);
            padding: 0.75rem 1rem;
            box-shadow: var(--shadow-sm);
        }
        div.stMetric:hover {
            box-shadow: var(--shadow-md);
        }

        /* ===== Responsive ===== */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem !important;
            }
            .hero-card {
                padding: 1rem;
            }
            .feature-card {
                padding: 1rem;
            }
        }

        /* ===== Caption styling ===== */
        .stCaption {
            color: var(--text-muted) !important;
            font-size: 0.8rem !important;
        }

        /* ===== Code blocks ===== */
        code {
            background: #F1F5F9 !important;
            padding: 0.1rem 0.3rem !important;
            border-radius: 4px !important;
            font-size: 0.8rem !important;
        }

        /* ===== Spinner ===== */
        div[data-testid="stSpinner"] {
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
