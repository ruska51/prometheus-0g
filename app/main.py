"""Streamlit entry point for the Prometheus-0g dashboard (stage 8, ADR-034).

Run: ``.venv/Scripts/python -m streamlit run app/main.py``. Pages live in app/pages/; they only call the fif
package and read generated artefacts.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

st.set_page_config(page_title="Prometheus-0g - Will it burn on the Moon?", page_icon=":fire:", layout="wide")

pages = [
    st.Page("pages/overview.py", title="Overview", icon=":material/home:", default=True),
    st.Page("pages/insights.py", title="Insights", icon=":material/insights:"),
    st.Page("pages/scenario.py", title="Moon-base scenario", icon=":material/science:"),
    st.Page("pages/risk_map.py", title="Risk map", icon=":material/map:"),
    st.Page("pages/investigations.py", title="Investigations", icon=":material/table_view:"),
    st.Page("pages/data_explorer.py", title="Data explorer", icon=":material/dataset:"),
    st.Page("pages/validation.py", title="Validation", icon=":material/fact_check:"),
    st.Page("pages/method.py", title="Method & sources", icon=":material/menu_book:"),
]
st.navigation(pages).run()
