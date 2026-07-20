#!/usr/bin/env python3
"""Streamlit entry point for Duplicate Question Detection.

This file lives at the project root so that sys.path[0] always points
to the project root, allowing absolute imports like ``from app._entry import main``
to resolve correctly.

Usage:
    streamlit run run_app.py
    python -m app
"""

from __future__ import annotations

from app._entry import main

main()
