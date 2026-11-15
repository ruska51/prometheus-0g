"""Ask the data: assistant that answers only from our verified results and NASA NTRS reports, with citations
(stage 9, ADR-042). Without a Gemini API key the page explains how to enable it; the rest of the app is unaffected."""

import os

import streamlit as st
from common import next_step, source_note
from i18n import t

from fif.assistant.knowledge import search
from fif.assistant.llm import (
    DEFAULT_MODEL,
    MAX_QUESTION_CHARS,
    SUP,
    _reason,
    api_key,
    ask,
    friendly_error,
    gemini_generate,
    offline_answer,
)

LIMIT = 10  # questions per browser session (protects the shared free-tier quota)

st.title(t("Ask the data"))
st.markdown(
    t(
        "Ask a question about NASA microgravity fire experiments. The assistant answers only from this dashboard's verified "
        "results and from public NASA technical reports (NTRS), cites a source after every statement, and says so when "
        "the data do not cover the question."
    )
)
st.caption(
    t(
        "Examples: Does helium dilution slow burning? / How much faster would a droplet burn in a Moon-base atmosphere? / "
        "What do NASA reports say about flammability at lunar gravity?"
    )
)


def _secrets() -> dict:
    try:
        return dict(st.secrets)
    except Exception:  # no secrets file locally
        return {}


sec = _secrets()
key = api_key(sec)
model = str(sec.get("GEMINI_MODEL") or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL)
if not key:
    st.info(
        t(
            "No AI model is configured on this server, so answers are quoted directly from our verified results and "
            "NASA reports, without AI."
        )
    )


@st.cache_resource(show_spinner=False)
def _generator(k: str, m: str):
    return gemini_generate(k, m)


@st.cache_resource(show_spinner=False)
def _warm_index() -> bool:
    search("moon", k=1)  # builds the data and report blocks once per server process
    return True


chat = st.session_state.setdefault("chat", [])
for turn in chat:
    with st.chat_message("user"):
        st.write(turn["q"])
    with st.chat_message("assistant"):
        if turn.get("offline_note"):
            st.caption(turn["offline_note"])
        st.markdown(turn.get("display") or turn["text"])
        if turn.get("uncited"):
            st.warning(t("This answer has no source citations - treat it with caution."))
        if turn.get("unsupported"):
            st.warning(
                t(
                    "Numbers not found in the cited sources: {nums} - check them against the sources below.",
                    nums=", ".join(turn["unsupported"]),
                )
            )
        if turn.get("sources"):
            lines = []
            for n, s in enumerate(turn["sources"], 1):
                link = f" - [{t('open report')}]({s['url']})" if s["url"] else ""
                lines.append(f"{str(n).translate(SUP)} {s['title']}{link}")
            st.caption("  \n".join(lines))
            with st.expander(t("Source excerpts ({n})", n=len(turn["sources"]))):
                for n, s in enumerate(turn["sources"], 1):
                    st.markdown(f"**{n}.** {s['title']} `{s['id']}`")
                    st.caption(s["text"][:700] + ("..." if len(s["text"]) > 700 else ""))

left = LIMIT - len(chat)
q = st.chat_input(
    t("Ask about NASA fire data...") if left > 0 else t("Question limit for this session reached"),
    max_chars=MAX_QUESTION_CHARS,
    disabled=left <= 0,
)
st.caption(
    t(
        "Questions left in this session: {n} of {total}. Model: {m} (Google Gemini).",
        n=left,
        total=LIMIT,
        m=st.session_state.get("model_used", model),
    )
    if key
    else t("Questions left in this session: {n} of {total}. Answers without AI, quoted from the data.", n=left, total=LIMIT)
)
SUGGESTIONS = [
    "How much faster would a droplet burn on a Moon base?",
    "Does helium dilution slow burning?",
    "Why may lunar gravity be dangerous for solid materials?",
    "How much CO do burning solids release?",
    "What did the fire on Mir teach us?",
]
if left > 0:
    st.caption(t("Or tap a question:"))
    picked = st.pills(" ", [t(x) for x in SUGGESTIONS], key=f"suggest-{len(chat)}", label_visibility="collapsed")
    if picked and not q:
        q = picked
_pq = st.query_params.get("q")  # a question handed over by the AI pilot (ADR-058), asked once
if _pq and not q and left > 0 and st.session_state.get("_pilot_q") != _pq:
    st.session_state["_pilot_q"] = _pq
    q = _pq
if st.query_params.get("debug") == "1" and "gen_failed" in st.session_state:  # diagnosis of model fall-through
    st.caption("debug: " + ("; ".join(f"{m}: {r}" for m, r in st.session_state["gen_failed"]) or "no failures"))
if q:
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        live = st.empty()
        live.caption(t("Searching the data and NASA reports..."))
        note = ""
        try:
            if not key:
                raise LookupError("no key")
            gen = _generator(key, model)
            r = ask(q, gen, on_text=live.markdown)
            st.session_state["model_used"] = getattr(gen, "model", model)
            st.session_state["gen_failed"] = list(getattr(gen, "failed", []))
        except Exception as e:  # quota, key, model, network, no key: answer from the data without AI (ADR-049)
            if key:
                why = {
                    "quota": t("the free Gemini quota is used up for now"),
                    "key": t("the Gemini API key was rejected"),
                    "model": t("the Gemini model is not available"),
                }.get(friendly_error(e), t("the Gemini service did not respond"))
                note = t(
                    "The AI model is not available right now ({why}). These are the most relevant verified facts, "
                    "quoted directly from our results and NASA reports without AI.",
                    why=why,
                )
                st.session_state["gen_failed"] = [("all", _reason(e))]
            r = offline_answer(q)
            if not r["covered"]:
                note = (note + " " if note else "") + t(
                    "The NASA data and reports in this tool do not cover this question. What the tool covers:"
                )
        chat.append(
            {
                "q": q,
                "text": r["answer"] or t("No answer was returned."),
                "display": r["display"],
                "uncited": r["uncited"],
                "unsupported": r.get("unsupported_numbers", []),
                "offline_note": note,
                "sources": [{"id": s.id, "title": s.title, "text": s.text, "url": s.url} for s in r["sources"]],
            }
        )
    st.rerun()
elif key and left > 0 and not chat:
    # warm-up while the visitor reads the page: model list and retrieval index, so the first answer starts at once
    try:
        _generator(key, model)
        _warm_index()
    except Exception:  # an API problem is reported when a question is asked
        pass
source_note(
    t(
        "dashboard results (docs/insights.json, docs/validation_results.json, scenario model, PSI catalog) and public-use "
        "NASA NTRS reports (data/raw/ntrs_text/MANIFEST.tsv); retrieval and rules: src/fif/assistant (ADR-042). "
        "Answers are generated by an AI model and can contain errors."
    )
)

next_step("views/assistant.py")
