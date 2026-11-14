"""Quasi-steady droplet combustion with the Law & Williams (1972) property prescription (ADR-027).

Law & Williams, Combust. Flame 19 (1972) 393-405 (L&W), Eq. (1), pp. 394-395, 399, 404:
    k0 = (8 / rho_F) (lambda_1 / c_1) ln(1 + B),   B = [Y_O,inf q / i - c_1 (T_b - T_inf)] / L
    c_1      = heat capacity of the fuel vapour                                   (p. 394)
    lambda_1 = x lambda_F1 + (1 - x) lambda_a1,  x = 0.4                          (pp. 394-395)
    c_1, lambda_F1, lambda_a1 evaluated at T_1 = (T_b + T_f) / 2                  (p. 395)
    T_f      = adiabatic flame temperature of the stoichiometric system, fuel at T_b, air at T_inf,
               dissociation included                                               (pp. 395, 399)
    q from thermochemical tables, not reduced for dissociation; rho_F and L at T_b (p. 395)
Buoyancy (Earth) correction, L&W Eqs. (4), (9) and p. 404:
    k = k0 (1 + f_B),  f_B = 0.533 Gr^0.52,  Gr = (g rho_2^2 d^3 / mu_2^2)(Delta T_2 / T_2),
    T_2 = (T_f + T_inf)/2, Delta T_2 = T_f - T_inf, rho_2, mu_2 of the ambient gas at T_2 (p. 396);
    fitted for Gr <~ 1 (p. 403) - rows with Gr > 1 are flagged.

Data sources: NIST SRD 69 (saturation, fuel-vapour cp, ambient-gas properties), NASA TR R-132
(Svehla 1962, fuel-vapour conductivity), NASA Glenn thermo data via Cantera (flame temperature),
NASA RP-1311 (gas mixing rules). FLEX generalisation (assumption A8): "air" -> the actual ambient
O2 + N2/CO2/He mixture for lambda_a1, T_f, rho_2, mu_2.

Earlier stage-4 variants are kept for comparison: ``K_theory_ambient_cp`` (cp of ambient gas,
Burke-Schumann T_f) and ``K_theory_c1_only`` (c_1 = fuel vapour, lambda_1 = ambient, Burke-Schumann T_f).
Ambient temperature T_inf = 298.15 K (assumption A1). Units: SI.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from . import flame, mixing
from .properties import (
    DELTA_C_H_LIQ_KJ_MOL,
    fuel_vapor_conductivity,
    fuel_vapor_cp,
    fuel_vapor_cp_table,
    gas_T_range,
    molar_mass,
    sat_prop,
    t_sat,
)

T_INF = 298.15
G0 = 9.80665  # standard gravity, m/s^2
G_MOON_RATIO = 1.0 / 6.0  # g_Moon / g_Earth: "lunar gravity is 1/6 of Earth gravity" (NTRS 20250004015, NASA GRC)


def buoyancy_factor(gr_earth: ArrayLike, g_ratio: float) -> np.ndarray:
    """1 + f_B at gravity g = g_ratio * g_Earth. Gr is proportional to g (Gr = g rho^2 d^3 dT / (mu^2 T)), so
    Gr(g) = g_ratio * Gr_Earth; f_B = 0.533 Gr^0.52 (Law & Williams 1972 Eq. 9, fitted for Gr <~ 1)."""
    return 1.0 + 0.533 * (np.asarray(gr_earth, dtype=float) * g_ratio) ** 0.52


SIGMA = 5.670374419e-8  # W/(m^2 K^4), CODATA 2018
R_U = 8.314462618  # J/(mol K), CODATA 2018
SPECIES = ["O2", "N2", "CO2", "He"]
X_FUEL_REGION1 = 0.4  # L&W pp. 394-395

# Global stoichiometry: CH3OH + 1.5 O2 -> CO2 + 2 H2O ; C7H16 + 11 O2 -> 7 CO2 + 8 H2O
STOICH = {"methanol": {"n_o2": 1.5, "n_h2o": 2}, "heptane": {"n_o2": 11.0, "n_h2o": 8}}


def nu_s(fuel: str) -> float:
    """Stoichiometric O2 mass per unit fuel mass (L&W 'i') [-]."""
    return STOICH[fuel]["n_o2"] * molar_mass("O2") / molar_mass(fuel)


def higher_heating_value(fuel: str) -> float:
    """HHV [J/kg]: -Delta_c H (liquid fuel, liquid water), NIST."""
    return -DELTA_C_H_LIQ_KJ_MOL[fuel][0] * 1000.0 / molar_mass(fuel)


def lower_heating_value(fuel: str) -> float:
    """LHV q [J/kg]: HHV minus vaporisation of the product water at 298.15 K (NIST water saturation table)."""
    h_fg_w = float(sat_prop("water", "h_fg", 298.15)) * molar_mass("water")  # J/mol water
    return higher_heating_value(fuel) - STOICH[fuel]["n_h2o"] * h_fg_w / molar_mass(fuel)


def _burke_schumann_tf(
    Tb: np.ndarray, L: np.ndarray, Q: np.ndarray, zst: np.ndarray, xm: np.ndarray, t_hi: float, n_iter: int = 30
) -> np.ndarray:
    """Constant-cp flame sheet without dissociation (FORMULAS.md section 2); kept for comparison."""
    Tf = np.full(len(Tb), 2000.0)
    for _ in range(n_iter):
        cp = mixing.mixture_cp(xm, SPECIES, np.minimum(0.5 * (Tb + Tf), t_hi))
        Tf = T_INF + zst * ((Tb - T_INF) + (Q - L) / cp)
    return Tf


def evaluate(fuel: ArrayLike, p_Pa: ArrayLike, x: np.ndarray, d0_m: ArrayLike | None = None) -> pd.DataFrame:
    """Physics for each row. fuel: 'methanol'/'heptane'; p_Pa [Pa]; x: ambient mole fractions (rows x 4,
    SPECIES order, summing to 1); d0_m: initial droplet diameter [m] (proxies and Earth correction)."""
    fuel = np.asarray(fuel)
    p = np.asarray(p_Pa, dtype=float)
    x = np.asarray(x, dtype=float)
    n = len(p)
    cols = [
        "T_b",
        "L",
        "rho_l",
        "Q",
        "nu_s",
        "Y_O2",
        "Z_st",
        "T_f",
        "T_1",
        "c1",
        "lambda_F1",
        "lambda_a1",
        "lambda_1",
        "B",
        "K_theory",
        "T_f_burke_schumann",
        "K_theory_ambient_cp",
        "K_theory_c1_only",
        "cp_g",
        "lambda_g",
        "mu_g",
        "rho_g",
        "alpha_g",
        "flame_standoff",
        "chi_rad_proxy",
        "tau_res_proxy",
        "T_2",
        "rho_2",
        "mu_2",
        "Gr",
        "f_B",
        "K_earth_theory",
    ]
    out = {k: np.full(n, np.nan) for k in cols}
    for k in ("T_1_capped", "Gr_above_fit_range"):
        out[k] = np.zeros(n, dtype=bool)
    Y = mixing.mass_fractions(np.nan_to_num(x), SPECIES)
    y_o2 = Y[:, 0]
    M_mix = mixing.mixture_molar_mass(x, SPECIES)
    t_hi_gas = min(gas_T_range(s)[1] for s in SPECIES)
    for f in ("methanol", "heptane"):
        m = (fuel == f) & np.isfinite(p)
        if not m.any():
            continue
        xm, pm = x[m], p[m]
        Tb = t_sat(f, pm)
        L = sat_prop(f, "h_fg", Tb)
        rho_l = sat_prop(f, "rho_l", Tb)
        Q = lower_heating_value(f)
        ns = nu_s(f)
        yo = y_o2[m]
        zst = yo / (yo + ns)
        # --- L&W prescription
        Tf = flame.adiabatic_flame_temperatures(np.full(m.sum(), f), Tb, xm, T_INF, pm)
        T1_raw = 0.5 * (Tb + Tf)
        t_hi = min(t_hi_gas, float(fuel_vapor_cp_table(f)[0].max()))
        T1 = np.minimum(T1_raw, t_hi)
        c1 = fuel_vapor_cp(f, T1)
        lamF = fuel_vapor_conductivity(f, T1)
        lama = mixing.mixture_conductivity(xm, SPECIES, T1)
        lam1 = X_FUEL_REGION1 * lamF + (1 - X_FUEL_REGION1) * lama
        B = (yo * Q / ns - c1 * (Tb - T_INF)) / L
        K = 8 * lam1 / (rho_l * c1) * np.log1p(B)
        # --- earlier variants (comparison only)
        Tf_bs = _burke_schumann_tf(Tb, L, Q, zst, xm, t_hi_gas)
        Tbar_bs = np.minimum(0.5 * (Tb + Tf_bs), t_hi_gas)
        cp_bs = mixing.mixture_cp(xm, SPECIES, Tbar_bs)
        lam_bs = mixing.mixture_conductivity(xm, SPECIES, Tbar_bs)
        B_amb = (yo * Q / ns + cp_bs * (T_INF - Tb)) / L
        K_amb = 8 * lam_bs / (rho_l * cp_bs) * np.log1p(B_amb)
        c1_bs = fuel_vapor_cp(f, np.minimum(0.5 * (Tb + Tf_bs), float(fuel_vapor_cp_table(f)[0].max())))
        B_c1 = (yo * Q / ns + c1_bs * (T_INF - Tb)) / L
        K_c1 = 8 * lam_bs / (rho_l * c1_bs) * np.log1p(B_c1)
        # --- ambient-gas properties at T_1 (proxies) and at T_2 (buoyancy, L&W p. 396)
        cp_g = mixing.mixture_cp(xm, SPECIES, T1)
        mu_g = mixing.mixture_viscosity(xm, SPECIES, T1)
        rho_g = pm * M_mix[m] / (R_U * T1)
        alpha = lama / (rho_g * cp_g)
        fs = np.log1p(B) / np.log1p(yo / ns)
        T2 = np.minimum(0.5 * (Tf + T_INF), t_hi_gas)
        rho2 = pm * M_mix[m] / (R_U * T2)
        mu2 = mixing.mixture_viscosity(xm, SPECIES, T2)
        vals = dict(
            T_b=Tb,
            L=L,
            rho_l=rho_l,
            Q=np.full(m.sum(), Q),
            nu_s=np.full(m.sum(), ns),
            Y_O2=yo,
            Z_st=zst,
            T_f=Tf,
            T_1=T1,
            c1=c1,
            lambda_F1=lamF,
            lambda_a1=lama,
            lambda_1=lam1,
            B=B,
            K_theory=K,
            T_f_burke_schumann=Tf_bs,
            K_theory_ambient_cp=K_amb,
            K_theory_c1_only=K_c1,
            cp_g=cp_g,
            lambda_g=lama,
            mu_g=mu_g,
            rho_g=rho_g,
            alpha_g=alpha,
            flame_standoff=fs,
            T_2=T2,
            rho_2=rho2,
            mu_2=mu2,
        )
        for k, v in vals.items():
            out[k][m] = v
        out["T_1_capped"][m] = T1_raw > t_hi
        if d0_m is not None:
            d0 = np.asarray(d0_m, dtype=float)[m]
            rs = d0 / 2
            # radiative-loss fraction proxy chi/kappa [Pa m] (FORMULAS.md section 3; kappa unknown)
            out["chi_rad_proxy"][m] = SIGMA * pm * Tf**4 * rs**2 * fs**3 * c1 / (3 * lam1 * np.log1p(B) * Q)
            out["tau_res_proxy"][m] = (fs * rs) ** 2 / alpha
            gr = G0 * rho2**2 * d0**3 / mu2**2 * (Tf - T_INF) / T2
            fb = buoyancy_factor(gr, 1.0) - 1.0
            out["Gr"][m], out["f_B"][m], out["K_earth_theory"][m] = gr, fb, K * (1 + fb)
            out["Gr_above_fit_range"][m] = gr > 1.0
    return pd.DataFrame(out)


def evaluate_flex(df: pd.DataFrame) -> pd.DataFrame:
    """Physics columns for the processed FLEX table (pre-ignition inputs only)."""
    x = df[["x_o2", "x_n2", "x_co2", "x_he"]].to_numpy(dtype=float)
    x = x / x.sum(axis=1, keepdims=True)  # assumption A4: renormalised for property evaluation only
    p = df["p_Pa"].to_numpy(dtype=float)
    p = np.where(p > 0, p, np.nan)  # test 114 (P = 0) -> NaN physics
    phys = evaluate(df["fuel"].str.lower().to_numpy(), p, x, df["d0_m"].to_numpy())
    phys.index = df.index
    return phys
