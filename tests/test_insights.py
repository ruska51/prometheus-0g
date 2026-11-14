"""Insight tests: every insight computes; its numbers equal a direct, independent calculation from the data."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from fif.data.catalog import REPO_ROOT
from fif.insights import catalog as cat
from fif.insights.base import EVIDENCE_WEIGHTS, rank, score_evidence_log_n


@pytest.fixture(scope="module")
def insights():
    return {i.id: i for i in cat.all_insights()}


def _flex():
    f = pd.read_csv(REPO_ROOT / "data" / "processed" / "flex.csv")
    return f[f["use_in_model"]]


def test_all_insights_complete(insights):
    assert len([i for i in insights.values() if i.stage in ("prevention", "detection", "suppression")]) == 14
    for i in insights.values():
        assert i.evidence_type in EVIDENCE_WEIGHTS
        assert i.title and i.finding and i.action and i.sources
        assert i.confidence in ("high", "medium", "low")
        if i.evidence_type in ("NASA history", "NASA spinoff"):
            assert i.n_tests == 0


def test_p1_matches_direct_regression(insights):
    f = _flex()
    f = f[(f["flex_identifier"] != "C13H201")].dropna(subset=["K_m2_s", "d0_m"])
    X = np.column_stack(
        [np.ones(len(f)), f["fuel_methanol"], f["x_o2"], np.log(f["p_atm"]), f["x_co2"], f["x_he"], np.log(f["d0_m"] * 1e3)]
    )
    b = np.linalg.lstsq(X, np.log(f["K_m2_s"]), rcond=None)[0]
    assert insights["P1"].effect["value"] == pytest.approx(math.exp(b[2] * 0.09))
    assert insights["S1"].effect["value"] == pytest.approx(math.exp(b[4] * 0.30))
    assert insights["S2"].effect["value"] == pytest.approx(math.exp(b[5] * 0.30))
    assert insights["P1"].n_tests == len(f)
    assert f"{(math.exp(b[2] * 0.09) - 1) * 100:+.0f} %" in insights["P1"].finding


def test_physical_signs(insights):
    assert insights["P1"].effect["value"] > 1  # more O2, faster burning
    assert insights["S1"].effect["value"] < 1  # CO2 slows burning
    assert insights["S3"].effect["value"] > 1  # less O2, extinction at larger relative size


def test_d1_matches_direct_bass_ii(insights):
    b = pd.read_csv(REPO_ROOT / "data" / "raw" / "psi_tables" / "PSI-25_Experimental table_BASS-II.csv", encoding="cp1252")
    b.columns = [str(x).strip().lstrip("﻿").lstrip("ï»¿") for x in b.columns]

    def n(c):
        return pd.to_numeric(b[c], errors="coerce")

    ok = (
        n("Initial CO (ppm)").notna()
        & n("Final CO (ppm)").notna()
        & n("Calibrated  initial O2 % by vol").notna()
        & n("Calibrated final O2 % by vol").notna()
        & (n("Calibrated final O2 % by vol") <= n("Calibrated  initial O2 % by vol") + 0.5)
    )
    d = (n("Final CO (ppm)") - n("Initial CO (ppm)"))[ok]
    assert insights["D1"].n_tests == int(ok.sum())
    assert insights["D1"].effect["value"] == pytest.approx(d.median())


def test_s4_matches_direct_shares(insights):
    f = _flex()
    lab = f[f["extinct_finite_d"].notna() & (f["diluent"] == "N2")]
    hi, lo = lab[lab["x_o2"] >= 0.30], lab[lab["x_o2"] <= 0.21]
    assert insights["S4"].n_tests == len(hi) + len(lo)
    assert f"{(1 - hi['extinct_finite_d'].mean()) * 100:.0f} % of {len(hi)} tests" in insights["S4"].finding


def test_p4_matches_direct_cfig(insights):
    c = pd.read_csv(REPO_ROOT / "data" / "processed" / "cfig.csv")
    inv = c[(c["table"] == "inverse") & c["ignited"].notna()]
    hi = inv[inv["x_o2_oxidizer"] >= 0.5]
    assert f"{hi['ignited'].mean() * 100:.0f} % of {len(hi)} attempts" in insights["P4"].finding


def test_ranking_formula_a(insights):
    i = insights["P1"]
    e = min(abs(i.effect["log_effect"]) / 0.5, 1)
    assert score_evidence_log_n(i) == pytest.approx(1.0 * math.log1p(i.n_tests) * (0.3 + 0.7 * e))
    ranked = rank(list(insights.values()))
    assert ranked[0].score >= ranked[-1].score


def test_cabin_atmosphere_labels():
    t = cat.cabin_atmospheres()
    st = dict(zip(t["atmosphere"] + "|" + t["fuel"], t["status"]))
    assert st["ISS cabin air|Methanol"] == "in range"
    assert st["Moon base / pressurized rover (planned)|Heptane"] == "extrapolation"
    assert st["Spacesuit|Methanol"] == "unreliable"
    assert t.loc[t["atmosphere"] == "Spacesuit", "K_hybrid_mm2_s"].isna().all()  # no model number when unreliable


def test_lunar_bound_between_microgravity_and_earth(insights):
    from fif.physics.droplet import G_MOON_RATIO, buoyancy_factor

    p5 = insights["P5"]
    assert p5.effect["value"] > 1.0 and p5.extrapolation
    for gr in (0.1, 1.0, 10.0, 100.0):  # property: 1 < moon factor < earth factor for any Gr
        assert 1.0 < float(buoyancy_factor(gr, G_MOON_RATIO)) < float(buoyancy_factor(gr, 1.0))
    assert insights["P6"].evidence_type == "NASA literature" and insights["P6"].n_tests == 0


def test_moon_answer_matches_model_and_insights(insights):
    from fif.insights.moon import moon_answer
    from fif.insights.scenario import PRESETS, predict

    for fuel in ("Methanol", "Heptane"):
        a = moon_answer(fuel)
        iss, moon = PRESETS["ISS cabin air"], PRESETS["Moon base / rover (planned)"]
        ratio = (
            predict(fuel, moon["p_atm"], moon["x_o2"])["K_hybrid_mm2_s"]
            / predict(fuel, iss["p_atm"], iss["x_o2"])["K_hybrid_mm2_s"]
        )
        assert a["k_ratio"] == pytest.approx(ratio)
        assert a["k_ratio_band"][0] < a["k_ratio"] < a["k_ratio_band"][1]
        assert a["burn_time_lunar_surface_s"] < a["burn_time_moon_s"] < a["burn_time_iss_s"]  # faster burning -> shorter
        assert a["burn_time_iss_s"] / a["burn_time_moon_s"] == pytest.approx(a["k_ratio"], rel=1e-6)  # d2-law: t = d0^2 / K
    a = moon_answer("Methanol")
    s4 = insights["S4"].effect["value"]  # share without extinction, high O2 / low O2
    assert (1 - a["self_ext_high_o2"]) / (1 - a["self_ext_low_o2"]) == pytest.approx(s4)
    p2 = insights["P2"].effect["value"]  # worst-fuel ratio
    assert max(moon_answer(f)["k_ratio"] for f in ("Methanol", "Heptane")) == pytest.approx(p2, rel=1e-6)
