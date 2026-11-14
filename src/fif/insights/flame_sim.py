"""Inputs for the burning-droplet animation (stage 8 extension, ADR-035). Everything shown is computed here;
the JavaScript only draws it.

Physics per panel:
- d^2 law: d(t)^2 = d0^2 - K t (K from the hybrid model; physics-only K if the model is withheld; on Earth
  K x (1 + f_B) with the Law & Williams buoyancy correction, extrapolated - docs/PHYSICS.md section 4).
- Flame-to-droplet diameter ratio: quasi-steady theory r_f/r_s = ln(1+B)/ln(1+Y_O/nu_s) (docs/PHYSICS.md section 5),
  known to overestimate the measured ratio several-fold (NTRS 20130014061, section 3.2): drawn on a common relative scale.
- Extinction (microgravity only, reliability 'in range'): if P(extinction) >= 0.5 (interface logistic model) the flame
  goes out at d_ext = d0 x (d_ext/d0 from the GP model trained on FLEX); otherwise the droplet burns to completion.
  Outside the tested data or on Earth extinction is not predicted (shown as burning to completion, labelled).
- Flame temperature: equilibrium T_f with dissociation (fif.physics.flame).
- Flame colour: heptane (sooty) = colour of a blackbody at T_f (an upper bound - soot is cooler than the adiabatic
  flame), from Planck's law and the analytic CIE 1931 colour-matching fit of Wyman, Sloan & Shirley (JCGT 2(2), 2013),
  converted to sRGB (IEC 61966-2-1 matrix); methanol (nearly soot-free) = faint blue, illustrative only.
  If the GP gives d_ext/d0 >= 1 the flame is not sustained (shown as a brief ignition flash, illustrative).
"""
from __future__ import annotations

import functools

import joblib
import numpy as np

from fif.data.catalog import REPO_ROOT
from fif.models.features import conditions_table

from .scenario import PRESETS, predict

ATMOSPHERES = {  # microgravity cabin atmospheres = scenario.PRESETS; Earth = ISS air at 1 g
    "ISS cabin air (microgravity)": {**PRESETS["ISS cabin air"], "g": 0},
    "Earth sea-level air (1 g)": {**PRESETS["ISS cabin air"], "g": 1,
                                  "src": "same air at 1 g; buoyancy: Law & Williams Eq. (9), extrapolated (docs/PHYSICS.md section 4)"},
    "Moon base / rover (planned)": {**PRESETS["Moon base / rover (planned)"], "g": 0},
    "Spacesuit (microgravity)": {**PRESETS["Spacesuit"], "g": 0},
}


def _g(lam, mu, s1, s2):
    return np.exp(-0.5 * ((lam - mu) / np.where(lam < mu, s1, s2)) ** 2)


def blackbody_srgb(T: float) -> tuple[float, float, float]:
    """Linear-light sRGB colour (max channel = 1) of a blackbody at temperature T [K]."""
    lam = np.arange(380.0, 781.0, 1.0)  # nm
    xb = 1.056 * _g(lam, 599.8, 37.9, 31.0) + 0.362 * _g(lam, 442.0, 16.0, 26.7) - 0.065 * _g(lam, 501.1, 20.4, 26.2)
    yb = 0.821 * _g(lam, 568.8, 46.9, 40.5) + 0.286 * _g(lam, 530.9, 16.3, 31.1)
    zb = 1.217 * _g(lam, 437.0, 11.8, 36.0) + 0.681 * _g(lam, 459.0, 26.0, 13.8)
    h, c, k = 6.62607015e-34, 2.99792458e8, 1.380649e-23  # SI 2019 exact constants
    lm = lam * 1e-9
    B = 1.0 / (lm ** 5 * (np.exp(h * c / (lm * k * T)) - 1.0))
    X, Y, Z = (B * xb).sum(), (B * yb).sum(), (B * zb).sum()
    M = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])
    rgb = np.clip(M @ np.array([X, Y, Z]), 0, None)
    rgb = rgb / rgb.max()
    return tuple(float(v) for v in rgb)


def _to_srgb8(rgb) -> list[int]:
    out = []
    for v in rgb:
        v = 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
        out.append(int(round(255 * min(max(v, 0.0), 1.0))))
    return out


@functools.lru_cache(maxsize=1)
def _dext_model():
    return joblib.load(REPO_ROOT / "models" / "dext_hybrid_gp.joblib")


def simulate(fuel: str, p_atm: float, x_o2: float, x_co2: float = 0.0, x_he: float = 0.0, d0_mm: float = 3.0,
             gravity: int = 0, label: str = "") -> dict:
    s = predict(fuel, p_atm, x_o2, x_co2, x_he, d0_mm)
    c = conditions_table(fuel, p_atm, x_o2, x_co2, x_he, d0_mm)
    status = s["reliability"]["status"]
    K = s["K_hybrid_mm2_s"] if s["K_hybrid_mm2_s"] is not None else s["K_theory_mm2_s"]
    k_src = "hybrid model" if s["K_hybrid_mm2_s"] is not None else "physics only (model withheld)"
    notes = []
    if gravity:
        K = K * s["earth_factor"]
        k_src += f" x (1 + f_B) = x{s['earth_factor']:.1f} (Earth buoyancy, extrapolated)"
        notes.append("Earth: buoyant flame shape is schematic; extinction not modelled at 1 g.")
    d_ext = None
    extinguishes = False
    if gravity:
        pass
    elif status == "in range":
        if s["P_extinction"] >= 0.5:
            m = _dext_model()
            ratio = float(np.exp(m["model"].predict(c[m["features"]].to_numpy())[0][0]))
            d_ext = min(ratio, 1.0) * d0_mm
            extinguishes = True
    else:
        notes.append("Extinction not predicted outside the tested data (P(extinction) shown for reference only).")
    t_end = (d0_mm ** 2 - (d_ext ** 2 if d_ext else 0.0)) / K
    sustained = not (extinguishes and d_ext >= d0_mm * 0.999)
    if not sustained:
        notes.append("Predicted extinction diameter >= initial diameter: no sustained flame (brief ignition flash, illustrative).")
    t = np.linspace(0.0, t_end, 121)
    d = np.sqrt(np.clip(d0_mm ** 2 - K * t, 0.0, None))
    sooty = fuel == "Heptane"
    color = _to_srgb8(blackbody_srgb(s["T_f_K"])) if sooty else [96, 150, 255]
    return {
        "label": label, "fuel": fuel, "gravity": int(gravity), "x_o2": x_o2, "p_atm": p_atm, "p_psi": p_atm * 14.696,
        "d0_mm": d0_mm, "K_mm2_s": float(K), "K_source": k_src, "t_end_s": float(t_end),
        "extinguishes": extinguishes, "d_ext_mm": d_ext, "P_extinction": s["P_extinction"],
        "standoff": float(c["flame_standoff"].iloc[0]), "T_f_K": s["T_f_K"], "status": status,
        "unburned_fraction": float((d_ext / d0_mm) ** 3) if d_ext else 0.0, "notes": notes,
        "sustained": sustained, "sooty": sooty, "flame_rgb": color,
        "series": {"t_s": [round(float(v), 4) for v in t], "d_mm": [round(float(v), 5) for v in d],
                   "flame_d_mm": [round(float(v) * float(c["flame_standoff"].iloc[0]), 4) for v in d],
                   "burned_frac": [round(float(1 - (v / d0_mm) ** 3), 5) for v in d]},
        "src": "K: docs/MODEL_CARD.md; d^2 law and r_f/r_s: docs/PHYSICS.md sections 3-5; d_ext: models/dext_hybrid_gp.joblib",
    }
