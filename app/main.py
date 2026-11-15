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


def _refresh_code() -> None:
    """Streamlit reruns this script and the pages on every interaction but does not reload modules outside app/views
    (the fif package in src/, app helpers). After a deploy (git pull on Streamlit Cloud) a running server would keep the
    old modules and stale cached results. When any source file is newer than what this process loaded, reload the
    modules (dependencies first) and clear the caches."""
    import importlib

    here = Path(__file__).resolve()
    files = [*(here.parents[1] / "src" / "fif").rglob("*.py"), *here.parent.glob("*.py")]
    stamp = max(f.stat().st_mtime for f in files)
    previous = getattr(sys, "_prometheus_code_stamp", None)
    sys._prometheus_code_stamp = stamp
    if previous is None or previous == stamp:  # first run of this process, or nothing changed
        return
    names = [
        n
        for n in list(sys.modules)
        if n == "fif"
        or n.startswith("fif.")
        or n in ("i18n", "common", "flame_view", "module_view", "glossary", "theme", "blueprint", "pilot_ui")
    ]
    for n in reversed(names):  # sys.modules keeps import order: reversed = dependencies before their importers
        try:
            importlib.reload(sys.modules[n])
        except Exception:  # a module that cannot be reloaded keeps its current version
            pass
    st.cache_data.clear()
    st.cache_resource.clear()


_refresh_code()

from i18n import language_selector, t  # noqa: E402

st.set_page_config(page_title=t("Prometheus-0g - Fire on the Moon"), page_icon=":fire:", layout="wide")
language_selector()

from theme import inject as inject_theme  # noqa: E402

inject_theme()


pages = {  # three groups: start here, explore the Moon base, check the evidence (ADR-054)
    t("Start here"): [
        st.Page("views/overview.py", title=t("Overview"), icon=":material/home:", default=True),
        st.Page("views/assistant.py", title=t("Ask the data"), icon=":material/forum:"),
    ],
    t("Moon base"): [
        st.Page("views/scenario.py", title=t("Moon-base scenario"), icon=":material/science:"),
        st.Page("views/module.py", title=t("Module fire"), icon=":material/local_fire_department:"),
        st.Page("views/base.py", title=t("Base planner"), icon=":material/hub:"),
        st.Page("views/risk_map.py", title=t("Risk map"), icon=":material/map:"),
    ],
    t("Evidence"): [
        st.Page("views/insights.py", title=t("Insights"), icon=":material/insights:"),
        st.Page("views/investigations.py", title=t("Investigations"), icon=":material/table_view:"),
        st.Page("views/data_explorer.py", title=t("Data explorer"), icon=":material/dataset:"),
        st.Page("views/validation.py", title=t("Validation"), icon=":material/fact_check:"),
        st.Page("views/method.py", title=t("Method & sources"), icon=":material/menu_book:"),
    ],
}
nav = st.navigation(pages)

from glossary import sidebar_glossary  # noqa: E402
from pilot_ui import sidebar_pilot  # noqa: E402

sidebar_pilot()  # AI pilot on every page (ADR-058); needs the pages registered for st.switch_page
sidebar_glossary()
nav.run()
