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


TP_SOURCE_ID = "NTRS-20150023456"


def parse_supplement(path: Path) -> pd.DataFrame:
    """Tests printed in NASA/TP-2015-216046 Table IX but absent from the PSI CSV (ADR-020).

    ``data/raw/ntrs/flex_tp_supplement.csv``: hand transcription from TP p. 26, same columns as the
    PSI CSV plus "Source"; verified against a pdfplumber parse of the PDF (stage 4 WORKLOG).
    ``test_no`` is left empty (the PSI numbering has no slot for them); ``tp_test_no`` keeps the TP number.
    """
    _, rows = read_csv_text(path)
    header = [c.strip() for c in rows[0]]
    if header[:-1] != EXPECTED_HEADER or header[-1] != "Source":
        raise ValueError(f"unexpected supplement header: {header}")
    df = _parse_rows(rows[1:], header, path.name, TP_SOURCE_ID)
    df["tp_test_no"] = df.pop("test_no")
    df["test_no"] = pd.array([pd.NA] * len(df), dtype="Int64")
    return df


def parse(path: Path) -> pd.DataFrame:
    """Parse the FLEX CSV; raises ValueError if the header differs from the expected one."""
    _, rows = read_csv_text(path)
    header = [c.strip() for c in rows[0]]
    if header != EXPECTED_HEADER:
        raise ValueError(f"unexpected FLEX header: {header}")
    df = _parse_rows(rows[1:], header, path.name, SOURCE_ID)
    df["test_no"] = df["test_no"].astype("Int64")
    df["tp_test_no"] = pd.array([pd.NA] * len(df), dtype="Int64")
    return df


def _parse_rows(rows: list[list[str]], header: list[str], file_name: str, source_id: str) -> pd.DataFrame:
    out = []
    for i, r in enumerate(rows, start=1):
        if not any(c.strip() for c in r):
            continue
        cell = dict(zip(header, (c.strip() for c in r)))
        rec = {
            "source_id": source_id,
            "source_file": file_name,
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
