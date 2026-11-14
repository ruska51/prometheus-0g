"""Reliability label for a prediction (ADR-031, Ruslan: tested range + sigma > 0.20).

- "extrapolation": at least one pre-ignition condition outside the FLEX tested range (ranges from the
  processed data, rows used for modeling; docs/DATA_QUALITY.md section 4 and validation_results.json).
- "unreliable": GP predictive sigma of ln K above SIGMA_UNRELIABLE (95 % band wider than x/÷ exp(1.96*0.20) = 1.48).
- otherwise "in range".
If both apply, "unreliable" wins and both reasons are listed.
"""
from __future__ import annotations

SIGMA_UNRELIABLE = 0.20

# Tested FLEX ranges (rows with use_in_model; data/processed/flex.csv, 2026-11-14 build)
TESTED = {
    "fuel": {"Methanol", "Heptane"},
    "p_atm": (0.693, 3.05),
    "x_o2": (0.12, 0.34),
    "x_co2": (0.0, 0.70),
    "x_he": (0.0, 0.45),
    "d0_mm": (1.1, 4.67),
}


O2_WINDOW = 0.02  # joint check: tested pressures of the same fuel + diluent within +-0.02 O2


def _tested_rows():
    import functools

    import pandas as pd

    from fif.data.catalog import REPO_ROOT

    @functools.lru_cache(maxsize=1)
    def load():
        f = pd.read_csv(REPO_ROOT / "data" / "processed" / "flex.csv")
        return f[f["use_in_model"]][["fuel", "diluent", "x_o2", "p_atm"]]
    return load()


def reliability(fuel, p_atm, x_o2, x_co2, x_he, d0_mm, sigma_log=None) -> dict:
    reasons = []
    # joint (combination) check: was this O2 level tested at this pressure for this fuel and diluent?
    if fuel in TESTED["fuel"]:
        dil = "CO2" if x_co2 > 0 else ("He" if x_he > 0 else "N2")
        t = _tested_rows()
        near = t[(t["fuel"] == fuel) & (t["diluent"] == dil) & ((t["x_o2"] - x_o2).abs() <= O2_WINDOW + 1e-9)]
        if near.empty:
            reasons.append(f"O2 {x_o2:.3g} with {dil} never tested for {fuel} (window +-{O2_WINDOW})")
        elif not (near["p_atm"].min() - 1e-9 <= p_atm <= near["p_atm"].max() + 1e-9):
            reasons.append(f"pressure {p_atm:.3g} atm outside tested {near['p_atm'].min():.3f}-{near['p_atm'].max():.3f} atm "
                           f"for {fuel}, {dil}, O2 {x_o2:.2f}+-{O2_WINDOW}")
    if fuel not in TESTED["fuel"]:
        reasons.append(f"fuel {fuel} not tested")
    for name, val in (("p_atm", p_atm), ("x_o2", x_o2), ("x_co2", x_co2), ("x_he", x_he), ("d0_mm", d0_mm)):
        lo, hi = TESTED[name]
        if not (lo <= val <= hi):
            label = {"p_atm": "pressure", "x_o2": "O2", "x_co2": "CO2", "x_he": "He", "d0_mm": "droplet size"}[name]
            reasons.append(f"{label} {val:.3g} outside tested {lo:g}-{hi:g}")
    if x_co2 > 0 and x_he > 0:
        reasons.append("CO2 and He together were never tested")
    status = "extrapolation" if reasons else "in range"
    if sigma_log is not None and sigma_log > SIGMA_UNRELIABLE:
        reasons.append(f"model uncertainty sigma_lnK {sigma_log:.2f} > {SIGMA_UNRELIABLE}")
        status = "unreliable"
    return {"status": status, "reasons": reasons}
