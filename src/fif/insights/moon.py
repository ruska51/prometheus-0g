"""The headline answer "Fire on the Moon" for the Overview page (post-stage 10, ADR-043; renamed in ADR-046).

Every number is computed here from the same sources the rest of the dashboard uses - nothing is typed by hand:
- burning rate in Moon-base air vs ISS cabin air: hybrid model (fif.insights.scenario.predict), 95 % band of the
  ratio from the model's uncertainty (same formula as insight P2);
- burn-out time of a 3 mm droplet: d2-law with that K (fif.insights.flame_sim.simulate), ISS air / Moon-base air in
  microgravity / Moon-base air on the lunar surface (upper bound, 1/6 g);
- self-extinction: measured FLEX share of N2 tests in which the flame went out at a finite diameter, O2 >= 0.30 vs
  O2 <= 0.21 (same rule as insight S4);
- lunar-surface factor: Law & Williams buoyancy correction at 1/6 g (upper bound, insight P5);
- solids at lunar gravity: NASA literature (insight P6).
"""

from __future__ import annotations

import functools

import numpy as np

from .catalog import _flex
from .flame_sim import ATMOSPHERES, simulate
from .scenario import PRESETS, predict


@functools.lru_cache(maxsize=2)
def moon_answer(fuel: str = "Methanol") -> dict:
    iss, moon = PRESETS["ISS cabin air"], PRESETS["Moon base / rover (planned)"]
    r_iss = predict(fuel, iss["p_atm"], iss["x_o2"])
    r_moon = predict(fuel, moon["p_atm"], moon["x_o2"])
    # ratio band: ln ratio +- 1.96 * sqrt(s1^2 + s2^2), sigma_log from the hybrid model
    lr = np.log(r_moon["K_hybrid_mm2_s"] / r_iss["K_hybrid_mm2_s"])
    sd = float(np.hypot(r_moon["sigma_log"], r_iss["sigma_log"]))
    t_iss = simulate(fuel, iss["p_atm"], iss["x_o2"], d0_mm=3.0, gravity=0)["t_end_s"]
    t_moon = simulate(fuel, moon["p_atm"], moon["x_o2"], d0_mm=3.0, gravity=0)["t_end_s"]
    lunar = ATMOSPHERES["Moon base on the lunar surface (1/6 g)"]
    t_lunar = simulate(fuel, lunar["p_atm"], lunar["x_o2"], d0_mm=3.0, gravity=lunar["g"])["t_end_s"]
    f = _flex()
    lab = f[f["extinct_finite_d"].notna() & (f["diluent"] == "N2")]
    hi, lo = lab[lab["x_o2"] >= 0.30], lab[lab["x_o2"] <= 0.21]
    return {
        "fuel": fuel,
        "k_ratio": float(np.exp(lr)),
        "k_ratio_band": [float(np.exp(lr - 1.96 * sd)), float(np.exp(lr + 1.96 * sd))],
        "status": r_moon["reliability"]["status"],
        "burn_time_iss_s": float(t_iss),
        "burn_time_moon_s": float(t_moon),
        "burn_time_lunar_surface_s": float(t_lunar),
        "moon_factor": float(r_moon["moon_factor"]),
        "self_ext_low_o2": float(lo["extinct_finite_d"].mean()),
        "n_low_o2": int(len(lo)),
        "self_ext_high_o2": float(hi["extinct_finite_d"].mean()),
        "n_high_o2": int(len(hi)),
        "flame_temperature_iss_K": float(r_iss["T_f_K"]),
        "flame_temperature_moon_K": float(r_moon["T_f_K"]),
    }
