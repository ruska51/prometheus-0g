"""Shared helpers for the Streamlit pages: cached loaders (data, models, generated results) and badges.
No physics or modeling here - everything comes from the fif package or generated artefacts (ADR-034).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

BLUE, ORANGE, INK, MUTED = "#1D4ED8", "#EA580C", "#111827", "#6B7280"
EVIDENCE_COLORS = {"NASA data": "#15803D", "model": "#1D4ED8", "physics theory": "#7C3AED", "NASA literature": "#4B5563",
                   "NASA history": "#92400E", "NASA spinoff": "#0F766E"}
STATUS_COLORS = {"in range": "#15803D", "extrapolation": "#B45309", "unreliable": "#B91C1C"}
STAGE_LABEL = {"prevention": "Prevention", "detection": "Detection", "suppression": "Suppression"}
PLOT_TEMPLATE = "plotly_white"


def badge(text: str, color: str) -> str:
    return (f"<span style='background:{color};color:white;padding:2px 8px;border-radius:10px;"
            f"font-size:0.78rem;font-weight:600;white-space:nowrap'>{text}</span>")


def evidence_badge(t: str) -> str:
    return badge(t, EVIDENCE_COLORS.get(t, MUTED))


def status_badge(s: str) -> str:
    return badge(s, STATUS_COLORS.get(s, MUTED))


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
def scenario(fuel, p_atm, x_o2, x_co2, x_he, d0_mm) -> dict:
    from fif.insights.scenario import predict
    return predict(fuel, p_atm, x_o2, x_co2, x_he, d0_mm)


@st.cache_data(show_spinner="Computing the risk map...")
def risk_grid(fuel: str, d0_mm: float) -> pd.DataFrame:
    from fif.insights.scenario import risk_grid as rg
    return rg(fuel, d0_mm=d0_mm)


def source_note(text: str) -> None:
    st.caption(f"Source: {text}")


@st.cache_data(show_spinner=False)
def flame_sim(fuel: str, p_atm: float, x_o2: float, x_co2: float, x_he: float, d0_mm: float, gravity: float, label: str) -> dict:
    from fif.insights.flame_sim import simulate
    return simulate(fuel, p_atm, x_o2, x_co2, x_he, d0_mm, gravity, label)
