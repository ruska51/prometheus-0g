"""Burning-droplet animation inputs (ADR-035): properties of the computed series, not fixed numbers."""
import numpy as np
import pytest

from fif.insights.flame_sim import ATMOSPHERES, blackbody_srgb, simulate
from fif.insights.scenario import PRESETS, predict


@pytest.mark.parametrize("fuel", ["Methanol", "Heptane"])
@pytest.mark.parametrize("name", list(ATMOSPHERES))
def test_series_follows_d2_law(fuel, name):
    a = ATMOSPHERES[name]
    r = simulate(fuel, a["p_atm"], a["x_o2"], d0_mm=3.0, gravity=a["g"])
    s = r["series"]
    t, d = np.array(s["t_s"]), np.array(s["d_mm"])
    assert d[0] == pytest.approx(3.0)
    assert np.all(np.diff(d) <= 1e-9)  # droplet only shrinks
    np.testing.assert_allclose(d ** 2, 9.0 - r["K_mm2_s"] * t, atol=1e-3)  # d^2 linear in t with slope K
    np.testing.assert_allclose(s["flame_d_mm"], np.array(s["d_mm"]) * r["standoff"], rtol=1e-3, atol=1e-3)
    assert d[-1] == pytest.approx(r["d_ext_mm"] if r["extinguishes"] else 0.0, abs=1e-3)
    assert 0.0 <= s["burned_frac"][-1] <= 1.0


def test_microgravity_K_matches_scenario_and_earth_is_faster():
    a = PRESETS["ISS cabin air"]
    for fuel in ("Methanol", "Heptane"):
        p = predict(fuel, a["p_atm"], a["x_o2"])
        mu = simulate(fuel, a["p_atm"], a["x_o2"], gravity=0)
        earth = simulate(fuel, a["p_atm"], a["x_o2"], gravity=1)
        assert mu["K_mm2_s"] == pytest.approx(p["K_hybrid_mm2_s"])
        assert earth["K_mm2_s"] == pytest.approx(p["K_hybrid_mm2_s"] * p["earth_factor"])
        assert earth["t_end_s"] < mu["t_end_s"]
        assert not earth["extinguishes"]  # extinction is not modelled at 1 g


def test_extinction_only_inside_tested_conditions():
    low = simulate("Methanol", 1.0, 0.16, d0_mm=3.0)  # low O2 at 1 atm: inside FLEX data, P(ext) > 0.5
    assert low["status"] == "in range" and low["P_extinction"] >= 0.5
    assert low["extinguishes"] and 0 < low["d_ext_mm"] < 3.0 and low["unburned_fraction"] > 0
    moon = simulate("Methanol", PRESETS["Moon base / rover (planned)"]["p_atm"], 0.30)
    assert moon["status"] != "in range" and not moon["extinguishes"]


def test_blackbody_colour_gets_whiter_and_bluer_with_temperature():
    cols = [blackbody_srgb(T) for T in (1000, 1500, 2000, 2500, 3000, 6500)]
    assert all(np.diff([c[1] / c[0] for c in cols]) > 0)  # green/red rises
    assert all(np.diff([c[2] / c[0] for c in cols]) >= 0) and cols[-1][2] > cols[2][2]  # blue/red never falls
    assert min(cols[-1]) > 0.85  # ~6500 K blackbody is close to white


def test_html_payload_is_safe():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
    from flame_view import html
    r = simulate("Methanol", 1.0, 0.21)
    r["label"] = "</script><b>x"
    page = html([r, r])
    assert page.count("</script>") == 1 and "__DATA__" not in page
