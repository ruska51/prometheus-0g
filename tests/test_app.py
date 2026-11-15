"""Smoke test: every dashboard page runs inside the real navigation without exceptions (streamlit.testing AppTest)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app"
PAGES = [
    "overview",
    "insights",
    "assistant",
    "scenario",
    "module",
    "base",
    "risk_map",
    "investigations",
    "data_explorer",
    "validation",
    "method",
]
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


def test_assistant_without_key_answers_from_the_data(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    at = _run("assistant")
    chat = next(c for c in at.chat_input if c.key != "pilot_cmd")  # the sidebar also holds the AI pilot box
    chat.set_value("How much faster does a droplet burn on a Moon base?").run()
    assert not at.exception, [e.value for e in at.exception]
    md = " ".join(m.value for m in at.markdown)
    assert "+32 %" in md
    assert any("without AI" in c.value for c in at.caption)


def _run_with(page: str, params: dict[str, str]) -> AppTest:
    at = AppTest.from_file(str(APP / "main.py"), default_timeout=180)
    at.run()
    at.switch_page(f"views/{page}.py")
    for k, v in params.items():
        at.query_params[k] = v
    at.run()
    return at


def test_scenario_link_restores_the_settings():
    """A shared link (ADR-055) reopens the scenario with the same inputs; bad values fall back to the defaults."""
    at = _run_with("scenario", {"preset": "Custom", "fuel": "Heptane", "o2": "0.40", "psi": "8.0", "d0": "2.0"})
    assert not at.exception, [e.value for e in at.exception]
    assert at.selectbox(key="sc_preset").value == "Custom"
    assert at.radio(key="sc_fuel").value == "Heptane"
    assert at.slider(key="sc_o2").value == 0.40 and at.slider(key="sc_psi").value == 8.0
    assert at.slider(key="sc_d0").value == 2.0
    bad = _run_with("scenario", {"preset": "Mars", "o2": "lots", "d0": "99"})
    assert not bad.exception
    assert bad.selectbox(key="sc_preset").value == "Moon base / rover (planned)"
    assert bad.slider(key="sc_d0").value == 5.0  # clipped to the slider range


def test_module_link_restores_wall_and_ignition():
    at = _run_with("module", {"wall": "lab", "atm": "custom", "o2": "35", "psi": "9.0", "ign": "16-14", "L": "F800"})
    assert not at.exception, [e.value for e in at.exception]
    assert at.selectbox(key="mod_wall").value == "lab"
    assert at.selectbox(key="mod_atm").value == "custom" and at.slider(key="mod_o2").value == 35
    assert at.session_state["module"]["layout"] == [["F"] * 40] * 20
    assert tuple(at.session_state["module"]["ignition"]) == (16, 14)
    broken = _run_with("module", {"wall": "crew", "L": "F3X9", "ign": "99-99"})
    assert not broken.exception, [e.value for e in broken.exception]


def test_glossary_has_both_languages():
    from glossary import TERMS

    assert len(TERMS) >= 15
    assert all(all(x.strip() for x in row) for row in TERMS)
    assert len({row[0] for row in TERMS}) == len(TERMS)


def test_module_custom_atmosphere_starts_at_moon_base_values():
    at = _run("module")
    at.selectbox(key="mod_atm").set_value("custom").run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.slider(key="mod_o2").value == 30 and at.slider(key="mod_psi").value == 10.2


def test_pilot_opens_the_module_with_settings(monkeypatch):
    """ADR-058: without a key the rule parser decides; the pilot switches page and the page reads the settings."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    at = _run("overview")
    at.chat_input(key="pilot_cmd").set_value("detectors in the lab module at 34 % oxygen").run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.selectbox(key="mod_wall").value == "lab"
    assert at.selectbox(key="mod_atm").value == "custom" and at.slider(key="mod_o2").value == 34
    assert "Module fire" in at.session_state["pilot_say"]


def test_pilot_rejects_values_outside_the_app():
    from fif.assistant.pilot import validate

    out = validate({"page": "mars", "module": {"wall": "reactor"}})
    assert out["page"] is None and out["params"] == {}
    out = validate({"page": "module", "module": {"wall": "lab", "o2": 95, "tab": "detect"}})
    assert out["params"] == {"wall": "lab", "o2": "40", "atm": "custom", "tab": "detect"}
    out = validate({"page": "scenario", "scenario": {"fuel": "Kerosene", "o2": 0.3}})
    assert out["params"] == {"o2": "0.30", "preset": "Custom"}
    q = validate({"page": "overview", "question": "Does helium slow burning?"})
    assert q["page"] == "assistant" and q["params"] == {"q": "Does helium slow burning?"}


def test_stray_translated_label_in_a_choice_does_not_break_the_module():
    """Seen live: after a language switch the browser sent the label "blows towards the hatch" as the ventilation value."""
    at = _run("module")
    at.session_state["mod_vent"] = "blows towards the hatch"
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["mod_vent"] in (1, -1)  # a valid option again (the test harness maps the label itself)


def test_choice_resets_values_outside_the_options(monkeypatch):
    import common

    calls = {}

    def fake_widget(label, options, key, **kw):
        calls["state"] = common.st.session_state[key]
        return "blows towards the hatch"  # what the browser sent live

    monkeypatch.setattr(common.st, "session_state", {"v": "blows towards the hatch"})
    assert common.choice(fake_widget, "Ventilation", [1, -1], "v") == 1
    assert calls["state"] == 1
