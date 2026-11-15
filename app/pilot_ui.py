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


EXAMPLES = [
    "Detectors in the lab module in Moon-base air",
    "Heptane droplet on the Moon, 2 mm",
    "Does helium slow burning?",
]


def _run(cmd: str) -> None:
    st.session_state["pilot_used"] = st.session_state.get("pilot_used", 0) + 1
    with st.spinner(t("Pilot is setting things up...")):
        action = pilot.plan(cmd, _generator())
    say = action["say"] if action.get("used_ai") and action["say"] else _describe(action)
    st.session_state["pilot_say"] = ("✨ " if action.get("used_ai") else "⚙️ ") + say
    if action["page"]:
        params = dict(action["params"])
        if st.session_state.get("lang") == "ru":
            params["lang"] = "ru"
        st.switch_page(pilot.PAGES[action["page"]], query_params=params)
    st.rerun()


def floating_pilot() -> None:
    """The AI pilot as a glowing button in the bottom-right corner of every page (ADR-058, Ruslan: 'visible at once')."""
    used = st.session_state.setdefault("pilot_used", 0)
    with st.container(key="pilot_fab"):
        with st.popover("🛰️ " + t("AI pilot"), use_container_width=False):
            st.markdown("**" + t("AI pilot") + "** · " + t("I open the right page and set it up for you."))
            last = st.session_state.get("pilot_say")
            if last:
                st.info(last)
            with st.form("pilot_form", clear_on_submit=True, border=False):
                cmd = st.text_input(
                    t("What should I show?"),
                    placeholder=t("e.g. detectors in the lab module in Moon-base air"),
                    max_chars=300,
                    disabled=used >= LIMIT,
                    key="pilot_cmd",
                )
                go_ = st.form_submit_button(t("Go") + " →", type="primary", disabled=used >= LIMIT)
            st.caption(t("Or try:"))
            for i, ex in enumerate(EXAMPLES):
                if st.button(t(ex), key=f"pilot_ex_{i}", use_container_width=True, disabled=used >= LIMIT):
                    _run(t(ex))
            st.caption(t("Requests left in this session: {n} of {total}.", n=max(LIMIT - used, 0), total=LIMIT))
    if go_ and cmd and cmd.strip():
        _run(cmd.strip())
