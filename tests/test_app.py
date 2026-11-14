"""Smoke test: every dashboard page runs inside the real navigation without exceptions (streamlit.testing AppTest)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app"
PAGES = ["overview", "insights", "scenario", "risk_map", "investigations", "data_explorer", "validation", "method"]
sys.path.insert(0, str(APP))


def _run(page: str) -> AppTest:
    at = AppTest.from_file(str(APP / "main.py"), default_timeout=180)
    at.run()
    if page != "overview":
        at.switch_page(f"views/{page}.py")
        at.run()
    return at


@pytest.mark.parametrize("page", PAGES)
def test_page_runs(page):
    at = _run(page)
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.title) == 1


def test_scenario_moon_preset_shows_extrapolation():
    at = _run("scenario")
    md = " ".join(m.value for m in at.markdown)
    assert "extrapolation" in md
    assert "vs ISS cabin air" in [m.label for m in at.metric]
