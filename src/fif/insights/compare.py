"""Comparison matrix of the PSI combustion investigations (stretch S5, requirement CH-11, ADR-037).

Similarities and differences are derived from the raw PSI files, not typed by hand:
- what each investigation recorded = which variable classes appear in the header of its Experimental Table(s)
  (data/raw/psi_tables/*.csv), matched by the regular expressions in VARIABLES (case-insensitive);
- shared hardware = tags matched in the PSI record field "hardware" (HARDWARE);
- platform, dates, tests, publications, raw-data volume = PSI record fields (fif.insights.investigations).
A tick means "the table has a column of this kind", not that the values are complete or comparable across tables.
"""

from __future__ import annotations

import re

import pandas as pd

from fif.data.catalog import REPO_ROOT

from .investigations import ranked_investigations

TABLE_DIR = REPO_ROOT / "data" / "raw" / "psi_tables"

# (label, kind, regex on one header cell)
VARIABLES = [
    ("fuel / material", "input", r"fuel|material|sample type"),
    ("oxygen", "input", r"\bx?o2\b|oxygen|^o initial|percent o2|^atmosphere"),  # s-Flame "Atmosphere": "~21% O2 with He"
    ("pressure", "input", r"pressure|^p ?(init|final|mean)|\(bar\)|mmhg"),
    ("inert / diluent", "input", r"\bm?n2\b|^n initial|nitrogen|helium|^he initial|^co initial|gas mixture|^atmosphere"),
    ("air or gas flow", "input", r"flow|velocity|air rate|fan|air display|mfc"),
    ("sample / droplet size", "input", r"diameter|thickness|sample length|samle|width|burner size|nozzle"),
    ("ignition outcome", "outcome", r"hot ignition|flames ignited"),
    ("extinction outcome", "outcome", r"extinction|self ?-?ext"),
    ("burning, spread or mass-loss rate / time", "outcome", r"burning rate|burnrate|burn time|spread|weight loss|burn length"),
    ("gas products (O2, CO, CO2)", "outcome", r"final (co|o2)|final co2|co \(ppm\)"),
    ("smoke / particles", "outcome", r"rt/r0|aging|soot"),
    ("measured burner / flame temperature", "outcome", r"burner t|flame temp"),  # not Tad (computed) or ambient T
]
HARDWARE = {
    "CIR (Combustion Integrated Rack)": r"\bCIR\b|Combustion Integrated Rack",
    "MDCA (droplet apparatus)": r"MDCA|Droplet Combustion Ap",
    "ACME (gaseous flames)": r"\bACME\b|Advanced Combustion via Microgravity",
    "MSG (glovebox)": r"\bMSG\b|Glovebox",
    "Saffire in Cygnus": r"Saffire|SAFFIRE|Cygnus",
    "Soot diagnostics (SAME)": r"Soot Diagnostic",
}


def _headers(file_name: str) -> list[str]:
    raw = (TABLE_DIR / file_name.strip()).read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    return [h.strip() for h in text.splitlines()[0].split(",") if h.strip()]


def table_headers(experimental_tables: str | None) -> list[str]:
    if not isinstance(experimental_tables, str) or not experimental_tables.strip():
        return []
    out = []
    for f in experimental_tables.split(";"):
        out += _headers(f)
    return out


def comparison_matrix() -> pd.DataFrame:
    """One row per investigation (relevance order): PSI fields, hardware tags, and one bool column per variable class."""
    c = ranked_investigations()
    rows = []
    for _, r in c.iterrows():
        heads = table_headers(r["experimental_tables"])
        row = {
            "psi_id": r["psi_id"],
            "acronym": r["acronym"] or r["psi_id"],
            "title": r["title"],
            "stage": r["stage"],
            "subject": r["fuel_type"],
            "platform": r["flight_platform"] if isinstance(r["flight_platform"], str) else "",
            "start_year": pd.to_datetime(r["start_date"], errors="coerce").year,
            "tests": int(r["n_table_rows"]),
            "publications": r["n_publications"],
            "has_table": bool(heads),
            "relevance": r["relevance"],
        }
        hw = r["hardware"] if isinstance(r["hardware"], str) else ""
        row["hardware_groups"] = [g for g, rx in HARDWARE.items() if re.search(rx, hw)]
        for label, _, rx in VARIABLES:
            row[label] = any(re.search(rx, h, flags=re.IGNORECASE) for h in heads)
        rows.append(row)
    return pd.DataFrame(rows)


def hardware_groups(m: pd.DataFrame | None = None) -> dict[str, list[str]]:
    """Shared-hardware families: hardware tag -> acronyms (only tags shared by >= 2 investigations)."""
    m = comparison_matrix() if m is None else m
    out = {}
    for g in HARDWARE:
        acr = [a for a, gs in zip(m["acronym"], m["hardware_groups"]) if g in gs]
        if len(acr) >= 2:
            out[g] = acr
    return out
