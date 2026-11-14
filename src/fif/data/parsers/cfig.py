"""Parser for PSI-159 ACME CFI-G Experimental Tables (normal + inverse flames) -> interim table.

Inputs: ``PSI-159_Experimental table_CFI-G_Normal Flames.csv`` (179 rows) and
``PSI-159_Experimental table_CFI-G_Inverse Flames.csv`` (154 rows).
Output: one row per CSV data row; columns of both files mapped to common interim names,
original units (bar, mg/s, K, degC, s); raw text kept for every parsed cell. No corrections.

Meaning of XO2 differs by flame type (to confirm in stage 4, PHYSICS.md): normal flames burn
fuel issuing from the spherical burner into an O2/N2 chamber (XO2 = chamber O2 before/after test);
inverse flames issue the O2/N2 oxidizer into a fuel/N2 chamber (challenge text; XO2 = supplied O2).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .common import read_csv_text, to_float

SOURCE_ID = "PSI-159"

# interim name -> header, per file; None = column absent in that file
MAP = {
    "normal": {
        "text": {
            "flame_type": "Flame Type",
            "fuel_label": "Fuel",
            "test_id": "Test",
            "cool_flame": "Cool flame?",
            "tfp": "TFP",
            "hot_ignition": "Hot ignition",
            "end_mode": "Self-ext or flow term",
            "color": None,
            "comments": "Comments",
        },
        "num": {
            "day": "Day",
            "x_o2_chamber_before": "XO2 before test",
            "x_o2_chamber_after": "XO2  after test",
            "p_bar": "approx p (bar)",
            "x_fuel_supply": "Xf",
            "m_fuel_mg_s": "mHC (mg/s)",
            "tad_K": "Tad (K)",
            "z_st": "Zst",
            "burn_time_s": "burn time (sec)",
            "peak_burner_T_C": "Peak burner T (C )",
        },
    },
    "inverse": {
        "text": {
            "flame_type": "Flame Type",
            "fuel_label": "Fuel",
            "test_id": "Test",
            "cool_flame": None,
            "tfp": "TFP",
            "hot_ignition": "Hot ignition",
            "end_mode": "Self -ext or flow term",
            "color": "Color",
            "comments": "Comments",
        },
        "num": {
            "day": "Day",
            "x_fuel_chamber_before": "Xf  before test",
            "x_fuel_chamber_after": "Xf  after test",
            "p_bar": "approx p (bar)",
            "x_o2_supply": "XO2",
            "m_fuel_mg_s": "HC burnrate (mg/s)",
            "m_o2_mg_s": "O2 flow rate (mg/s)",
            "tad_K": "Tad (K)",
            "z_st": "Zst",
            "burn_time_s": "burn time (sec)",
            "peak_burner_T_C": "Peak burner Temp (C)",
            "peak_burner_T_K": "Peak burner temp (K)",
        },
    },
}


def parse_one(path: Path, kind: str) -> pd.DataFrame:
    _, rows = read_csv_text(path)
    header = [c.strip() for c in rows[0]]
    spec = MAP[kind]
    needed = [h for h in list(spec["text"].values()) + list(spec["num"].values()) if h]
    missing = [h for h in needed if h not in header]
    if missing:
        raise ValueError(f"CFI-G {kind}: missing columns {missing}")
    out = []
    for i, r in enumerate(rows[1:], start=1):
        if not any(c.strip() for c in r):
            continue
        cell = dict(zip(header, (c.strip() for c in r)))
        rec = {"source_id": SOURCE_ID, "source_file": path.name, "row_id": i, "table": kind}
        for name, col in spec["text"].items():
            rec[name] = cell.get(col, "") if col else ""
        for name, col in spec["num"].items():
            rec[name] = to_float(cell[col])
            rec[f"{name}__raw"] = cell[col]
        out.append(rec)
    return pd.DataFrame(out)


def parse(normal_path: Path, inverse_path: Path) -> pd.DataFrame:
    """Parse both CFI-G tables and stack them (columns absent in one table are NaN/empty)."""
    return pd.concat([parse_one(normal_path, "normal"), parse_one(inverse_path, "inverse")], ignore_index=True)
