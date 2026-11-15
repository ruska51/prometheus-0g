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
    for key, rows in ((k, v) for k, v in mf.PRESETS.items() if k != "blank"):
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


@pytest.mark.parametrize("key", ["crew", "lab"])
def test_time_to_hatch_backwards_equals_forward_from_every_start(key):
    g = mf.grid(mf.PRESETS[key])
    for e in mf.ENVIRONMENTS.values():
        back = mf.time_to_hatch(g, e)
        for r, c in list(zip(*np.where(np.isin(g, mf.FLAMMABLE)), strict=True))[::7]:
            fwd = mf.hatch_time(g, mf.arrival_times(g, (r, c), e))
            assert (math.isinf(fwd) and math.isinf(back[r, c])) or fwd == pytest.approx(back[r, c]), (e.key, r, c)


def test_firebreaks_are_metal_strips_that_help():
    e = mf.ENVIRONMENTS["moon"]
    for key in ["crew", "lab", "stowage"]:
        g, ign = mf.grid(mf.PRESETS[key]), mf.IGNITION[key]
        base = mf.hatch_time(g, mf.arrival_times(g, ign, e))
        fb = mf.best_firebreak(g, ign, e)
        assert fb is not None and fb.hatch_s > base and ign not in fb.cells
        assert 1 <= len(fb.cells) <= 5 and all(g[x] in mf.FLAMMABLE for x in fb.cells)
        rows, cols = zip(*fb.cells, strict=True)
        assert len(set(rows)) == 1 or len(set(cols)) == 1  # a straight strip
        lay = mf.with_metal(g, fb.cells)
        assert mf.hatch_time(lay, mf.arrival_times(lay, ign, e)) == fb.hatch_s
        anywhere = mf.best_firebreak_anywhere(g, e)
        before = mf.hatch_catchment_m2(mf.time_to_hatch(g, e))
        assert anywhere is not None and anywhere.reached_m2 < before
        assert mf.hatch_catchment_m2(mf.time_to_hatch(mf.with_metal(g, anywhere.cells), e)) == pytest.approx(anywhere.reached_m2)


def test_blank_wall_has_nothing_to_burn():
    g = mf.grid(mf.PRESETS["blank"])
    t = mf.arrival_times(g, mf.IGNITION["blank"], mf.ENVIRONMENTS["moon"])
    s = mf.summary(g, t)
    assert s["flammable_m2"] == 0 and s["reached_m2"] == 0 and math.isinf(s["hatch_s"])
    assert mf.best_firebreak(g, mf.IGNITION["blank"], mf.ENVIRONMENTS["moon"]) is None


def test_ventilation_direction_swaps_the_measured_concurrent_and_opposed_rates():
    g = strip(11)
    to_right = mf.arrival_times(g, (0, 0), mf.iss_with_flow(1))[0, -1]
    against = mf.arrival_times(g, (0, 0), mf.iss_with_flow(-1))[0, -1]
    assert to_right == pytest.approx(10 * mf.CELL_MM / 1.8) and against == pytest.approx(10 * mf.CELL_MM / 1.3)
    crew = mf.grid(mf.PRESETS["crew"])
    towards = mf.hatch_time(crew, mf.arrival_times(crew, mf.IGNITION["crew"], mf.iss_with_flow(1)))
    away = mf.hatch_time(crew, mf.arrival_times(crew, mf.IGNITION["crew"], mf.iss_with_flow(-1)))
    assert towards < away  # air blowing towards the hatch brings the fire there sooner


def test_atmosphere_scaling_follows_the_nasa_formula_and_its_constants():
    bass = _text("20210011385")
    assert "a vaporization temperature of 673 K" in bass and mf.T_V_K == 673.0
    assert mf.atmosphere_factor(*mf.AIR) == pytest.approx(1.0)
    fs = [mf.atmosphere_factor(x, 1.0) for x in (0.17, 0.21, 0.25, 0.30, 0.35)]
    assert all(a < b for a, b in zip(fs, fs[1:], strict=False))  # more oxygen, hotter flame, faster spread
    moon = mf.atmosphere_factor(0.30, 10.2 / 14.696)
    tf, ta = mf.flame_temperature_K(0.30, round(10.2 / 14.696, 4)), mf.flame_temperature_K(*mf.AIR)
    assert moon == pytest.approx((tf - 673.0) / (ta - 673.0), rel=1e-3) and moon > 1
    e = mf.scaled(mf.ENVIRONMENTS["moon"], 2.0)
    assert e.rates["F"] == (2.2, 1.8)
    g, ign = strip(11), (0, 0)
    t1 = mf.arrival_times(g, ign, mf.iss_with_flow(1))[0, -1]
    t2 = mf.arrival_times(g, ign, mf.scaled(mf.iss_with_flow(1), moon))[0, -1]
    assert t2 == pytest.approx(t1 / moon)


def test_zone_model_constants_are_quoted_and_balances_hold():
    assert "0.24 g cellulose (about 18 cm2 SIBAL fabric)" in _text("20210020516")
    assert "the amount of oxygen consumed by burning" in _text("20210020516") and "0.28 g" in _text("20210020516")
    assert "the constant 13.1 kJ of heat released per gram of O2 consumed" in _text("20210011385")
    saffire = _text("20170008805")
    assert "Saffire 1: 1200 +/- 300 W" in saffire and "Total burn time is 420 s" in saffire and "(40.6 cm x 94 cm)" in saffire
    assert mf.O2_G_PER_M2_FABRIC * 1e-4 * 18 == pytest.approx(0.28)
    g = mf.grid(mf.PRESETS["crew"])
    tt = mf.arrival_times(g, mf.IGNITION["crew"], mf.ENVIRONMENTS["moon"])
    tg = np.linspace(0, 3000, 61)
    z = mf.zone_history(g, tt, tg, volume_m3=20.0, x_o2=0.30, p_atm=0.694)
    assert np.all(np.diff(z["x_o2"]) <= 0) and np.all(np.diff(z["x_co2"]) >= 0)
    assert z["x_o2"][0] == pytest.approx(0.30, abs=1e-3) and z["x_o2"][-1] + z["x_co2"][-1] == pytest.approx(0.30)  # 1 CO2 per O2
    assert z["heat_MJ"][-1] == pytest.approx(z["area_m2"][-1] * 0.28 / 18e-4 * 13.1 / 1000)
    big = mf.zone_history(g, tt, tg, volume_m3=40.0, x_o2=0.30, p_atm=0.694)
    assert big["dT_K"][-1] == pytest.approx(z["dT_K"][-1] / 2, rel=1e-6)  # twice the air, half the warming


def test_fire_power_is_the_one_minute_average_of_the_heat_release():
    g = mf.grid(mf.PRESETS["crew"])
    tt = mf.arrival_times(g, mf.IGNITION["crew"], mf.ENVIRONMENTS["iss"])
    tg = np.linspace(0, 1200, 241)
    z = mf.zone_history(g, tt, tg, 30.0, 0.21, 1.0)
    i = 120  # t = 600 s
    assert z["hrr_kW"][i] == pytest.approx((z["heat_MJ"][i] - np.interp(540, tg, z["heat_MJ"])) * 1e3 / 60)
    assert z["hrr_kW"].min() >= 0
