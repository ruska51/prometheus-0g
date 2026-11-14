"""Quasi-steady droplet combustion (level L2 + L3 proxies, ADR-022). Vectorised, SI units.

Burning-rate constant (NTRS 20130014061, Nayagam, Dietrich, Hicks & Williams, Eqs. 1-2):
    K = 8 lambda_g / (rho_l cp_g) * ln(1 + B),
    B = (q_f Y_O,inf nu_f + cp_g (T_inf - T_b)) / L,
with nu_f the stoichiometric fuel-to-oxygen mass ratio (= 1 / nu_s below).
L2 additions (ADR-022): T_b(P) from the NIST saturation curve; lambda_g, cp_g of the ambient
O2 + diluent mixture (NASA RP-1311 mixing rules) at T_bar = (T_b + T_f)/2, capped at 1500 K
(ADR-023); flame temperature from the Burke-Schumann flame sheet (docs/FORMULAS.md section 2):
    T_f = T_inf + Z_st [(T_s - T_inf) + (Q - L)/cp],  Z_st = Y_O,inf / (Y_O,inf + nu_s),  T_s = T_b.
L3 proxies (ADR-022): flame-standoff ratio, radiative-loss proxy, residence-time proxy.
Gravity (ADR-024): base = microgravity (Nu = 2); Earth estimate K_1g/K_0g = Nu/2 with
Nu = 2 + 0.6 Gr^(1/4) Pr^(1/3) (docs/FORMULAS.md section 6; textbook source not checked by Claude).
Ambient temperature T_inf = 298.15 K (FLEX-2 PSI-68 Experimental Table lists 25 C; FLEX CSV has
no temperature column) - assumption A1 in docs/PHYSICS.md.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import mixing
from .properties import gas_T_range, molar_mass, sat_prop, t_sat, DELTA_C_H_LIQ_KJ_MOL

T_INF = 298.15
G0 = 9.80665  # standard gravity, m/s^2 (CGPM 1901 definition)
SIGMA = 5.670374419e-8  # Stefan-Boltzmann, W/(m^2 K^4) (CODATA 2018 exact-derived value)
R_U = 8.314462618  # J/(mol K) (CODATA 2018)
SPECIES = ["O2", "N2", "CO2", "He"]

# Global stoichiometry: CH3OH + 1.5 O2 -> CO2 + 2 H2O ; C7H16 + 11 O2 -> 7 CO2 + 8 H2O
STOICH = {"methanol": {"n_o2": 1.5, "n_h2o": 2}, "heptane": {"n_o2": 11.0, "n_h2o": 8}}


def nu_s(fuel: str) -> float:
    """Stoichiometric O2 mass per unit fuel mass [-]."""
    return STOICH[fuel]["n_o2"] * molar_mass("O2") / molar_mass(fuel)


def lower_heating_value(fuel: str) -> float:
    """Q [J/kg fuel]: -Delta_c H(liquid, NIST) minus vaporisation of product water at 298.15 K (NIST)."""
    hhv = -DELTA_C_H_LIQ_KJ_MOL[fuel][0] * 1000.0  # J/mol fuel, liquid water in products
    h_fg_w = float(sat_prop("water", "h_fg", 298.15)) * molar_mass("water")  # J/mol water
    return (hhv - STOICH[fuel]["n_h2o"] * h_fg_w) / molar_mass(fuel)


def evaluate(fuel, p_Pa, x, d0_m=None, n_iter: int = 30) -> pd.DataFrame:
    """Physics for each test row.

    fuel: array of 'methanol'/'heptane'; p_Pa: pressure [Pa]; x: mole fractions (rows x 4) in SPECIES order;
    d0_m: initial droplet diameter [m] (only for the L3 proxies and the gravity estimate).
    Returns a DataFrame with SI columns (see docs/DATA_DICTIONARY.md, physics section).
    """
    fuel = np.asarray(fuel)
    p = np.asarray(p_Pa, dtype=float)
    x = np.asarray(x, dtype=float)
    n = len(p)
    out = {k: np.full(n, np.nan) for k in
           ["T_b", "L", "rho_l", "Q", "nu_s", "Y_O2", "Z_st", "T_f", "T_bar", "cp_g", "lambda_g",
            "mu_g", "rho_g", "B", "K_theory", "flame_standoff", "alpha_g", "chi_rad_proxy",
            "tau_res_proxy", "Gr", "Pr", "Nu_earth", "K_earth_theory"]}
    out["T_bar_capped"] = np.zeros(n, dtype=bool)
    Y = mixing.mass_fractions(x, SPECIES)
    y_o2 = Y[:, 0]
    M_mix = mixing.mixture_molar_mass(x, SPECIES)
    t_hi = min(gas_T_range(s)[1] for s in SPECIES)
    for f in ("methanol", "heptane"):
        m = fuel == f
        if not m.any():
            continue
        Tb = t_sat(f, p[m])
        L = sat_prop(f, "h_fg", Tb)
        rho_l = sat_prop(f, "rho_l", Tb)
        Q = lower_heating_value(f)
        ns = nu_s(f)
        zst = y_o2[m] / (y_o2[m] + ns)
        xm = x[m]
        Tf = np.full(m.sum(), 2000.0)
        for _ in range(n_iter):  # fixed point: cp depends on T_bar, which depends on T_f
            Tbar = np.minimum(0.5 * (Tb + Tf), t_hi)
            cp = mixing.mixture_cp(xm, SPECIES, Tbar)
            Tf = T_INF + zst * ((Tb - T_INF) + (Q - L) / cp)
        Tbar_raw = 0.5 * (Tb + Tf)
        Tbar = np.minimum(Tbar_raw, t_hi)
        cp = mixing.mixture_cp(xm, SPECIES, Tbar)
        lam = mixing.mixture_conductivity(xm, SPECIES, Tbar)
        mu = mixing.mixture_viscosity(xm, SPECIES, Tbar)
        rho_g = p[m] * M_mix[m] / (R_U * Tbar)
        B = (Q * y_o2[m] / ns + cp * (T_INF - Tb)) / L
        K = 8 * lam / (rho_l * cp) * np.log1p(B)
        fs = np.log1p(B) / np.log1p(y_o2[m] / ns)
        alpha = lam / (rho_g * cp)
        for k, v in dict(T_b=Tb, L=L, rho_l=rho_l, Q=np.full(m.sum(), Q), nu_s=np.full(m.sum(), ns),
                         Y_O2=y_o2[m], Z_st=zst, T_f=Tf, T_bar=Tbar, cp_g=cp, lambda_g=lam, mu_g=mu,
                         rho_g=rho_g, B=B, K_theory=K, flame_standoff=fs, alpha_g=alpha).items():
            out[k][m] = v
        out["T_bar_capped"][m] = Tbar_raw > t_hi
        if d0_m is not None:
            d0 = np.asarray(d0_m, dtype=float)[m]
            rs = d0 / 2
            # radiative-loss fraction proxy chi/kappa [Pa m]: kappa (Planck-mean absorption per unit pressure) unknown
            out["chi_rad_proxy"][m] = (SIGMA * p[m] * Tf ** 4 * rs ** 2 * fs ** 3 * cp
                                       / (3 * lam * np.log1p(B) * Q))
            # flow (diffusion) time at the flame r_f^2 / alpha [s]; Arrhenius factor not included (no sourced Ea)
            out["tau_res_proxy"][m] = (fs * rs) ** 2 / alpha
            nu_kin = mu / rho_g
            gr = G0 * (Tf - T_INF) * d0 ** 3 / (T_INF * nu_kin ** 2)
            pr = mu * cp / lam
            nu_e = 2 + 0.6 * gr ** 0.25 * pr ** (1 / 3)
            out["Gr"][m], out["Pr"][m], out["Nu_earth"][m] = gr, pr, nu_e
            out["K_earth_theory"][m] = K * nu_e / 2
    return pd.DataFrame(out)


def evaluate_flex(df: pd.DataFrame) -> pd.DataFrame:
    """Physics columns for the processed FLEX table (pre-ignition inputs only)."""
    x = df[["x_o2", "x_n2", "x_co2", "x_he"]].to_numpy(dtype=float)
    x = x / x.sum(axis=1, keepdims=True)  # rows with sum 0.98 renormalised HERE only, for property evaluation (A4)
    p = df["p_Pa"].to_numpy(dtype=float)
    p = np.where(p > 0, p, np.nan)  # test 114 (P = 0) -> NaN physics
    phys = evaluate(df["fuel"].str.lower().to_numpy(), p, x, df["d0_m"].to_numpy())
    phys.index = df.index
    return phys
