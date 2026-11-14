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
from numpy.typing import ArrayLike

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


@functools.cache
def gas_table(species: str) -> dict[str, np.ndarray]:
    t = _read_tsv(NIST / f"gas_{GAS_IDS[species]}.tsv")
    return {
        "T": t["Temperature (K)"],
        "cp": t["Cp (J/g*K)"] * 1000.0,
        "mu": t["Viscosity (Pa*s)"],
        "k": t["Therm. Cond. (W/m*K)"],
    }


def gas_prop(species: str, prop: str, T: ArrayLike) -> np.ndarray:
    """cp [J/(kg K)], mu [Pa s] or k [W/(m K)] of a pure gas at temperature T [K] (1 atm table)."""
    t = gas_table(species)
    return np.interp(np.asarray(T, dtype=float), t["T"], t[prop])


def gas_T_range(species: str) -> tuple[float, float]:
    t = gas_table(species)["T"]
    return float(t.min()), float(t.max())


@functools.cache
def sat_table(liquid: str) -> dict[str, np.ndarray]:
    t = _read_tsv(NIST / f"sat_{LIQ_IDS[liquid]}.tsv")
    return {
        "T": t["Temperature (K)"],
        "P_atm": t["Pressure (atm)"],
        "rho_l": t["Density (l, kg/m3)"],
        "cp_l": t["Cp (l, J/g*K)"] * 1000.0,
        "h_l": t["Enthalpy (l, kJ/kg)"] * 1000.0,
        "h_v": t["Enthalpy (v, kJ/kg)"] * 1000.0,
    }


def t_sat(liquid: str, p_Pa: ArrayLike) -> np.ndarray:
    """Saturation (boiling) temperature [K] at pressure p [Pa]; interpolated in ln P."""
    t = sat_table(liquid)
    lnp = np.log(np.asarray(p_Pa, dtype=float) / 101325.0)
    return np.interp(lnp, np.log(t["P_atm"]), t["T"])


def sat_prop(liquid: str, prop: str, T: ArrayLike) -> np.ndarray:
    """Saturated-liquid property at T [K]: rho_l [kg/m3], cp_l [J/(kg K)], or h_fg [J/kg]."""
    t = sat_table(liquid)
    if prop == "h_fg":
        return np.interp(np.asarray(T, dtype=float), t["T"], t["h_v"] - t["h_l"])
    return np.interp(np.asarray(T, dtype=float), t["T"], t[prop])


@functools.cache
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


@functools.cache
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
    T = np.array([float(b) for a, b in pairs])
    cp = np.array([float(a) for a, b in pairs])
    order = np.argsort(T)
    return T[order], cp[order] / molar_mass(fuel)


def fuel_vapor_cp(fuel: str, T: ArrayLike) -> np.ndarray:
    """cp of fuel vapour [J/(kg K)] at T [K] (NIST ideal-gas table, linear interpolation, clamped at ends)."""
    t, cp = fuel_vapor_cp_table(fuel)
    return np.interp(np.asarray(T, dtype=float), t, cp)


# --- Fuel-vapour thermal conductivity (Law & Williams lambda_F1), ADR-027 -----------------------------
SVEHLA = ROOT / "data" / "raw" / "nasa_tr_r132" / "svehla_1962_extract.csv"
CAL_CM_S_K_TO_W_M_K = 418.4  # 1 cal/(cm s K) = 4.184 J/cal * 100 cm/m (thermochemical calorie)
R_CAL = 1.98726  # cal/(mol K), reproduces Svehla's Table III columns to the printed precision (tests)


@functools.cache
def svehla_table(species: str) -> dict[str, np.ndarray]:
    """Transcription of NASA TR R-132 (Svehla 1962): Table III p. 56 (CH3OH), Table IV p. 119 (n-C5H12, n-C6H14)."""
    import csv

    rows = [r for r in csv.DictReader(open(SVEHLA, encoding="utf-8")) if r["species"] == species]

    def col(k: str) -> np.ndarray:
        return np.array([float(r[k]) if r[k] else np.nan for r in rows])

    return {
        "T": col("T_K"),
        "cp_over_R": col("cp_over_R"),
        "eta_poise": col("eta_x1e6_poise") * 1e-6,
        "lambda_cal": col("lambda_x1e6_cal_cm_s_K") * 1e-6,
    }


def svehla_lambda(eta_Pa_s: ArrayLike, cp_J_kg_K: ArrayLike, M_kg_mol: float) -> np.ndarray:
    """Svehla (1962) Eq. (2): lambda = (R/M) [15/4 + 1.32 (Cp/R - 5/2)] eta  [W/(m K)], SI inputs."""
    R = 8.314462618
    cp_over_R = cp_J_kg_K * M_kg_mol / R
    return (R / M_kg_mol) * (15 / 4 + 1.32 * (cp_over_R - 2.5)) * eta_Pa_s


def fuel_vapor_conductivity(fuel: str, T: ArrayLike) -> np.ndarray:
    """lambda_F1 [W/(m K)] of fuel vapour at T [K] (clamped to 300-2000 K).

    methanol: Svehla Table III total conductivity (interpolated).
    n-heptane: not tabulated by Svehla. Viscosity extrapolated linearly in carbon number from n-C5H12 and
    n-C6H14 (Svehla Table IV), following Law & Williams p. 399 ("extrapolating values for n-alkanes with
    lower carbon-atom contents"); conductivity from Svehla Eq. (2) with the NIST ideal-gas cp of n-heptane.
    """
    T = np.clip(np.asarray(T, dtype=float), 300.0, 2000.0)
    if fuel == "methanol":
        t = svehla_table("CH3OH")
        return np.interp(T, t["T"], t["lambda_cal"]) * CAL_CM_S_K_TO_W_M_K
    if fuel == "heptane":
        c5, c6 = svehla_table("n-C5H12"), svehla_table("n-C6H14")
        eta7 = 2 * np.interp(T, c6["T"], c6["eta_poise"]) - np.interp(T, c5["T"], c5["eta_poise"])
        return svehla_lambda(eta7 * 0.1, fuel_vapor_cp("heptane", T), molar_mass("heptane"))
    raise ValueError(fuel)
