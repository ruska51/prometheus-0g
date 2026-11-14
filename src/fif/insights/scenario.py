"""Scenario prediction for the dashboard (MVP M4): one call -> physics, hybrid, band, ISS ratio, extinction trend,
reliability label, Earth factor and nearest FLEX tests. The app only displays what this returns.
"""
from __future__ import annotations

import functools

import joblib
import numpy as np
import pandas as pd

from fif.data.catalog import REPO_ROOT
from fif.models.features import EXTINCTION_UI_MODEL, conditions_table
from fif.models.train import _aux
from fif.physics.droplet import G_MOON_RATIO, buoyancy_factor
from fif.validation.reliability import reliability

PRESETS = {  # sources: docs/INSIGHTS.md "Cabin atmospheres"
    "ISS cabin air": {"x_o2": 0.21, "p_atm": 1.0, "src": "NASA/TP-2015-216046 Table I (FLEX cabin-air tests)"},
    "Moon base / rover (planned)": {"x_o2": 0.30, "p_atm": 10.2 / 14.696, "src": "Challenge page: O2 30 % or greater at 10.2 psi or less"},
    "Spacesuit": {"x_o2": 1.0, "p_atm": 4.3 / 14.696, "src": "Challenge page: 100 % O2 at 4.3 psi"},
}


@functools.lru_cache(maxsize=1)
def _models():
    k = joblib.load(REPO_ROOT / "models" / "K_hybrid.joblib")
    e = joblib.load(REPO_ROOT / "models" / f"ext_{EXTINCTION_UI_MODEL}.joblib")
    return k, e


@functools.lru_cache(maxsize=1)
def _flex():
    f = pd.read_csv(REPO_ROOT / "data" / "processed" / "flex.csv")
    return f[f["use_in_model"]]


def predict(fuel: str, p_atm: float, x_o2: float, x_co2: float = 0.0, x_he: float = 0.0, d0_mm: float = 3.0) -> dict:
    k, e = _models()
    c = conditions_table(fuel, [p_atm, 1.0], [x_o2, 0.21], [x_co2, 0.0], [x_he, 0.0], d0_mm)
    mu, sd = k["model"].predict(c[k["features"]].to_numpy(), aux=_aux(c))
    rel = reliability(fuel, p_atm, x_o2, x_co2, x_he, d0_mm, sigma_log=float(sd[0]))
    show_model = rel["status"] != "unreliable"
    p_ext = float(e["model"].predict_proba(c[e["features"]].to_numpy())[0, 1])
    f = _flex()
    f = f[f["fuel"] == fuel]
    dist = np.hypot((f["x_o2"] - x_o2) / 0.02, np.log(f["p_atm"] / p_atm) / 0.05) + np.abs(f["x_co2"] - x_co2) / 0.05 \
        + np.abs(f["x_he"] - x_he) / 0.05
    near = f.assign(distance=dist).nsmallest(5, "distance")[
        ["flex_identifier", "x_o2", "x_co2", "x_he", "p_atm", "d0_mm_orig", "K_mm2_s_orig", "test_end", "source_id", "row_id"]]
    return {
        "K_theory_mm2_s": float(c["K_theory"].iloc[0] * 1e6),
        "K_hybrid_mm2_s": float(np.exp(mu[0]) * 1e6) if show_model else None,
        "K_band_mm2_s": [float(np.exp(mu[0] - 1.96 * sd[0]) * 1e6), float(np.exp(mu[0] + 1.96 * sd[0]) * 1e6)] if show_model else None,
        "sigma_log": float(sd[0]),
        "ratio_vs_iss": float(np.exp(mu[0] - mu[1])) if show_model else float(c["K_theory"].iloc[0] / c["K_theory"].iloc[1]),
        "ratio_basis": "hybrid model" if show_model else "physics theory only",
        "T_f_K": float(c["T_f"].iloc[0]),
        "P_extinction": p_ext,
        "earth_factor": float(1 + c["f_B"].iloc[0]),
        "earth_Gr": float(c["Gr"].iloc[0]),
        "moon_factor": float(buoyancy_factor(c["Gr"].iloc[0], G_MOON_RATIO)),  # upper bound of the lunar-surface rate
        "moon_Gr": float(c["Gr"].iloc[0] * G_MOON_RATIO),
        "reliability": rel,
        "nearest_tests": near,
    }


def risk_grid(fuel: str, o2=None, p=None, d0_mm: float = 3.0) -> pd.DataFrame:
    """Hybrid K relative to ISS air over O2 x pressure; status per cell (N2 balance)."""
    o2 = np.round(np.arange(0.12, 0.405, 0.02), 2) if o2 is None else np.asarray(o2)
    p = np.round(np.arange(0.30, 1.11, 0.05), 2) if p is None else np.asarray(p)
    k, _ = _models()
    O, P = np.meshgrid(o2, p)
    c = conditions_table(fuel, P.ravel(), O.ravel(), d0_mm=d0_mm)
    mu, sd = k["model"].predict(c[k["features"]].to_numpy(), aux=_aux(c))
    ref = conditions_table(fuel, 1.0, 0.21, d0_mm=d0_mm)
    mu0, _ = k["model"].predict(ref[k["features"]].to_numpy(), aux=_aux(ref))
    status = [reliability(fuel, pp, oo, 0, 0, d0_mm, sigma_log=float(s))["status"] for pp, oo, s in zip(P.ravel(), O.ravel(), sd)]
    return pd.DataFrame({"x_o2": O.ravel(), "p_atm": P.ravel(), "ratio_vs_iss": np.exp(mu - mu0[0]), "sigma_log": sd,
                         "status": status})
