"""Module fire sketch (ADR-049 step 2): spread geometry, blocking, and that every rate is quoted from the NASA report."""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pytest

from fif.physics import module_fire as mf

NTRS = Path(__file__).resolve().parents[1] / "data" / "raw" / "ntrs_text"


def _text(ntrs_id: str) -> str:
    raw = (NTRS / f"{ntrs_id}.txt").read_text(encoding="utf-8")
    return " ".join(re.sub(r"<[^>]*>", " ", raw).split())


def test_rates_are_quoted_in_the_reports():
    saffire = _text("20170008805")
    assert "average concurrent-flow flame spread rate is 1.8 mm/s" in saffire
    assert "opposed-flow flame average spread rate 1.3 mm/s" in saffire
    assert "flames remain anchored at the base" in saffire
    luci = _text("20250010653")
    assert "Partial- G (mm/s) 1-G (mm/s) Ratio Flame Base .9 1.5 .6 Flame Tip 1.1 2.8 .39" in luci
    assert "Partial-G (cm/s) 1-G (cm/s) Ratio .15 .40 .38" in luci  # PMMA flame tip
    assert "increases linearly from 0 to ~.6 mm/s" in luci
    assert "Flame base location is ~constant" in luci
    e = mf.ENVIRONMENTS
    assert e["iss"].rates["F"] == (1.8, 1.3) and e["iss"].rates["A"] == (0.0, 0.0)
    assert e["moon"].rates["F"] == (1.1, 0.9) and e["moon"].rates["A"] == (1.5, 0.6)
    assert e["earth"].rates["F"] == (2.8, 1.5) and e["earth"].rates["A"] == (4.0, 0.0)


def strip(n: int, vertical: bool = False) -> np.ndarray:
    return mf.grid(["F"] * n) if vertical else mf.grid(["F" * n])


@pytest.mark.parametrize("env,fast,slow", [("iss", 1.8, 1.3), ("moon", 1.1, 0.9), ("earth", 2.8, 1.5)])
def test_times_follow_the_measured_rates_and_the_flow_direction(env, fast, slow):
    e = mf.ENVIRONMENTS[env]
    n = 11
    if e.fast_axis == (1, 0):  # ventilation: left -> right is downstream
        down = mf.arrival_times(strip(n), (0, 0), e)[0, -1]
        up = mf.arrival_times(strip(n), (0, n - 1), e)[0, 0]
    else:  # gravity: row 0 is the top, so burning from the bottom row goes upward
        down = mf.arrival_times(strip(n, True), (n - 1, 0), e)[0, 0]
        up = mf.arrival_times(strip(n, True), (0, 0), e)[-1, 0]
    assert down == pytest.approx((n - 1) * mf.CELL_MM / fast)  # with the flow
    assert up == pytest.approx((n - 1) * mf.CELL_MM / slow)  # against it
    assert down < up


def test_metal_and_gaps_stop_the_flame_and_acrylic_does_not_spread_in_microgravity():
    g = mf.grid(["FFMFF", "FFMFF", "FFMFF"])
    t = mf.arrival_times(g, (1, 0), mf.ENVIRONMENTS["earth"])
    assert np.isfinite(t[:, :2]).all() and np.isinf(t[:, 2:]).all()
    a = mf.grid(["AAAA"])
    assert np.isfinite(mf.arrival_times(a, (0, 0), mf.ENVIRONMENTS["iss"])).sum() == 1
    assert np.isinf(mf.arrival_times(g, (0, 2), mf.ENVIRONMENTS["earth"])).all()  # ignition on metal: nothing burns


def test_presets_reach_the_hatch_and_summary_is_consistent():
    for key, rows in mf.PRESETS.items():
        g = mf.grid(rows)
        assert g.shape == (20, 40) and (g == "H").any()
        assert g[mf.IGNITION[key]] in mf.FLAMMABLE
        for e in mf.ENVIRONMENTS.values():
            t = mf.arrival_times(g, mf.IGNITION[key], e)
            s = mf.summary(g, t)
            assert 0 < s["reached_m2"] <= s["flammable_m2"]
            assert math.isfinite(s["hatch_s"]) and s["hatch_s"] <= s["time_all_s"]
            curve = mf.burned_area_curve(t, np.array([0.0, s["time_all_s"]]))
            assert curve[0] == pytest.approx(0.01) and curve[-1] == pytest.approx(s["reached_m2"])


def test_module_page_quotes_are_verbatim_in_the_reports():
    page = (Path(__file__).resolve().parents[1] / "app" / "views" / "module.py").read_text(encoding="utf-8")
    quotes = re.findall(r'\(\s*"(\d{11})",\s*t\([^)]*\),\s*"(.*?)",\s*\)', page, re.S)
    assert len(quotes) == 5
    for ntrs_id, quote in quotes:
        assert quote in _text(ntrs_id), (ntrs_id, quote[:60])
