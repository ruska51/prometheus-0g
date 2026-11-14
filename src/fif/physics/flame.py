"""Adiabatic flame temperature with dissociation, as prescribed by Law & Williams (1972) p. 399:
"the adiabatic flame temperature of a stoichiometric system in which the initial temperature of
fuel is T_b and the initial temperature of air is T_inf" (dissociation taken into account, p. 395).

Implementation (ADR-027): Cantera ideal-gas phase built from NASA Glenn thermodynamic data shipped
with Cantera (nasa_gas.yaml; original source McBride, Gordon & Reno, NASA TM-4513, 1993); constant
enthalpy and pressure equilibrium (HP). Fuel enters as vapour at T_b, the oxidiser is the actual
ambient mixture (O2 + N2/CO2/He) at T_inf - the FLEX generalisation of "air" (assumption A8).
Product species: CO2, CO, H2O, H2, OH, H, O, O2, N2, NO, N, He, plus the fuel itself.
"""
from __future__ import annotations

import functools

import cantera as ct
import numpy as np

FUEL_SPECIES = {"methanol": "CH3OH", "heptane": "C7H16,n-heptane"}
N_O2 = {"methanol": 1.5, "heptane": 11.0}
AMBIENT = ["O2", "N2", "CO2", "He"]
PRODUCTS = ["CO2", "CO", "H2O", "H2", "OH", "H", "O", "O2", "N2", "NO", "N", "He"]


@functools.lru_cache(maxsize=None)
def _gas() -> ct.Solution:
    wanted = set(PRODUCTS) | set(FUEL_SPECIES.values())
    species = [s for s in ct.Species.list_from_file("nasa_gas.yaml") if s.name in wanted]
    return ct.Solution(thermo="ideal-gas", species=species)


def adiabatic_flame_temperature(fuel: str, T_fuel: float, x_amb: np.ndarray, T_amb: float, p: float) -> float:
    """Stoichiometric adiabatic flame temperature [K] with dissociation (HP equilibrium).

    x_amb: ambient mole fractions in AMBIENT order (sum 1). Stoichiometric: 1 mol fuel per N_O2 mol O2.
    """
    gas = _gas()
    if x_amb[0] <= 0 or not np.isfinite(p) or p <= 0:
        return float("nan")
    fuel_sp = FUEL_SPECIES[fuel]
    n_ox_total = N_O2[fuel] / x_amb[0]  # mol of ambient mixture that carries the stoichiometric O2
    # enthalpies of the two inlet streams at their own temperatures
    gas.TPX = T_fuel, p, {fuel_sp: 1.0}
    h_fuel = gas.enthalpy_mole  # J/kmol
    gas.TPX = T_amb, p, {s: v for s, v in zip(AMBIENT, x_amb) if v > 0}
    h_ox = gas.enthalpy_mole
    n_tot = 1.0 + n_ox_total
    h_mix = (h_fuel * 1.0 + h_ox * n_ox_total) / n_tot  # J/kmol of mixture
    comp = {fuel_sp: 1.0}
    for s, v in zip(AMBIENT, x_amb):
        if v > 0:
            comp[s] = comp.get(s, 0.0) + v * n_ox_total
    gas.TPX = 0.5 * (T_fuel + T_amb), p, comp
    gas.HP = h_mix / gas.mean_molecular_weight, p  # specific enthalpy J/kg (mean MW constant before equilibrate)
    gas.equilibrate("HP")
    return float(gas.T)


def adiabatic_flame_temperatures(fuel, T_fuel, x_amb, T_amb, p) -> np.ndarray:
    """Vectorised wrapper (loops over rows; ~1 ms per row)."""
    fuel = np.asarray(fuel); T_fuel = np.asarray(T_fuel, dtype=float); p = np.asarray(p, dtype=float)
    x_amb = np.asarray(x_amb, dtype=float)
    return np.array([adiabatic_flame_temperature(f, tf, xa, T_amb, pp)
                     for f, tf, xa, pp in zip(fuel, T_fuel, x_amb, p)])
