"""AI pilot box in the sidebar of every page (ADR-058): a request in plain words opens the right page with its inputs set.
The decision logic and its guards are in fif.assistant.pilot; this file only shows the box and switches pages."""

from __future__ import annotations

import os

import streamlit as st
from i18n import t

from fif.assistant import pilot
from fif.assistant.llm import DEFAULT_MODEL, api_key, gemini_generate

PAGE_NAME = {
    "overview": "Overview",
    "assistant": "Ask the data",
    "scenario": "Moon-base scenario",
    "module": "Module fire",
    "base": "Base planner",
    "risk_map": "Risk map",
    "insights": "Insights",
    "investigations": "Investigations",
    "data_explorer": "Data explorer",
    "validation": "Validation",
    "method": "Method & sources",
}
LIMIT = 20  # pilot requests per visitor session (shares the free AI quota fairly)


@st.cache_resource(show_spinner=False)
def _gen(key: str, model: str):
    return gemini_generate(key, model)


def _generator():
    try:
        sec = dict(st.secrets)
    except Exception:
        sec = {}
    key = api_key(sec)
    if not key:
        return None
    try:
        return _gen(key, str(sec.get("GEMINI_MODEL") or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL))
    except Exception:
        return None


def _describe(action: dict) -> str:
    """A reply built from the validated action (used when the rules decided, or the model said nothing)."""
    if action["question"]:
        return t("Opening the data assistant with your question.")
    if not action["page"]:
        return t(
            "I could not match that to a page. Try: 'heptane on the Moon base', 'detectors in the lab module', 'open the base planner'."
        )
    sets = ", ".join(f"{k} = {v}" for k, v in action["params"].items() if k != "tab")
    page = t(PAGE_NAME[action["page"]])
    return t("Opening {page}", page=page) + (f" - {sets}." if sets else ".")


def sidebar_pilot() -> None:
    used = st.session_state.setdefault("pilot_used", 0)
    with st.sidebar:
        st.markdown(
            "<div style='font:600 .72rem Space Grotesk,sans-serif;letter-spacing:.16em;color:#38e8ff;"
            "text-transform:uppercase;margin:6px 0 2px'>🛰️ " + t("AI pilot") + "</div>",
            unsafe_allow_html=True,
        )
        last = st.session_state.get("pilot_say")
        if last:
            st.markdown(
                f"<div style='font-size:.85rem;background:rgba(56,232,255,.07);border:1px solid rgba(56,232,255,.3);"
                f"border-radius:12px;padding:8px 10px;margin-bottom:6px'>{last}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption(t("Tell me what to show: 'heptane on the Moon base', 'detectors in the lab at 34 % O2', 'plan a base'."))
        cmd = st.chat_input(
            t("Ask the pilot...") if used < LIMIT else t("Pilot limit for this session reached"),
            key="pilot_cmd",
            max_chars=300,
            disabled=used >= LIMIT,
        )
    if not cmd:
        return
    st.session_state["pilot_used"] = used + 1
    with st.sidebar, st.spinner(t("Pilot is setting things up...")):
        action = pilot.plan(cmd, _generator())
    say = action["say"] if action.get("used_ai") and action["say"] else _describe(action)
    st.session_state["pilot_say"] = ("✨ " if action.get("used_ai") else "⚙️ ") + say
    if action["page"]:
        params = dict(action["params"])
        if st.session_state.get("lang") == "ru":
            params["lang"] = "ru"
        st.switch_page(pilot.PAGES[action["page"]], query_params=params)
    st.rerun()
