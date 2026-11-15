"""Shared helpers for the Streamlit pages: cached loaders (data, models, generated results) and badges.
No physics or modeling here - everything comes from the fif package or generated artefacts (ADR-034).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from i18n import t as _t

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

BLUE, ORANGE, INK, MUTED = "#1D4ED8", "#EA580C", "#111827", "#6B7280"
EVIDENCE_COLORS = {
    "NASA data": "#15803D",
    "model": "#1D4ED8",
    "physics theory": "#7C3AED",
    "NASA literature": "#4B5563",
    "NASA history": "#92400E",
    "NASA spinoff": "#0F766E",
}
STATUS_COLORS = {"in range": "#15803D", "extrapolation": "#B45309", "unreliable": "#B91C1C"}
STAGE_LABEL = {"prevention": "Prevention", "detection": "Detection", "suppression": "Suppression"}
PLOT_TEMPLATE = "prometheus"  # plotly_dark on a transparent background, so charts sit on the glass cards (ADR-056)


def _register_template() -> None:
    import plotly.graph_objects as go
    import plotly.io as pio

    if PLOT_TEMPLATE in pio.templates:
        return
    tpl = go.layout.Template(pio.templates["plotly_dark"])
    tpl.layout.paper_bgcolor = "rgba(0,0,0,0)"
    tpl.layout.plot_bgcolor = "rgba(10,15,30,0.35)"
    tpl.layout.font = {"family": "Inter, sans-serif", "color": "#d8deea"}
    tpl.layout.colorway = ["#FF7A1A", "#7FA6FF", "#38E8FF", "#C9D4FF", "#FFB627", "#2FD27A", "#E86BB5"]
    tpl.layout.xaxis.gridcolor = tpl.layout.yaxis.gridcolor = "rgba(140,170,255,0.10)"
    tpl.layout.xaxis.zerolinecolor = tpl.layout.yaxis.zerolinecolor = "rgba(140,170,255,0.18)"
    pio.templates[PLOT_TEMPLATE] = tpl


_register_template()
RESULT_SCHEMA = 2  # 2: Russian fields reasons_ru / notes_ru (ADR-041)


def badge(text: str, color: str) -> str:
    return (
        f"<span style='background:{color};color:white;padding:2px 8px;border-radius:10px;"
        f"font-size:0.78rem;font-weight:600;white-space:nowrap'>{text}</span>"
    )


def evidence_badge(kind: str) -> str:
    return badge(_t(kind), EVIDENCE_COLORS.get(kind, MUTED))


def status_badge(status: str) -> str:
    return badge(_t(status), STATUS_COLORS.get(status, MUTED))


@st.cache_data(show_spinner=False)
def insights() -> dict:
    return json.loads((ROOT / "docs" / "insights.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def validation() -> dict:
    return json.loads((ROOT / "docs" / "validation_results.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def model_report() -> dict:
    return json.loads((ROOT / "docs" / "verification" / "model_report.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def flex() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "processed" / "flex.csv")


@st.cache_data(show_spinner=False)
def cfig() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "processed" / "cfig.csv")


@st.cache_data(show_spinner=False)
def investigations() -> pd.DataFrame:
    from fif.insights.investigations import ranked_investigations

    return ranked_investigations()


@st.cache_data(show_spinner="Computing the scenario...")
def scenario(fuel, p_atm, x_o2, x_co2, x_he, d0_mm, schema: int = RESULT_SCHEMA) -> dict:
    # schema: bump when the package adds result fields, so a running server never serves cached old dicts
    from fif.insights.scenario import predict

    return predict(fuel, p_atm, x_o2, x_co2, x_he, d0_mm)


@st.cache_data(show_spinner="Computing the risk map...")
def risk_grid(fuel: str, d0_mm: float) -> pd.DataFrame:
    from fif.insights.scenario import risk_grid as rg

    return rg(fuel, d0_mm=d0_mm)


def source_note(text: str) -> None:
    st.caption(_t("Source:") + " " + text)


@st.cache_data(show_spinner=False)
def flame_sim(
    fuel: str,
    p_atm: float,
    x_o2: float,
    x_co2: float,
    x_he: float,
    d0_mm: float,
    gravity: float,
    label: str,
    schema: int = RESULT_SCHEMA,
) -> dict:
    from fif.insights.flame_sim import simulate

    return simulate(fuel, p_atm, x_o2, x_co2, x_he, d0_mm, gravity, label)


@st.cache_data(show_spinner=False)
def comparison() -> tuple[pd.DataFrame, dict]:
    from fif.insights.compare import comparison_matrix, hardware_groups

    m = comparison_matrix()
    return m, hardware_groups(m)


@st.cache_data(show_spinner=False)
def moon(fuel: str, schema: int = RESULT_SCHEMA) -> dict:
    from fif.insights.moon import moon_answer

    return moon_answer(fuel)


# Guided path through the dashboard (ADR-054): question -> Moon base -> evidence. Each page ends with a link to the next.
TOUR = [
    ("views/overview.py", "Overview"),
    ("views/scenario.py", "Moon-base scenario"),
    ("views/module.py", "Module fire"),
    ("views/risk_map.py", "Risk map"),
    ("views/insights.py", "Insights"),
    ("views/investigations.py", "Investigations"),
    ("views/data_explorer.py", "Data explorer"),
    ("views/validation.py", "Validation"),
    ("views/method.py", "Method & sources"),
    ("views/assistant.py", "Ask the data"),
]


def next_step(page: str) -> None:
    """A 'Next step' link at the bottom of a page, to the next page of the tour (and back to the previous one)."""
    paths = [p for p, _ in TOUR]
    i = paths.index(page)
    st.divider()
    left, right = st.columns(2)
    if i > 0:
        p, name = TOUR[i - 1]
        left.page_link(p, label=_t("Back: {page}").format(page=_t(name)), icon=":material/arrow_back:")
    if i + 1 < len(TOUR):
        p, name = TOUR[i + 1]
        right.page_link(p, label=_t("Next step: {page}").format(page=_t(name)), icon=":material/arrow_forward:")


# Shareable settings (ADR-055): a page keeps its inputs in the address bar, so a link reopens the same scenario.
def qp_get(name: str, cast, default):
    """A setting from the page address, or the default when it is missing or unreadable."""
    v = st.query_params.get(name)
    if v is None:
        return default
    try:
        return cast(v)
    except (ValueError, TypeError):
        return default


def share_link(params: dict[str, str]) -> None:
    """Write the settings into the address bar and offer the link in a popover with a copy button."""
    from urllib.parse import urlencode

    st.query_params.update(params)
    full = {k: st.query_params[k] for k in st.query_params}
    try:
        base = str(st.context.url).split("?")[0]
    except Exception:  # no browser context (tests)
        base = ""
    with st.popover(_t("Share these settings"), icon=":material/link:"):
        st.caption(_t("This link opens the page with exactly these settings (copy button on the right):"))
        st.code(base + "?" + urlencode(full), language=None, wrap_lines=True)
