"""Parser for PSI-69 FLEX Experimental Table -> interim table.

Input: ``data/raw/psi_tables/PSI-69_Experimental table_FLEX.csv`` (274 data rows, cp1252).
Output: one row per CSV data row, original units (mmHg, mole fraction, mm, s), raw cell text kept
for every numeric column that contains non-numeric codes. No values are corrected here.

Column meanings follow NASA/TP-2015-216046 Appendix A.1 (docs/DATA_SOURCES.md, TP-FLEX).
The CSV header labels the burning rate "mm"; the TP defines it as the burning-rate constant
from a linear fit of d^2 vs t (mm^2/s). The unit is assigned in ``clean.py`` (ADR-015).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .common import read_csv_text, to_float

SOURCE_ID = "PSI-69"
EXPECTED_HEADER = [
    "FLEX Test #", "FLEX Identifier", "Test Date", "Test GMT", "Fuel",
    "Ambient pressure; mmHg",
    "O initial ambient composition; mole fraction",
    "N initial ambient composition; mole fraction",
    "CO initial ambient composition; mole fraction",
    "He initial ambient composition; mole fraction",
    "Droplet initial diameter; mm",
    "Visible flame extinction diameter; mm",
    "Burning rate; mm",
    "Burn time; s",
    "Test end",
]
NUMERIC = {  # interim name: header
    "p_mmHg": "Ambient pressure; mmHg",
    "x_o2": "O initial ambient composition; mole fraction",
    "x_n2": "N initial ambient composition; mole fraction",
    "x_co2": "CO initial ambient composition; mole fraction",
    "x_he": "He initial ambient composition; mole fraction",
    "d0_mm": "Droplet initial diameter; mm",
    "d_ext_mm": "Visible flame extinction diameter; mm",
    "burning_rate_raw_value": "Burning rate; mm",
    "burn_time_s": "Burn time; s",
}


def parse(path: Path) -> pd.DataFrame:
    """Parse the FLEX CSV; raises ValueError if the header differs from the expected one."""
    _, rows = read_csv_text(path)
    header = [c.strip() for c in rows[0]]
    if header != EXPECTED_HEADER:
        raise ValueError(f"unexpected FLEX header: {header}")
    out = []
    for i, r in enumerate(rows[1:], start=1):
        if not any(c.strip() for c in r):
            continue
        cell = dict(zip(header, (c.strip() for c in r)))
        rec = {
            "source_id": SOURCE_ID,
            "source_file": path.name,
            "row_id": i,  # 1-based data row (CSV line = row_id + 1)
            "test_no": int(cell["FLEX Test #"]),
            "flex_identifier": cell["FLEX Identifier"],
            "test_date": cell["Test Date"],
            "test_gmt": cell["Test GMT"],
            "fuel": cell["Fuel"],
            "test_end": cell["Test end"],
        }
        for name, col in NUMERIC.items():
            rec[name] = to_float(cell[col])
            rec[f"{name}__raw"] = cell[col]
        out.append(rec)
    return pd.DataFrame(out)
