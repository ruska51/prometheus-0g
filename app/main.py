"""Streamlit entry point for the Prometheus-0g dashboard (stage 8, ADR-034).

Run: ``.venv/Scripts/python -m streamlit run app/main.py``. Pages live in app/views/ (not app/pages/: Streamlit would auto-register that folder and bypass st.navigation); they only call the fif
package and read generated artefacts.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from i18n import language_selector, t  # noqa: E402

st.set_page_config(page_title=t("Prometheus-0g - Will it burn on the Moon?"), page_icon=":fire:", layout="wide")
language_selector()

pages = [
    st.Page("views/overview.py", title=t("Overview"), icon=":material/home:", default=True),
    st.Page("views/insights.py", title=t("Insights"), icon=":material/insights:"),
    st.Page("views/assistant.py", title=t("Ask the data"), icon=":material/forum:"),
    st.Page("views/scenario.py", title=t("Moon-base scenario"), icon=":material/science:"),
    st.Page("views/risk_map.py", title=t("Risk map"), icon=":material/map:"),
    st.Page("views/investigations.py", title=t("Investigations"), icon=":material/table_view:"),
    st.Page("views/data_explorer.py", title=t("Data explorer"), icon=":material/dataset:"),
    st.Page("views/validation.py", title=t("Validation"), icon=":material/fact_check:"),
    st.Page("views/method.py", title=t("Method & sources"), icon=":material/menu_book:"),
]
st.navigation(pages).run()
