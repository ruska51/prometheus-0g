"""Physics-layer tests: property data provenance, mixing-rule limits, monotonicity, units, gravity.

No textbook worked examples are used: the textbooks named in docs/FORMULAS.md were not accessible
to Claude (docs/PHYSICS.md section 8). Instead every check is against NIST raw data, a NASA source
equation, a limiting case or a physical monotonicity property.
"""
from __future__ import annotations

import numpy as np
import pytest

from fif.physics import droplet, mixing, properties as pr

SP = droplet.SPECIES


def _x(o2=0.21, n2=0.79, co2=0.0, he=0.0, rows=1):
    return np.tile([[o2, n2, co2, he]], (rows, 1))


def test_heats_of_combustion_are_printed_on_nist_pages():
    assert pr.check_delta_c_h_on_page("methanol")
    assert pr.check_delta_c_h_on_page("heptane")


def test_molar_masses_from_nist():
    assert pr.molar_mass("methanol") == pytest.approx(0.0320419)
    assert pr.molar_mass("heptane") == pytest.approx(0.1002019)
    assert pr.molar_mass("He") == pytest.approx(0.004002602)


def test_stoichiometry():
    # CH3OH + 1.5 O2 ; C7H16 + 11 O2 (O2 mass per fuel mass)
    assert droplet.nu_s("methanol") == pytest.approx(1.5 * 31.9988 / 32.0419)
    assert droplet.nu_s("heptane") == pytest.approx(11 * 31.9988 / 100.2019)


def test_boiling_point_monotonic_in_pressure():
    for fuel in ("methanol", "heptane"):
        tb = pr.t_sat(fuel, np.array([0.5, 0.7, 1.0, 2.0, 3.0]) * 101325)
        assert np.all(np.diff(tb) > 0)
    # 1 atm boiling points lie within the NIST saturation table rows bracketing 1 atm
    t = pr.sat_table("heptane")
    i = np.searchsorted(t["P_atm"], 1.0)
    assert t["T"][i - 1] <= pr.t_sat("heptane", 101325) <= t["T"][i]


@pytest.mark.parametrize("sp", ["N2", "O2", "CO2", "He"])
def test_mixing_rules_reduce_to_pure_species(sp):
    x = np.zeros((1, 4)); x[0, SP.index(sp)] = 1.0
    for T in (400.0, 1000.0, 1450.0):
        assert mixing.mixture_viscosity(x, SP, T)[0] == pytest.approx(pr.gas_prop(sp, "mu", T))
        assert mixing.mixture_conductivity(x, SP, T)[0] == pytest.approx(pr.gas_prop(sp, "k", T))
        assert mixing.mixture_cp(x, SP, T)[0] == pytest.approx(pr.gas_prop(sp, "cp", T))


def test_rp1311_phi_equals_wilke_form_in_formulas_md():
    mu = np.array([[2.0e-5, 4.0e-5]]); M = np.array([0.032, 0.004])
    phi = mixing._phi(mu, M)[0]
    wilke = (1 + np.sqrt(mu[0, 0] / mu[0, 1]) * (M[1] / M[0]) ** 0.25) ** 2 / np.sqrt(8 * (1 + M[0] / M[1]))
    assert phi[0, 1] == pytest.approx(wilke)


def test_helium_raises_mixture_conductivity():
    T = 1200.0
    lam_n2 = mixing.mixture_conductivity(_x(), SP, T)[0]
    lam_he = mixing.mixture_conductivity(_x(n2=0.49, he=0.30), SP, T)[0]
    assert lam_he > lam_n2


@pytest.mark.parametrize("fuel", ["methanol", "heptane"])
def test_more_oxygen_burns_faster_and_hotter(fuel):
    o2 = np.array([0.15, 0.21, 0.30])
    x = np.stack([o2, 1 - o2, 0 * o2, 0 * o2], axis=1)
    r = droplet.evaluate(np.array([fuel] * 3), np.full(3, 101325.0), x)
    assert np.all(np.diff(r["B"]) > 0)
    assert np.all(np.diff(r["T_f"]) > 0)
    assert np.all(np.diff(r["K_theory"]) > 0)


def test_flame_temperature_limits():
    # no oxygen -> Z_st = 0 -> T_f = T_inf
    r = droplet.evaluate(np.array(["methanol"]), np.array([101325.0]), _x(o2=0.0, n2=1.0))
    assert r["Z_st"][0] == 0 and r["T_f"][0] == pytest.approx(droplet.T_INF)


def test_units_and_ranges_for_air():
    r = droplet.evaluate(np.array(["methanol", "heptane"]), np.full(2, 101325.0), _x(rows=2))
    # K in m^2/s: the raw theory gives O(1e-6) (FLEX measured 0.2-1.06 mm^2/s)
    assert np.all((r["K_theory"] > 1e-7) & (r["K_theory"] < 1e-5))
    assert np.all((r["T_f"] > 1500) & (r["T_f"] < 4000))
    assert np.all(r["flame_standoff"] > 1)


def test_lower_heating_value_below_higher():
    for fuel in ("methanol", "heptane"):
        hhv = -pr.DELTA_C_H_LIQ_KJ_MOL[fuel][0] * 1000 / pr.molar_mass(fuel)
        assert 0.85 * hhv < droplet.lower_heating_value(fuel) < hhv


def test_earth_gravity_increases_burning_rate():
    r = droplet.evaluate(np.array(["heptane"] * 2), np.full(2, 101325.0), _x(rows=2), d0_m=np.array([1e-3, 4e-3]))
    assert np.all(r["Nu_earth"] > 2)
    assert np.all(r["K_earth_theory"] > r["K_theory"])
    assert r["Nu_earth"][1] > r["Nu_earth"][0]  # bigger droplet -> stronger buoyancy


def test_physics_uses_only_pre_ignition_inputs():
    import inspect
    src = inspect.getsource(droplet.evaluate_flex)
    for post in ("K_m2_s", "d_ext", "burn_time", "test_end", "extinct"):
        assert post not in src


def test_fuel_vapor_cp_matches_nist_printed_values():
    # NIST gas-phase pages: methanol 89.54 J/(mol K) at 1000 K (TRC 1997); heptane 381.58 at 1000 K (Scott 1974)
    assert pr.fuel_vapor_cp("methanol", 1000.0) * pr.molar_mass("methanol") == pytest.approx(89.54)
    assert pr.fuel_vapor_cp("heptane", 1000.0) * pr.molar_mass("heptane") == pytest.approx(381.58)


def test_inner_region_cp_lowers_K_vs_ambient_cp():
    # ADR-026: c_1 (fuel vapour) > cp of air at flame-zone temperatures -> lower K
    r = droplet.evaluate(np.array(["methanol", "heptane"]), np.full(2, 101325.0), _x(rows=2))
    assert np.all(r["c1_fuel_vapor"] > r["cp_g"])
    assert np.all(r["K_theory"] < r["K_theory_ambient_cp"])
