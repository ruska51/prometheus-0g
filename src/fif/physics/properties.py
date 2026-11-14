"""Species property data from the NIST Chemistry WebBook (raw files in data/raw/nist/, stage 4).

Every value used by the physics layer comes from these raw files; nothing is typed in from memory.
- Gas properties (O2, N2, CO2, He) at 1 atm, 300-1500 K: cp [J/(kg K)], viscosity [Pa s],
  thermal conductivity [W/(m K)]. Linear interpolation in T; outside 300-1500 K the value is
  clamped to the table end (callers flag this). Ideal-gas assumption: cp, mu, lambda taken as
  pressure independent over 0.5-3 atm (ADR-023); density is computed from the ideal-gas law.
- Saturation tables (methanol, n-heptane, water): T_sat(P), liquid density, liquid cp,
  enthalpy of vaporization h_v - h_l, interpolated along the saturation curve.
- Molar masses and liquid heats of combustion parsed from the NIST species pages.
Units: SI. See docs/PHYSICS.md section "Property data".
"""
from __future__ import annotations

import functools
import html
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
NIST = ROOT / "data" / "raw" / "nist"

GAS_IDS = {"O2": "C7782447", "N2": "C7727379", "CO2": "C124389", "He": "C7440597"}
LIQ_IDS = {"methanol": "C67561", "heptane": "C142825", "water": "C7732185"}

# Liquid heats of combustion (products CO2(g) + H2O(l)), as printed on the NIST pages:
# methanol: "-725.7 ± 0.1 kJ/mol", Chao and Rossini, 1965 (most recent of the listed calorimetric values);
# n-heptane: "-4817. ± 8. kJ/mol", NIST average of 7 values.
DELTA_C_H_LIQ_KJ_MOL = {"methanol": (-725.7, "-725.7 ± 0.1"), "heptane": (-4817.0, "-4817. ± 8.")}


def _read_tsv(path: Path) -> dict[str, np.ndarray]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    header = lines[0].split("\t")
    cols: dict[str, list] = {h: [] for h in header}
    for ln in lines[1:]:
        parts = ln.split("\t")
        if len(parts) != len(header):
            continue
        for h, v in zip(header, parts):
            cols[h].append(v)
    out = {}
    for h, vals in cols.items():
        nums = []
        for v in vals:
            try:
                nums.append(float(v))
            except ValueError:
                nums.append(np.nan)  # NIST prints 'undefined' near the critical point
        out[h] = np.array(nums) if not all(np.isnan(nums)) else np.array(vals)
    return out


@functools.lru_cache(maxsize=None)
def gas_table(species: str) -> dict[str, np.ndarray]:
    t = _read_tsv(NIST / f"gas_{GAS_IDS[species]}.tsv")
    return {"T": t["Temperature (K)"], "cp": t["Cp (J/g*K)"] * 1000.0,
            "mu": t["Viscosity (Pa*s)"], "k": t["Therm. Cond. (W/m*K)"]}


def gas_prop(species: str, prop: str, T) -> np.ndarray:
    """cp [J/(kg K)], mu [Pa s] or k [W/(m K)] of a pure gas at temperature T [K] (1 atm table)."""
    t = gas_table(species)
    return np.interp(np.asarray(T, dtype=float), t["T"], t[prop])


def gas_T_range(species: str) -> tuple[float, float]:
    t = gas_table(species)["T"]
    return float(t.min()), float(t.max())


@functools.lru_cache(maxsize=None)
def sat_table(liquid: str) -> dict[str, np.ndarray]:
    t = _read_tsv(NIST / f"sat_{LIQ_IDS[liquid]}.tsv")
    return {"T": t["Temperature (K)"], "P_atm": t["Pressure (atm)"],
            "rho_l": t["Density (l, kg/m3)"], "cp_l": t["Cp (l, J/g*K)"] * 1000.0,
            "h_l": t["Enthalpy (l, kJ/kg)"] * 1000.0, "h_v": t["Enthalpy (v, kJ/kg)"] * 1000.0}


def t_sat(liquid: str, p_Pa) -> np.ndarray:
    """Saturation (boiling) temperature [K] at pressure p [Pa]; interpolated in ln P."""
    t = sat_table(liquid)
    lnp = np.log(np.asarray(p_Pa, dtype=float) / 101325.0)
    return np.interp(lnp, np.log(t["P_atm"]), t["T"])


def sat_prop(liquid: str, prop: str, T) -> np.ndarray:
    """Saturated-liquid property at T [K]: rho_l [kg/m3], cp_l [J/(kg K)], or h_fg [J/kg]."""
    t = sat_table(liquid)
    if prop == "h_fg":
        return np.interp(np.asarray(T, dtype=float), t["T"], t["h_v"] - t["h_l"])
    return np.interp(np.asarray(T, dtype=float), t["T"], t[prop])


@functools.lru_cache(maxsize=None)
def molar_mass(species: str) -> float:
    """Molar mass [kg/mol] from 'Molecular weight' on the NIST species page."""
    nid = GAS_IDS.get(species) or LIQ_IDS[species]
    text = (NIST / f"thermo_{nid}.html").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Molecular weight</a>:</strong>\s*([0-9.]+)", text)
    if not m:
        raise ValueError(f"molecular weight not found for {species}")
    return float(m.group(1)) / 1000.0


def check_delta_c_h_on_page(fuel: str) -> bool:
    """True if the NIST page for ``fuel`` prints the Delta_c H liquid value used here."""
    text = html.unescape((NIST / f"thermo_{LIQ_IDS[fuel]}.html").read_text(encoding="utf-8", errors="replace"))
    text = re.sub(r"<[^>]+>", " ", text)
    text = " ".join(text.split())
    return DELTA_C_H_LIQ_KJ_MOL[fuel][1] in text


@functools.lru_cache(maxsize=None)
def fuel_vapor_cp_table(fuel: str) -> tuple[np.ndarray, np.ndarray]:
    """Ideal-gas cp of fuel vapour from the FIRST 'Constant pressure heat capacity of gas' table on the
    NIST gas-phase page (thermo_gas_<ID>.html): methanol - Thermodynamics Research Center 1997 (50-3000 K);
    n-heptane - Scott 1974 (200-1500 K). Returns (T [K], cp [J/(kg K)])."""
    text = (NIST / f"thermo_gas_{LIQ_IDS[fuel]}.html").read_text(encoding="utf-8", errors="replace")
    i = text.find('<table class="data" aria-label="Constant pressure heat capacity of gas">')
    j = text.find("</table>", i)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", text[i:j], flags=re.S)
    pairs = []
    for r in rows:
        cells = re.findall(r'<td class="right-nowrap">(.*?)</td>', r, flags=re.S)
        if len(cells) >= 2:
            cp_txt = html.unescape(re.sub(r"<[^>]+>", "", cells[0])).split("±")[0].strip()
            pairs.append((cp_txt, html.unescape(cells[1]).strip()))
    T = np.array([float(b) for a, b in pairs]); cp = np.array([float(a) for a, b in pairs])
    order = np.argsort(T)
    return T[order], cp[order] / molar_mass(fuel)


def fuel_vapor_cp(fuel: str, T) -> np.ndarray:
    """cp of fuel vapour [J/(kg K)] at T [K] (NIST ideal-gas table, linear interpolation, clamped at ends)."""
    t, cp = fuel_vapor_cp_table(fuel)
    return np.interp(np.asarray(T, dtype=float), t, cp)
